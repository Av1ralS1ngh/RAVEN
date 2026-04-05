"""TigerGraph client — data models, connection management, and query execution.

This module is the single point of contact between the Python backend and the
TigerGraph cluster. It owns:

  - Dataclasses that describe the graph domain objects used for upserts.
  - ``TigerGraphClient``: lazy-connected wrapper around pyTigerGraph that
    exposes install, upsert, and query methods for both graphs.
  - ``TigerGraphError``: typed exception so callers can distinguish DB errors.
"""

from __future__ import annotations

import logging
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import pyTigerGraph as tg  # pyTigerGraph uses camelCase package name

if TYPE_CHECKING:
    from app.config import Settings

logger = logging.getLogger(__name__)

# Paths to the GSQL artefacts relative to the project root.
# File lives at: backend/app/services/tigergraph_client.py
#   parents[0] → services/
#   parents[1] → app/
#   parents[2] → backend/
#   parents[3] → recruitgraph/  ← project root
PROJECT_ROOT = Path(__file__).parents[3]
SCHEMAS_DIR = PROJECT_ROOT / "tigergraph" / "schemas"
QUERIES_DIR = PROJECT_ROOT / "tigergraph" / "queries"

# Keep private aliases so existing internal references resolve.
_SCHEMAS_DIR = SCHEMAS_DIR
_QUERIES_DIR = QUERIES_DIR

_CHUNK_SIZE = 500  # vertices/edges per batch upsert call


# ─────────────────────────────────────────────────────────────────────────────
# Domain dataclasses  (transport layer — not coupled to Pydantic)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(slots=True)
class PersonNode:
    """A LinkedIn person vertex to be upserted into PersonGraph."""

    id: str
    name: str
    linkedin_url: str
    headline: str = ""
    company: str = ""
    profile_image_url: str = ""


@dataclass(slots=True)
class ConnectionEdge:
    """An undirected CONNECTED_TO edge between two Person vertices."""

    src_id: str
    tgt_id: str
    mutual_count: int = 0
    strength: float = 0.5


@dataclass(slots=True)
class LibNode:
    """A library/package vertex to be upserted into DepGraph."""

    name: str
    version: str = ""
    ecosystem: str = ""  # "cargo" | "npm" | "pip"


@dataclass(slots=True)
class FileNode:
    """A source-file vertex to be upserted into DepGraph."""

    path: str
    repo: str = ""
    language: str = ""


@dataclass(slots=True)
class DepEdge:
    """One of: IMPORTS, CALLS, or LIB_DEPENDS_ON edge for DepGraph.

    ``edge_type`` must be one of the three GSQL edge type names.
    ``attrs`` carries optional per-edge attributes (e.g. import_count,
    is_dev_dep).
    """

    edge_type: str
    src_type: str
    src_id: str
    tgt_type: str
    tgt_id: str
    attrs: dict[str, int | float | bool | str] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Custom exception
# ─────────────────────────────────────────────────────────────────────────────


class TigerGraphError(Exception):
    """Wraps any exception raised by pyTigerGraph so callers get a typed error.

    Attributes:
        message: Human-readable description of what went wrong.
        original: The underlying exception from pyTigerGraph or stdlib.
    """

    def __init__(self, message: str, original: BaseException | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.original = original

    def __str__(self) -> str:
        if self.original:
            return f"{self.message} — caused by: {type(self.original).__name__}: {self.original}"
        return self.message


# ─────────────────────────────────────────────────────────────────────────────
# Client
# ─────────────────────────────────────────────────────────────────────────────


class TigerGraphClient:
    """Thin service wrapper around pyTigerGraph.

    Connections to PersonGraph and DepGraph are created lazily on first access
    so that the app can start even when TigerGraph is temporarily unreachable.

    Args:
        settings: Application ``Settings`` instance injected by the caller —
            never imported directly to avoid circular imports and to keep this
            class independently testable.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._conn_global: tg.TigerGraphConnection | None = None
        self._conn_person: tg.TigerGraphConnection | None = None
        self._conn_dep: tg.TigerGraphConnection | None = None

    # ── Lazy connection properties ────────────────────────────────────────────

    @property
    def conn_global(self) -> tg.TigerGraphConnection:
        """Return a connection with no graph name — used for global DDL
        (CREATE VERTEX, CREATE GRAPH, etc.) where the target graph may not
        exist yet."""
        if self._conn_global is None:
            self._conn_global = self._make_conn("", use_token=False)
        return self._conn_global

    @property
    def conn_person(self) -> tg.TigerGraphConnection:
        """Return an authenticated connection to PersonGraph, creating it if
        needed."""
        if self._conn_person is None:
            self._conn_person = self._make_conn(
                self._settings.tigergraph_graph_name_person
            )
        return self._conn_person

    @property
    def conn_dep(self) -> tg.TigerGraphConnection:
        """Return an authenticated connection to DepGraph, creating it if
        needed."""
        if self._conn_dep is None:
            self._conn_dep = self._make_conn(
                self._settings.tigergraph_graph_name_dep
            )
        return self._conn_dep

    def _make_conn(
        self, graph_name: str, use_token: bool = True
    ) -> tg.TigerGraphConnection:
        """Create and authenticate a TigerGraphConnection.

        Args:
            graph_name: Target graph. Pass ``""`` for a global DDL connection.
            use_token:  Whether to call ``getToken()`` with the secret. Set to
                        ``False`` for global DDL connections where token scope
                        is not applicable.
        """
        label = graph_name or "<global>"
        try:
            conn = tg.TigerGraphConnection(
                host=self._settings.tigergraph_host,
                graphname=graph_name,
                username=self._settings.tigergraph_username,
                password=self._settings.tigergraph_password,
            )
            if use_token and self._settings.tigergraph_secret:
                conn.getToken(self._settings.tigergraph_secret)
            return conn
        except Exception as exc:
            raise TigerGraphError(
                f"Failed to connect to TigerGraph graph '{label}'", exc
            ) from exc

    # ── Schema & query installation ──────────────────────────────────────────

    def install_schemas(self) -> None:
        """Run both GSQL schema files against the global graph context.

        Idempotent: vertex/edge/graph types that already exist produce a
        warning from TigerGraph which is logged and swallowed.
        """
        for schema_file in [
            _SCHEMAS_DIR / "person_graph.gsql",
            _SCHEMAS_DIR / "dep_graph.gsql",
        ]:
            self._run_gsql_file(schema_file, label=f"schema:{schema_file.stem}")

    def install_queries(self) -> None:
        """Compile and install both GSQL query files.

        Idempotent: if a query is already installed TigerGraph returns an
        error message (not an exception). We detect the phrase "already exists"
        in the response and treat it as a no-op.
        """
        for query_file, conn, graph in [
            (_QUERIES_DIR / "shortest_path.gsql", self.conn_person, "PersonGraph"),
            (_QUERIES_DIR / "blast_radius.gsql", self.conn_dep, "DepGraph"),
        ]:
            self._run_gsql_file(
                query_file,
                conn=conn,
                label=f"query:{query_file.stem}@{graph}",
            )

    def _run_gsql_file(
        self,
        path: Path,
        conn: tg.TigerGraphConnection | None = None,
        label: str = "",
    ) -> str:
        """Read a GSQL file and execute it, returning the server response.

        Args:
            path: Absolute path to the .gsql file.
            conn: Optional connection to use. When ``None``, uses the global
                  context (suitable for schema DDL).
            label: Human-readable label for log messages.

        Raises:
            TigerGraphError: On file-read failure or unexpected TigerGraph error.
        """
        try:
            gsql = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise TigerGraphError(f"Cannot read GSQL file: {path}", exc) from exc

        try:
            if conn is not None:
                result = conn.gsql(gsql)
            else:
                # Use the global (no-graphname) connection for schema DDL.
                # conn_person requires PersonGraph to already exist — a
                # circular dependency when we're in the middle of creating it.
                result = self.conn_global.gsql(gsql)
        except Exception as exc:
            raise TigerGraphError(
                f"GSQL execution failed for {label}", exc
            ) from exc

        # Idempotency: "already exists" is not a real error.
        result_str = str(result)
        if "already exists" in result_str.lower():
            logger.info("[TG] %s — already installed, skipping.", label)
        else:
            logger.info("[TG] %s — OK: %s", label, textwrap.shorten(result_str, 120))

        return result_str

    # ── Upserts ──────────────────────────────────────────────────────────────

    def upsert_persons(
        self,
        persons: list[PersonNode],
        edges: list[ConnectionEdge] | None = None,
    ) -> None:
        """Batch-upsert Person vertices and CONNECTED_TO edges into PersonGraph.

        Args:
            persons: List of person dataclasses to upsert.
            edges:   Optional list of connection edges to upsert alongside.
        """
        try:
            if persons:
                for chunk in _chunks(persons, _CHUNK_SIZE):
                    vertex_data = [
                        (p.id, {
                            "name": p.name,
                            "headline": p.headline,
                            "company": p.company,
                            "linkedin_url": p.linkedin_url,
                            "profile_image_url": p.profile_image_url,
                        })
                        for p in chunk if p.id
                    ]
                    self.conn_person.upsertVertices("Person", vertex_data)
                    logger.debug("[TG] Upserted %d Person vertices.", len(chunk))

            if edges:
                for chunk in _chunks(edges, _CHUNK_SIZE):
                    edge_data = [
                        (e.src_id, e.tgt_id, {
                            "mutual_count": e.mutual_count,
                            "strength": e.strength,
                        })
                        for e in chunk
                        if e.src_id and e.tgt_id
                    ]
                    self.conn_person.upsertEdges("Person", "CONNECTED_TO", "Person", edge_data)
                    logger.debug("[TG] Upserted %d CONNECTED_TO edges.", len(chunk))

        except TigerGraphError:
            raise
        except Exception as exc:
            raise TigerGraphError("upsert_persons failed", exc) from exc

    def upsert_dep_graph(
        self,
        files: list[FileNode],
        libs: list[LibNode],
        edges: list[DepEdge],
    ) -> None:
        """Batch-upsert FileNode + LibNode vertices and DepGraph edges.

        Args:
            files: Source file vertices.
            libs:  Library/package vertices.
            edges: IMPORTS, CALLS, or LIB_DEPENDS_ON edges.
        """
        try:
            # ── Vertices ───────────────────────────────────────────────────
            if files:
                for chunk in _chunks(files, _CHUNK_SIZE):
                    self.conn_dep.upsertVertices(
                        "FileNode",
                        [(f.path, {"repo": f.repo, "language": f.language})
                         for f in chunk if f.path],
                    )
            if libs:
                for chunk in _chunks(libs, _CHUNK_SIZE):
                    self.conn_dep.upsertVertices(
                        "LibNode",
                        [(lb.name, {"version": lb.version, "ecosystem": lb.ecosystem})
                         for lb in chunk if lb.name],
                    )

            # ── Edges ──────────────────────────────────────────────────────
            # pyTigerGraph batch edge upsert signature:
            #   upsertEdges(srcType, edgeType, tgtType,
            #               [[src_id, tgt_id, {attrs}], ...])
            # Group by (edge_type, src_type, tgt_type) to batch correctly.
            edge_groups: dict[tuple[str, str, str], list[list]] = {}
            for e in edges:
                # Skip edges with empty IDs — these cause string index errors.
                if not e.src_id or not e.tgt_id:
                    continue
                key = (e.edge_type, e.src_type, e.tgt_type)
                row = [e.src_id, e.tgt_id, e.attrs or {}]
                edge_groups.setdefault(key, []).append(row)

            for (edge_type, src_type, tgt_type), rows in edge_groups.items():
                for chunk in _chunks(rows, _CHUNK_SIZE):
                    self.conn_dep.upsertEdges(src_type, edge_type, tgt_type, chunk)
                    logger.debug(
                        "[TG] Upserted %d %s edges (%s→%s).",
                        len(chunk), edge_type, src_type, tgt_type,
                    )

        except TigerGraphError:
            raise
        except Exception as exc:
            raise TigerGraphError("upsert_dep_graph failed", exc) from exc

    # ── Query runners ─────────────────────────────────────────────────────────

    def run_shortest_path(
        self,
        src_id: str,
        tgt_id: str,
        max_hops: int = 6,
    ) -> dict:
        """Execute the ``shortestPath`` installed query on PersonGraph.

        Returns:
            Raw result dict from pyTigerGraph (contains ``path`` and
            ``hop_count`` keys).

        Raises:
            TigerGraphError: On query execution failure.
        """
        try:
            result = self.conn_person.runInstalledQuery(
                "shortestPath",
                params={"src_id": src_id, "tgt_id": tgt_id, "max_hops": max_hops},
            )
            # result is typically a list of dicts from TigerGraph prints.
            merged = {}
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        merged.update(item)
            return merged
        except Exception as exc:
            raise TigerGraphError("run_shortest_path failed", exc) from exc

    def run_blast_radius(
        self,
        lib_name: str,
        max_hops: int = 4,
    ) -> dict:
        """Execute the ``blastRadius`` installed query on DepGraph.

        Returns:
            Raw result dict from pyTigerGraph (contains ``blast_radius`` key
            with a list of FileImpact tuples).

        Raises:
            TigerGraphError: On query execution failure.
        """
        try:
            result = self.conn_dep.runInstalledQuery(
                "blastRadius",
                params={"lib_name": lib_name, "max_hops": max_hops},
            )
            raw = result[0] if isinstance(result, list) and result else {}
            # Sort by depth ASC, then path ASC (GSQL ListAccum has no ordering).
            items: list[dict] = raw.get("blast_radius", [])
            items.sort(key=lambda x: (x.get("depth", 0), x.get("file_path", "")))
            return {"blast_radius": items}
        except Exception as exc:
            raise TigerGraphError("run_blast_radius failed", exc) from exc


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _chunks(lst: list, size: int):
    """Yield successive ``size``-length slices of ``lst``."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]

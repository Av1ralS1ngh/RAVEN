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

_IDEMPOTENT_GSQL_ERROR_SNIPPETS = (
    "already exists",
    "used by another object",
    "already in graph",
    "already created",
    "does not exist",
    "could not be found",
)

_GSQL_FAILURE_SNIPPETS = (
    "semantic check fails",
    "failed to",
    "encountered",
    "error",
)

_DISCOVERY_SCHEMA_STATEMENTS = [
        """
        USE GLOBAL
        CREATE VERTEX SkillNode (
            PRIMARY_ID name   STRING,
            category          STRING DEFAULT "other",
            difficulty        INT DEFAULT 1
        ) WITH primary_id_as_attribute="true"
        """,
        """
        USE GLOBAL
        CREATE VERTEX RoleNode (
            PRIMARY_ID name   STRING,
            level             STRING DEFAULT "mid"
        ) WITH primary_id_as_attribute="true"
        """,
        """
        USE GLOBAL
        CREATE VERTEX DomainNode (
            PRIMARY_ID name   STRING
        ) WITH primary_id_as_attribute="true"
        """,
        """
        USE GLOBAL
        CREATE VERTEX TraitNode (
            PRIMARY_ID name   STRING,
            trait_group       STRING DEFAULT ""
        ) WITH primary_id_as_attribute="true"
        """,
        """
        USE GLOBAL
        CREATE VERTEX LearningResourceNode (
            PRIMARY_ID id     STRING,
            title             STRING,
            resource_type     STRING DEFAULT "article",
            url               STRING DEFAULT ""
        ) WITH primary_id_as_attribute="true"
        """,
        """
        USE GLOBAL
        CREATE DIRECTED EDGE ROLE_REQUIRES_SKILL (
            FROM RoleNode, TO SkillNode,
            weight      FLOAT DEFAULT 0.5
        )
        """,
        """
        USE GLOBAL
        CREATE DIRECTED EDGE SKILL_RELATES_TO_SKILL (
            FROM SkillNode, TO SkillNode,
            affinity    FLOAT DEFAULT 0.5
        )
        """,
        """
        USE GLOBAL
        CREATE DIRECTED EDGE SKILL_IN_DOMAIN (
            FROM SkillNode, TO DomainNode
        )
        """,
        """
        USE GLOBAL
        CREATE DIRECTED EDGE TRAIT_ALIGNS_ROLE (
            FROM TraitNode, TO RoleNode,
            weight      FLOAT DEFAULT 0.5
        )
        """,
        """
        USE GLOBAL
        CREATE DIRECTED EDGE RESOURCE_TEACHES_SKILL (
            FROM LearningResourceNode, TO SkillNode,
            strength    FLOAT DEFAULT 0.5
        )
        """,
        """
        USE GLOBAL
        CREATE DIRECTED EDGE SKILL_USES_LIB (
            FROM SkillNode, TO LibNode,
            relevance   FLOAT DEFAULT 0.5
        )
        """,
        """
        USE GLOBAL
        CREATE DIRECTED EDGE ROLE_IN_DOMAIN (
            FROM RoleNode, TO DomainNode,
            fit         FLOAT DEFAULT 0.5
        )
        """,
        """
        USE GLOBAL
        CREATE DIRECTED EDGE ROLE_USES_LIB (
            FROM RoleNode, TO LibNode,
            relevance   FLOAT DEFAULT 0.5
        )
        """,
        """
        USE GLOBAL
        CREATE DIRECTED EDGE TRAIT_RELATES_TO_SKILL (
            FROM TraitNode, TO SkillNode,
            weight      FLOAT DEFAULT 0.5
        )
        """,
        """
        USE GLOBAL
        CREATE DIRECTED EDGE RESOURCE_IN_DOMAIN (
            FROM LearningResourceNode, TO DomainNode,
            strength    FLOAT DEFAULT 0.5
        )
        """,
        """
        USE GLOBAL
        CREATE DIRECTED EDGE FILE_SUPPORTS_SKILL (
            FROM FileNode, TO SkillNode,
            relevance   FLOAT DEFAULT 0.5
        )
        """,
        """
        USE GLOBAL
        CREATE DIRECTED EDGE DOMAIN_RELATES_TO_DOMAIN (
            FROM DomainNode, TO DomainNode,
            affinity    FLOAT DEFAULT 0.5
        )
        """,
]

_DEPGRAPH_REQUIRED_VERTICES = {
    "LibNode",
    "FileNode",
    "SkillNode",
    "RoleNode",
    "DomainNode",
    "TraitNode",
    "LearningResourceNode",
}

_DEPGRAPH_REQUIRED_EDGES = {
    "IMPORTS",
    "CALLS",
    "LIB_DEPENDS_ON",
    "ROLE_REQUIRES_SKILL",
    "SKILL_RELATES_TO_SKILL",
    "SKILL_IN_DOMAIN",
    "TRAIT_ALIGNS_ROLE",
    "RESOURCE_TEACHES_SKILL",
    "SKILL_USES_LIB",
    "ROLE_IN_DOMAIN",
    "ROLE_USES_LIB",
    "TRAIT_RELATES_TO_SKILL",
    "RESOURCE_IN_DOMAIN",
    "FILE_SUPPORTS_SKILL",
    "DOMAIN_RELATES_TO_DOMAIN",
}


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
class SkillNode:
    """A skill vertex used by the discovery graph."""

    name: str
    category: str = "other"
    difficulty: int = 1


@dataclass(slots=True)
class RoleNode:
    """A role vertex representing a recommendation target."""

    name: str
    level: str = "mid"


@dataclass(slots=True)
class DomainNode:
    """A broad learning or work domain vertex."""

    name: str


@dataclass(slots=True)
class TraitNode:
    """A quiz-derived trait vertex that aligns to roles."""

    name: str
    trait_group: str = ""


@dataclass(slots=True)
class LearningResourceNode:
    """A learning resource vertex connected to recommended skills."""

    id: str
    title: str
    resource_type: str = "article"
    url: str = ""


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
            host = self._settings.tigergraph_host.strip()
            if host and not host.lower().startswith(("http://", "https://")):
                host = f"http://{host}"

            conn = tg.TigerGraphConnection(
                host=host,
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

        # Ensure discovery extension schema is applied even when base schema
        # files short-circuit on already-existing objects.
        self._ensure_depgraph_discovery_schema()
        self._ensure_depgraph_membership()

    def install_queries(self) -> None:
        """Compile and install both GSQL query files.

        Idempotent: if a query is already installed TigerGraph returns an
        error message (not an exception). We detect the phrase "already exists"
        in the response and treat it as a no-op.
        """
        failures: list[str] = []

        for query_file, graph in [
            (_QUERIES_DIR / "shortest_path.gsql", "PersonGraph"),
            (_QUERIES_DIR / "blast_radius.gsql", "DepGraph"),
            (_QUERIES_DIR / "skill_discovery.gsql", "DepGraph"),
            (_QUERIES_DIR / "role_skill_mesh.gsql", "DepGraph"),
            (_QUERIES_DIR / "lib_role_bridge.gsql", "DepGraph"),
            (_QUERIES_DIR / "domain_mesh.gsql", "DepGraph"),
        ]:
            label = f"query:{query_file.stem}@{graph}"
            try:
                self._run_gsql_file(
                    query_file,
                    graph_name=graph,
                    label=label,
                )
            except TigerGraphError as exc:
                failures.append(f"{label}: {exc}")
                logger.warning("[TG] %s — skipped: %s", label, exc)

        if failures:
            logger.warning("[TG] Query installation completed with %d warning(s).", len(failures))

    def _run_gsql_file(
        self,
        path: Path,
        conn: tg.TigerGraphConnection | None = None,
        graph_name: str | None = None,
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
            if graph_name:
                scoped_gsql = f"USE GRAPH {graph_name}\n{gsql}"
                result = self.conn_global.gsql(scoped_gsql)
            elif conn is not None:
                result = conn.gsql(gsql)
            else:
                # Use the global (no-graphname) connection for schema DDL.
                # conn_person requires PersonGraph to already exist — a
                # circular dependency when we're in the middle of creating it.
                result = self.conn_global.gsql(gsql)
        except Exception as exc:
            message = str(exc).lower()
            if any(snippet in message for snippet in _IDEMPOTENT_GSQL_ERROR_SNIPPETS):
                logger.info("[TG] %s — already installed, skipping: %s", label, textwrap.shorten(str(exc), 140))
                return str(exc)
            raise TigerGraphError(
                f"GSQL execution failed for {label}", exc
            ) from exc

        # Idempotency: "already exists" is not a real error.
        result_str = str(result)
        result_lower = result_str.lower()
        if any(snippet in result_lower for snippet in _IDEMPOTENT_GSQL_ERROR_SNIPPETS):
            logger.info("[TG] %s — already installed, skipping.", label)
        elif any(snippet in result_lower for snippet in _GSQL_FAILURE_SNIPPETS):
            raise TigerGraphError(f"GSQL execution failed for {label}: {result_str}")
        else:
            logger.info("[TG] %s — OK: %s", label, textwrap.shorten(result_str, 120))

        return result_str

    def _run_gsql_statement(self, statement: str, label: str) -> str:
        """Execute one GSQL statement with idempotent error handling."""
        statement = textwrap.dedent(statement).strip()
        if not statement:
            return ""

        try:
            result = self.conn_global.gsql(statement)
            result_str = str(result)
            result_lower = result_str.lower()
            if any(snippet in result_lower for snippet in _IDEMPOTENT_GSQL_ERROR_SNIPPETS):
                logger.info("[TG] %s — already installed, skipping.", label)
            elif any(snippet in result_lower for snippet in _GSQL_FAILURE_SNIPPETS):
                raise TigerGraphError(f"GSQL execution failed for {label}: {result_str}")
            else:
                logger.info("[TG] %s — OK: %s", label, textwrap.shorten(result_str, 120))
            return result_str
        except Exception as exc:
            message = str(exc).lower()
            if any(snippet in message for snippet in _IDEMPOTENT_GSQL_ERROR_SNIPPETS):
                logger.info("[TG] %s — already installed, skipping: %s", label, textwrap.shorten(str(exc), 140))
                return str(exc)
            raise TigerGraphError(f"GSQL execution failed for {label}", exc) from exc

    def _ensure_depgraph_discovery_schema(self) -> None:
        """Apply discovery schema additions to DepGraph idempotently."""
        for idx, statement in enumerate(_DISCOVERY_SCHEMA_STATEMENTS, start=1):
            self._run_gsql_statement(statement, label=f"schema:dep_graph_discovery_step_{idx}")

    def _ensure_depgraph_membership(self) -> None:
        """Ensure DepGraph includes all required discovery vertex/edge types.

        Some TigerGraph deployments do not support ALTER GRAPH syntax in the
        dialect used by this project. For those clusters, we recreate DepGraph
        with the full required schema membership when it is missing.
        """
        try:
            existing_vertices = set(self.conn_dep.getVertexTypes())
            existing_edges = set(self.conn_dep.getEdgeTypes())
        except Exception as exc:
            raise TigerGraphError("Failed to inspect DepGraph schema membership", exc) from exc

        missing_vertices = sorted(_DEPGRAPH_REQUIRED_VERTICES - existing_vertices)
        missing_edges = sorted(_DEPGRAPH_REQUIRED_EDGES - existing_edges)

        if not missing_vertices and not missing_edges:
            return

        graph_name = self._settings.tigergraph_graph_name_dep
        logger.warning(
            "DepGraph missing schema members (vertices=%s edges=%s). Recreating graph '%s'.",
            missing_vertices,
            missing_edges,
            graph_name,
        )

        # Installed queries can hold graph dependencies that block DROP GRAPH.
        for query_name in (
            "skillDiscovery",
            "blastRadius",
            "roleSkillMesh",
            "libRoleBridge",
            "domainMesh",
        ):
            self._run_gsql_statement(
                f"USE GRAPH {graph_name}\nDROP QUERY {query_name}",
                label=f"schema:dep_graph_drop_query_{query_name}",
            )

        self._run_gsql_statement(
            f"USE GLOBAL\nDROP GRAPH {graph_name}",
            label="schema:dep_graph_drop_for_recreate",
        )

        create_graph_stmt = f"""
        USE GLOBAL
        CREATE GRAPH {graph_name} (
          LibNode,
          FileNode,
          SkillNode,
          RoleNode,
          DomainNode,
          TraitNode,
          LearningResourceNode,
          IMPORTS,
          CALLS,
          LIB_DEPENDS_ON,
          ROLE_REQUIRES_SKILL,
          SKILL_RELATES_TO_SKILL,
          SKILL_IN_DOMAIN,
          TRAIT_ALIGNS_ROLE,
          RESOURCE_TEACHES_SKILL,
                    SKILL_USES_LIB,
                    ROLE_IN_DOMAIN,
                    ROLE_USES_LIB,
                    TRAIT_RELATES_TO_SKILL,
                    RESOURCE_IN_DOMAIN,
                    FILE_SUPPORTS_SKILL,
                    DOMAIN_RELATES_TO_DOMAIN
        )
        """
        self._run_gsql_statement(
            create_graph_stmt,
            label="schema:dep_graph_full_recreate",
        )

        # Force fresh graph-scoped connection after recreate.
        self._conn_dep = None

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

    def upsert_skill_graph(
        self,
        skills: list[SkillNode],
        roles: list[RoleNode],
        domains: list[DomainNode],
        traits: list[TraitNode],
        resources: list[LearningResourceNode],
        edges: list[DepEdge],
    ) -> None:
        """Batch-upsert discovery vertices and edges into DepGraph.

        This method extends DepGraph usage beyond file/library blast analysis by
        writing role-skill-domain-trait-resource entities into the same graph.
        """
        try:
            if skills:
                for chunk in _chunks(skills, _CHUNK_SIZE):
                    self.conn_dep.upsertVertices(
                        "SkillNode",
                        [
                            (
                                s.name,
                                {
                                    "category": s.category,
                                    "difficulty": s.difficulty,
                                },
                            )
                            for s in chunk
                            if s.name
                        ],
                    )

            if roles:
                for chunk in _chunks(roles, _CHUNK_SIZE):
                    self.conn_dep.upsertVertices(
                        "RoleNode",
                        [(r.name, {"level": r.level}) for r in chunk if r.name],
                    )

            if domains:
                for chunk in _chunks(domains, _CHUNK_SIZE):
                    self.conn_dep.upsertVertices(
                        "DomainNode",
                        [(d.name, {}) for d in chunk if d.name],
                    )

            if traits:
                for chunk in _chunks(traits, _CHUNK_SIZE):
                    self.conn_dep.upsertVertices(
                        "TraitNode",
                        [
                            (t.name, {"trait_group": t.trait_group})
                            for t in chunk
                            if t.name
                        ],
                    )

            if resources:
                for chunk in _chunks(resources, _CHUNK_SIZE):
                    self.conn_dep.upsertVertices(
                        "LearningResourceNode",
                        [
                            (
                                r.id,
                                {
                                    "title": r.title,
                                    "resource_type": r.resource_type,
                                    "url": r.url,
                                },
                            )
                            for r in chunk
                            if r.id
                        ],
                    )

            edge_groups: dict[tuple[str, str, str], list[list]] = {}
            for e in edges:
                if not e.src_id or not e.tgt_id:
                    continue
                key = (e.edge_type, e.src_type, e.tgt_type)
                row = [e.src_id, e.tgt_id, e.attrs or {}]
                edge_groups.setdefault(key, []).append(row)

            for (edge_type, src_type, tgt_type), rows in edge_groups.items():
                for chunk in _chunks(rows, _CHUNK_SIZE):
                    self.conn_dep.upsertEdges(src_type, edge_type, tgt_type, chunk)

        except TigerGraphError:
            raise
        except Exception as exc:
            raise TigerGraphError("upsert_skill_graph failed", exc) from exc

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
            items: list[dict] = raw.get("blast_radius", [])

            normalized: list[dict[str, int | str]] = []
            for item in items:
                if not isinstance(item, dict):
                    continue

                # Legacy tuple output format.
                if "file_path" in item:
                    normalized.append(
                        {
                            "file_path": str(item.get("file_path", "")),
                            "repo": str(item.get("repo", "")),
                            "depth": int(item.get("depth", 0)),
                        }
                    )
                    continue

                # Vertex output format (PRINT Affected AS blast_radius).
                attrs = item.get("attributes", {})
                if not isinstance(attrs, dict):
                    attrs = {}

                depth_raw = attrs.get("@depth", attrs.get("depth", 0))
                if isinstance(depth_raw, list) and depth_raw:
                    depth_raw = depth_raw[0]

                try:
                    depth = int(depth_raw)
                except Exception:
                    depth = 0

                file_path = str(attrs.get("path", item.get("v_id", "")))
                repo = str(attrs.get("repo", ""))

                if file_path:
                    normalized.append(
                        {
                            "file_path": file_path,
                            "repo": repo,
                            "depth": depth,
                        }
                    )

            normalized.sort(key=lambda x: (int(x.get("depth", 0)), str(x.get("file_path", ""))))
            return {"blast_radius": normalized}
        except Exception as exc:
            raise TigerGraphError("run_blast_radius failed", exc) from exc

    def run_skill_discovery(
        self,
        role_name: str,
        related_limit: int = 8,
        resource_limit: int = 4,
    ) -> dict:
        """Execute the ``skillDiscovery`` installed query on DepGraph.

        Returns:
            Dict containing ``nodes``, ``edges``, ``node_count``, and
            ``edge_count`` keys when available.
        """
        def _merge_query_output(raw: object) -> dict:
            merged: dict = {}
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict):
                        merged.update(item)
            elif isinstance(raw, dict):
                merged.update(raw)
            return merged

        def _section_rows(payload: dict, section: str) -> list[dict]:
            rows = payload.get(section, [])
            if not isinstance(rows, list):
                return []
            return [row for row in rows if isinstance(row, dict)]

        def _safe_float(value: object, default: float) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        node_index: dict[tuple[str, str], dict[str, str | float]] = {}
        edge_index: dict[tuple[str, str, str, str, str], dict[str, str | float]] = {}

        def add_node(
            *,
            node_id: str,
            node_type: str,
            label: str,
            category: str,
            score: float,
        ) -> None:
            if not node_id:
                return

            key = (node_id, node_type)
            existing = node_index.get(key)
            if existing is None:
                node_index[key] = {
                    "node_id": node_id,
                    "node_type": node_type,
                    "label": label or node_id,
                    "category": category or "other",
                    "score": float(min(1.0, max(0.0, score))),
                }
                return

            existing_score = _safe_float(existing.get("score", 0.5), 0.5)
            existing["score"] = float(max(existing_score, min(1.0, max(0.0, score))))

        def add_nodes_from_rows(
            rows: list[dict],
            *,
            node_type: str,
            id_attr: str,
            category_attr: str,
            default_category: str,
            default_score: float,
        ) -> list[str]:
            ids: list[str] = []
            seen_ids: set[str] = set()

            for row in rows:
                attrs = row.get("attributes", {})
                if not isinstance(attrs, dict):
                    attrs = {}

                node_id = str(row.get("v_id", attrs.get(id_attr, ""))).strip()
                if not node_id or node_id in seen_ids:
                    continue

                label = str(attrs.get(id_attr, attrs.get("name", node_id))).strip() or node_id
                category = str(attrs.get(category_attr, default_category)).strip() or default_category
                score = default_score

                if node_type == "SkillNode":
                    difficulty = attrs.get("difficulty")
                    score = min(1.0, max(0.45, 0.25 + 0.15 * _safe_float(difficulty, 2.0)))
                elif node_type == "RoleNode":
                    category = "role"
                    score = 1.0
                elif node_type == "DomainNode":
                    category = "domain"
                elif node_type == "TraitNode":
                    category = "trait"
                elif node_type == "LearningResourceNode":
                    category = str(attrs.get("resource_type", default_category)).strip() or default_category
                elif node_type == "LibNode":
                    category = str(attrs.get("ecosystem", default_category)).strip() or default_category
                elif node_type == "FileNode":
                    language = str(attrs.get("language", default_category)).strip() or default_category
                    category = language
                    label = node_id.rsplit("/", 1)[-1] if "/" in node_id else node_id

                add_node(
                    node_id=node_id,
                    node_type=node_type,
                    label=label,
                    category=category,
                    score=score,
                )
                ids.append(node_id)
                seen_ids.add(node_id)

            return ids

        def add_edge(
            *,
            edge_type: str,
            src_id: str,
            src_type: str,
            tgt_id: str,
            tgt_type: str,
            weight: float,
        ) -> None:
            if not src_id or not tgt_id:
                return
            if src_id == tgt_id and src_type == tgt_type:
                return

            edge_key = (edge_type, src_type, src_id, tgt_type, tgt_id)
            new_weight = float(min(1.0, max(0.0, weight)))
            existing = edge_index.get(edge_key)
            if existing is None:
                edge_index[edge_key] = {
                    "edge_type": edge_type,
                    "src_id": src_id,
                    "src_type": src_type,
                    "tgt_id": tgt_id,
                    "tgt_type": tgt_type,
                    "weight": new_weight,
                }
                return

            current_weight = _safe_float(existing.get("weight", 0.5), 0.5)
            existing["weight"] = float(max(current_weight, new_weight))

        def connect_sets(
            *,
            edge_type: str,
            src_ids: list[str],
            src_type: str,
            tgt_ids: list[str],
            tgt_type: str,
            base_weight: float,
            max_targets_per_src: int = 4,
        ) -> None:
            if not src_ids or not tgt_ids:
                return

            limit = max(1, max_targets_per_src)
            unique_targets = list(dict.fromkeys(tgt_ids))

            for s_idx, src_id in enumerate(dict.fromkeys(src_ids)):
                for t_idx, tgt_id in enumerate(unique_targets[:limit]):
                    weight = base_weight - (0.018 * t_idx) - (0.008 * s_idx)
                    add_edge(
                        edge_type=edge_type,
                        src_id=src_id,
                        src_type=src_type,
                        tgt_id=tgt_id,
                        tgt_type=tgt_type,
                        weight=weight,
                    )

        try:
            # 1) Role-centered mesh query.
            role_mesh_raw = self.conn_dep.runInstalledQuery(
                "roleSkillMesh",
                params={
                    "role_name": role_name,
                    "related_limit": max(20, related_limit * 3),
                },
            )
            role_mesh = _merge_query_output(role_mesh_raw)

            role_ids = add_nodes_from_rows(
                _section_rows(role_mesh, "role"),
                node_type="RoleNode",
                id_attr="name",
                category_attr="role",
                default_category="role",
                default_score=1.0,
            )
            if not role_ids:
                add_node(
                    node_id=role_name,
                    node_type="RoleNode",
                    label=role_name,
                    category="role",
                    score=1.0,
                )
                role_ids = [role_name]

            role_traits = add_nodes_from_rows(
                _section_rows(role_mesh, "role_traits"),
                node_type="TraitNode",
                id_attr="name",
                category_attr="trait_group",
                default_category="trait",
                default_score=0.72,
            )
            required_skills = add_nodes_from_rows(
                _section_rows(role_mesh, "required_skills"),
                node_type="SkillNode",
                id_attr="name",
                category_attr="category",
                default_category="other",
                default_score=0.86,
            )
            related_skills = add_nodes_from_rows(
                _section_rows(role_mesh, "related_skills"),
                node_type="SkillNode",
                id_attr="name",
                category_attr="category",
                default_category="other",
                default_score=0.67,
            )
            role_skill_domains = add_nodes_from_rows(
                _section_rows(role_mesh, "domains"),
                node_type="DomainNode",
                id_attr="name",
                category_attr="domain",
                default_category="domain",
                default_score=0.64,
            )
            role_skill_libs = add_nodes_from_rows(
                _section_rows(role_mesh, "libraries"),
                node_type="LibNode",
                id_attr="name",
                category_attr="ecosystem",
                default_category="library",
                default_score=0.62,
            )
            role_domains = add_nodes_from_rows(
                _section_rows(role_mesh, "role_domains"),
                node_type="DomainNode",
                id_attr="name",
                category_attr="domain",
                default_category="domain",
                default_score=0.7,
            )
            role_libs = add_nodes_from_rows(
                _section_rows(role_mesh, "role_libraries"),
                node_type="LibNode",
                id_attr="name",
                category_attr="ecosystem",
                default_category="library",
                default_score=0.71,
            )
            trait_skills = add_nodes_from_rows(
                _section_rows(role_mesh, "trait_skills"),
                node_type="SkillNode",
                id_attr="name",
                category_attr="category",
                default_category="other",
                default_score=0.65,
            )

            connect_sets(
                edge_type="ROLE_REQUIRES_SKILL",
                src_ids=role_ids,
                src_type="RoleNode",
                tgt_ids=required_skills,
                tgt_type="SkillNode",
                base_weight=0.92,
                max_targets_per_src=max(6, related_limit),
            )
            connect_sets(
                edge_type="SKILL_RELATES_TO_SKILL",
                src_ids=required_skills,
                src_type="SkillNode",
                tgt_ids=related_skills,
                tgt_type="SkillNode",
                base_weight=0.73,
                max_targets_per_src=max(4, related_limit // 2),
            )
            connect_sets(
                edge_type="SKILL_IN_DOMAIN",
                src_ids=required_skills,
                src_type="SkillNode",
                tgt_ids=role_skill_domains,
                tgt_type="DomainNode",
                base_weight=0.76,
                max_targets_per_src=4,
            )
            connect_sets(
                edge_type="SKILL_USES_LIB",
                src_ids=required_skills,
                src_type="SkillNode",
                tgt_ids=role_skill_libs,
                tgt_type="LibNode",
                base_weight=0.81,
                max_targets_per_src=6,
            )
            connect_sets(
                edge_type="TRAIT_ALIGNS_ROLE",
                src_ids=role_traits,
                src_type="TraitNode",
                tgt_ids=role_ids,
                tgt_type="RoleNode",
                base_weight=0.78,
                max_targets_per_src=1,
            )
            connect_sets(
                edge_type="TRAIT_RELATES_TO_SKILL",
                src_ids=role_traits,
                src_type="TraitNode",
                tgt_ids=trait_skills,
                tgt_type="SkillNode",
                base_weight=0.69,
                max_targets_per_src=6,
            )
            connect_sets(
                edge_type="ROLE_IN_DOMAIN",
                src_ids=role_ids,
                src_type="RoleNode",
                tgt_ids=role_domains,
                tgt_type="DomainNode",
                base_weight=0.84,
                max_targets_per_src=6,
            )
            connect_sets(
                edge_type="ROLE_USES_LIB",
                src_ids=role_ids,
                src_type="RoleNode",
                tgt_ids=role_libs,
                tgt_type="LibNode",
                base_weight=0.82,
                max_targets_per_src=8,
            )
            connect_sets(
                edge_type="LIB_DEPENDS_ON",
                src_ids=role_libs,
                src_type="LibNode",
                tgt_ids=role_skill_libs,
                tgt_type="LibNode",
                base_weight=0.57,
                max_targets_per_src=3,
            )

            # 2) Library bridge queries for role-associated libraries.
            libraries_to_probe = list(
                dict.fromkeys(role_libs + role_skill_libs)
            )[:6]
            probed_domains: list[str] = list(dict.fromkeys(role_domains + role_skill_domains))

            for library_name in libraries_to_probe:
                try:
                    lib_bridge_raw = self.conn_dep.runInstalledQuery(
                        "libRoleBridge",
                        params={
                            "lib_name": library_name,
                            "caller_limit": max(30, related_limit * 4),
                            "related_limit": max(20, related_limit * 3),
                        },
                    )
                except Exception:
                    continue

                lib_bridge = _merge_query_output(lib_bridge_raw)

                library_nodes = add_nodes_from_rows(
                    _section_rows(lib_bridge, "library"),
                    node_type="LibNode",
                    id_attr="name",
                    category_attr="ecosystem",
                    default_category="library",
                    default_score=0.74,
                )
                importing_files = add_nodes_from_rows(
                    _section_rows(lib_bridge, "importing_files"),
                    node_type="FileNode",
                    id_attr="path",
                    category_attr="language",
                    default_category="file",
                    default_score=0.6,
                )
                downstream_files = add_nodes_from_rows(
                    _section_rows(lib_bridge, "downstream_files"),
                    node_type="FileNode",
                    id_attr="path",
                    category_attr="language",
                    default_category="file",
                    default_score=0.55,
                )
                direct_skills = add_nodes_from_rows(
                    _section_rows(lib_bridge, "direct_skills"),
                    node_type="SkillNode",
                    id_attr="name",
                    category_attr="category",
                    default_category="other",
                    default_score=0.8,
                )
                file_connected_skills = add_nodes_from_rows(
                    _section_rows(lib_bridge, "file_connected_skills"),
                    node_type="SkillNode",
                    id_attr="name",
                    category_attr="category",
                    default_category="other",
                    default_score=0.66,
                )
                bridge_related_skills = add_nodes_from_rows(
                    _section_rows(lib_bridge, "related_skills"),
                    node_type="SkillNode",
                    id_attr="name",
                    category_attr="category",
                    default_category="other",
                    default_score=0.63,
                )
                aligned_roles = add_nodes_from_rows(
                    _section_rows(lib_bridge, "aligned_roles"),
                    node_type="RoleNode",
                    id_attr="name",
                    category_attr="role",
                    default_category="role",
                    default_score=0.92,
                )
                direct_roles = add_nodes_from_rows(
                    _section_rows(lib_bridge, "direct_roles"),
                    node_type="RoleNode",
                    id_attr="name",
                    category_attr="role",
                    default_category="role",
                    default_score=0.88,
                )
                aligned_traits = add_nodes_from_rows(
                    _section_rows(lib_bridge, "aligned_traits"),
                    node_type="TraitNode",
                    id_attr="name",
                    category_attr="trait_group",
                    default_category="trait",
                    default_score=0.71,
                )
                skill_domains = add_nodes_from_rows(
                    _section_rows(lib_bridge, "skill_domains"),
                    node_type="DomainNode",
                    id_attr="name",
                    category_attr="domain",
                    default_category="domain",
                    default_score=0.64,
                )
                role_domains_from_lib = add_nodes_from_rows(
                    _section_rows(lib_bridge, "role_domains"),
                    node_type="DomainNode",
                    id_attr="name",
                    category_attr="domain",
                    default_category="domain",
                    default_score=0.69,
                )
                direct_role_domains = add_nodes_from_rows(
                    _section_rows(lib_bridge, "direct_role_domains"),
                    node_type="DomainNode",
                    id_attr="name",
                    category_attr="domain",
                    default_category="domain",
                    default_score=0.7,
                )

                for domain_name in skill_domains + role_domains_from_lib + direct_role_domains:
                    if domain_name not in probed_domains:
                        probed_domains.append(domain_name)

                connect_sets(
                    edge_type="IMPORTS",
                    src_ids=importing_files,
                    src_type="FileNode",
                    tgt_ids=library_nodes,
                    tgt_type="LibNode",
                    base_weight=0.78,
                    max_targets_per_src=1,
                )
                connect_sets(
                    edge_type="CALLS",
                    src_ids=importing_files,
                    src_type="FileNode",
                    tgt_ids=downstream_files,
                    tgt_type="FileNode",
                    base_weight=0.63,
                    max_targets_per_src=3,
                )
                connect_sets(
                    edge_type="SKILL_USES_LIB",
                    src_ids=direct_skills,
                    src_type="SkillNode",
                    tgt_ids=library_nodes,
                    tgt_type="LibNode",
                    base_weight=0.82,
                    max_targets_per_src=1,
                )
                connect_sets(
                    edge_type="FILE_SUPPORTS_SKILL",
                    src_ids=importing_files,
                    src_type="FileNode",
                    tgt_ids=file_connected_skills,
                    tgt_type="SkillNode",
                    base_weight=0.66,
                    max_targets_per_src=5,
                )
                connect_sets(
                    edge_type="ROLE_REQUIRES_SKILL",
                    src_ids=aligned_roles,
                    src_type="RoleNode",
                    tgt_ids=direct_skills,
                    tgt_type="SkillNode",
                    base_weight=0.79,
                    max_targets_per_src=6,
                )
                connect_sets(
                    edge_type="ROLE_USES_LIB",
                    src_ids=direct_roles,
                    src_type="RoleNode",
                    tgt_ids=library_nodes,
                    tgt_type="LibNode",
                    base_weight=0.8,
                    max_targets_per_src=2,
                )
                connect_sets(
                    edge_type="TRAIT_ALIGNS_ROLE",
                    src_ids=aligned_traits,
                    src_type="TraitNode",
                    tgt_ids=aligned_roles,
                    tgt_type="RoleNode",
                    base_weight=0.74,
                    max_targets_per_src=4,
                )
                connect_sets(
                    edge_type="TRAIT_RELATES_TO_SKILL",
                    src_ids=aligned_traits,
                    src_type="TraitNode",
                    tgt_ids=file_connected_skills,
                    tgt_type="SkillNode",
                    base_weight=0.62,
                    max_targets_per_src=5,
                )
                connect_sets(
                    edge_type="SKILL_IN_DOMAIN",
                    src_ids=direct_skills,
                    src_type="SkillNode",
                    tgt_ids=skill_domains,
                    tgt_type="DomainNode",
                    base_weight=0.75,
                    max_targets_per_src=4,
                )
                connect_sets(
                    edge_type="ROLE_IN_DOMAIN",
                    src_ids=aligned_roles,
                    src_type="RoleNode",
                    tgt_ids=role_domains_from_lib,
                    tgt_type="DomainNode",
                    base_weight=0.82,
                    max_targets_per_src=4,
                )
                connect_sets(
                    edge_type="ROLE_IN_DOMAIN",
                    src_ids=direct_roles,
                    src_type="RoleNode",
                    tgt_ids=direct_role_domains,
                    tgt_type="DomainNode",
                    base_weight=0.83,
                    max_targets_per_src=4,
                )
                connect_sets(
                    edge_type="SKILL_RELATES_TO_SKILL",
                    src_ids=direct_skills,
                    src_type="SkillNode",
                    tgt_ids=bridge_related_skills,
                    tgt_type="SkillNode",
                    base_weight=0.67,
                    max_targets_per_src=6,
                )
                connect_sets(
                    edge_type="LIB_DEPENDS_ON",
                    src_ids=library_nodes,
                    src_type="LibNode",
                    tgt_ids=role_skill_libs,
                    tgt_type="LibNode",
                    base_weight=0.54,
                    max_targets_per_src=3,
                )

            # 3) Domain mesh queries for domains discovered so far.
            for domain_name in probed_domains[:6]:
                try:
                    domain_mesh_raw = self.conn_dep.runInstalledQuery(
                        "domainMesh",
                        params={
                            "domain_name": domain_name,
                            "related_limit": max(20, related_limit * 3),
                        },
                    )
                except Exception:
                    continue

                domain_mesh = _merge_query_output(domain_mesh_raw)

                domain_nodes = add_nodes_from_rows(
                    _section_rows(domain_mesh, "domain"),
                    node_type="DomainNode",
                    id_attr="name",
                    category_attr="domain",
                    default_category="domain",
                    default_score=0.74,
                )
                domain_skills = add_nodes_from_rows(
                    _section_rows(domain_mesh, "skills"),
                    node_type="SkillNode",
                    id_attr="name",
                    category_attr="category",
                    default_category="other",
                    default_score=0.79,
                )
                domain_roles = add_nodes_from_rows(
                    _section_rows(domain_mesh, "roles"),
                    node_type="RoleNode",
                    id_attr="name",
                    category_attr="role",
                    default_category="role",
                    default_score=0.88,
                )
                direct_domain_roles = add_nodes_from_rows(
                    _section_rows(domain_mesh, "direct_roles"),
                    node_type="RoleNode",
                    id_attr="name",
                    category_attr="role",
                    default_category="role",
                    default_score=0.92,
                )
                domain_traits = add_nodes_from_rows(
                    _section_rows(domain_mesh, "traits"),
                    node_type="TraitNode",
                    id_attr="name",
                    category_attr="trait_group",
                    default_category="trait",
                    default_score=0.7,
                )
                skill_libraries = add_nodes_from_rows(
                    _section_rows(domain_mesh, "skill_libraries"),
                    node_type="LibNode",
                    id_attr="name",
                    category_attr="ecosystem",
                    default_category="library",
                    default_score=0.66,
                )
                role_libraries = add_nodes_from_rows(
                    _section_rows(domain_mesh, "role_libraries"),
                    node_type="LibNode",
                    id_attr="name",
                    category_attr="ecosystem",
                    default_category="library",
                    default_score=0.68,
                )
                direct_role_libraries = add_nodes_from_rows(
                    _section_rows(domain_mesh, "direct_role_libraries"),
                    node_type="LibNode",
                    id_attr="name",
                    category_attr="ecosystem",
                    default_category="library",
                    default_score=0.72,
                )
                resources = add_nodes_from_rows(
                    _section_rows(domain_mesh, "resources"),
                    node_type="LearningResourceNode",
                    id_attr="id",
                    category_attr="resource_type",
                    default_category="resource",
                    default_score=0.66,
                )
                domain_related_skills = add_nodes_from_rows(
                    _section_rows(domain_mesh, "related_skills"),
                    node_type="SkillNode",
                    id_attr="name",
                    category_attr="category",
                    default_category="other",
                    default_score=0.64,
                )
                neighboring_domains = add_nodes_from_rows(
                    _section_rows(domain_mesh, "neighboring_domains"),
                    node_type="DomainNode",
                    id_attr="name",
                    category_attr="domain",
                    default_category="domain",
                    default_score=0.62,
                )
                linked_domains = add_nodes_from_rows(
                    _section_rows(domain_mesh, "linked_domains"),
                    node_type="DomainNode",
                    id_attr="name",
                    category_attr="domain",
                    default_category="domain",
                    default_score=0.65,
                )

                connect_sets(
                    edge_type="SKILL_IN_DOMAIN",
                    src_ids=domain_skills,
                    src_type="SkillNode",
                    tgt_ids=domain_nodes,
                    tgt_type="DomainNode",
                    base_weight=0.82,
                    max_targets_per_src=2,
                )
                connect_sets(
                    edge_type="SKILL_RELATES_TO_SKILL",
                    src_ids=domain_skills,
                    src_type="SkillNode",
                    tgt_ids=domain_related_skills,
                    tgt_type="SkillNode",
                    base_weight=0.68,
                    max_targets_per_src=6,
                )
                connect_sets(
                    edge_type="ROLE_REQUIRES_SKILL",
                    src_ids=domain_roles,
                    src_type="RoleNode",
                    tgt_ids=domain_skills,
                    tgt_type="SkillNode",
                    base_weight=0.8,
                    max_targets_per_src=7,
                )
                connect_sets(
                    edge_type="ROLE_IN_DOMAIN",
                    src_ids=direct_domain_roles,
                    src_type="RoleNode",
                    tgt_ids=domain_nodes,
                    tgt_type="DomainNode",
                    base_weight=0.86,
                    max_targets_per_src=2,
                )
                connect_sets(
                    edge_type="TRAIT_ALIGNS_ROLE",
                    src_ids=domain_traits,
                    src_type="TraitNode",
                    tgt_ids=domain_roles,
                    tgt_type="RoleNode",
                    base_weight=0.76,
                    max_targets_per_src=5,
                )
                connect_sets(
                    edge_type="SKILL_USES_LIB",
                    src_ids=domain_skills,
                    src_type="SkillNode",
                    tgt_ids=skill_libraries,
                    tgt_type="LibNode",
                    base_weight=0.79,
                    max_targets_per_src=6,
                )
                connect_sets(
                    edge_type="ROLE_USES_LIB",
                    src_ids=domain_roles,
                    src_type="RoleNode",
                    tgt_ids=role_libraries,
                    tgt_type="LibNode",
                    base_weight=0.8,
                    max_targets_per_src=6,
                )
                connect_sets(
                    edge_type="ROLE_USES_LIB",
                    src_ids=direct_domain_roles,
                    src_type="RoleNode",
                    tgt_ids=direct_role_libraries,
                    tgt_type="LibNode",
                    base_weight=0.83,
                    max_targets_per_src=6,
                )
                connect_sets(
                    edge_type="RESOURCE_IN_DOMAIN",
                    src_ids=resources,
                    src_type="LearningResourceNode",
                    tgt_ids=domain_nodes,
                    tgt_type="DomainNode",
                    base_weight=0.74,
                    max_targets_per_src=2,
                )
                connect_sets(
                    edge_type="RESOURCE_TEACHES_SKILL",
                    src_ids=resources,
                    src_type="LearningResourceNode",
                    tgt_ids=domain_skills,
                    tgt_type="SkillNode",
                    base_weight=0.7,
                    max_targets_per_src=max(2, resource_limit),
                )
                connect_sets(
                    edge_type="DOMAIN_RELATES_TO_DOMAIN",
                    src_ids=domain_nodes,
                    src_type="DomainNode",
                    tgt_ids=neighboring_domains,
                    tgt_type="DomainNode",
                    base_weight=0.67,
                    max_targets_per_src=5,
                )
                connect_sets(
                    edge_type="DOMAIN_RELATES_TO_DOMAIN",
                    src_ids=domain_nodes,
                    src_type="DomainNode",
                    tgt_ids=linked_domains,
                    tgt_type="DomainNode",
                    base_weight=0.71,
                    max_targets_per_src=5,
                )
                connect_sets(
                    edge_type="LIB_DEPENDS_ON",
                    src_ids=role_libraries,
                    src_type="LibNode",
                    tgt_ids=skill_libraries,
                    tgt_type="LibNode",
                    base_weight=0.52,
                    max_targets_per_src=4,
                )

            if node_index and edge_index:
                parsed_nodes = sorted(
                    node_index.values(),
                    key=lambda item: (
                        str(item.get("node_type", "")),
                        str(item.get("node_id", "")),
                    ),
                )
                parsed_edges = sorted(
                    edge_index.values(),
                    key=lambda item: (
                        str(item.get("edge_type", "")),
                        str(item.get("src_type", "")),
                        str(item.get("src_id", "")),
                        str(item.get("tgt_type", "")),
                        str(item.get("tgt_id", "")),
                    ),
                )
                return {
                    "nodes": parsed_nodes,
                    "edges": parsed_edges,
                    "node_count": len(parsed_nodes),
                    "edge_count": len(parsed_edges),
                }
        except Exception as exc:
            logger.warning("[TG] run_skill_discovery mesh mode failed; using fallback parser: %s", exc)

        try:
            result = self.conn_dep.runInstalledQuery(
                "skillDiscovery",
                params={
                    "role_name": role_name,
                    "related_limit": related_limit,
                    "resource_limit": resource_limit,
                },
            )
            merged = _merge_query_output(result)

            # Newer query shape (explicit node/edge tuples) fast-path.
            nodes = merged.get("nodes", [])
            edges = merged.get("edges", [])
            if not isinstance(nodes, list):
                nodes = []
            if not isinstance(edges, list):
                edges = []

            if nodes and edges:
                node_count = merged.get("node_count", len(nodes))
                edge_count = merged.get("edge_count", len(edges))

                try:
                    node_count = int(node_count)
                except Exception:
                    node_count = len(nodes)

                try:
                    edge_count = int(edge_count)
                except Exception:
                    edge_count = len(edges)

                return {
                    "nodes": nodes,
                    "edges": edges,
                    "node_count": node_count,
                    "edge_count": edge_count,
                }

            # Legacy/compatible query shape: printed vertex sets + edge sets.
            node_index = {}
            edge_index = {}

            vertex_sections: list[tuple[str, str, str, str, float]] = [
                ("roles", "RoleNode", "name", "role", 1.0),
                ("traits", "TraitNode", "name", "trait", 0.7),
                ("required_skills", "SkillNode", "name", "category", 0.86),
                ("related_skills", "SkillNode", "name", "category", 0.67),
                ("domains", "DomainNode", "name", "domain", 0.62),
                ("resources", "LearningResourceNode", "id", "resource_type", 0.6),
                ("libs", "LibNode", "name", "ecosystem", 0.58),
            ]

            for section, node_type, id_attr, category_attr, default_score in vertex_sections:
                rows = merged.get(section, [])
                if not isinstance(rows, list):
                    continue
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    attrs = row.get("attributes", {})
                    if not isinstance(attrs, dict):
                        attrs = {}

                    node_id = str(row.get("v_id", attrs.get(id_attr, ""))).strip()
                    if not node_id:
                        continue

                    label = str(attrs.get(id_attr, attrs.get("name", node_id))).strip() or node_id
                    category = str(attrs.get(category_attr, "other")).strip() or "other"

                    score = default_score
                    if node_type == "SkillNode":
                        difficulty = attrs.get("difficulty")
                        try:
                            score = min(1.0, max(0.45, 0.25 + 0.15 * float(difficulty)))
                        except Exception:
                            pass

                    key = (node_id, node_type)
                    if key in node_index:
                        continue

                    node_index[key] = {
                        "node_id": node_id,
                        "node_type": node_type,
                        "label": label,
                        "category": category,
                        "score": float(score),
                    }

            edge_sections: list[tuple[str, str, str]] = [
                ("role_skill_edges", "ROLE_REQUIRES_SKILL", "weight"),
                ("trait_role_edges", "TRAIT_ALIGNS_ROLE", "weight"),
                ("skill_related_edges", "SKILL_RELATES_TO_SKILL", "affinity"),
                ("skill_domain_edges", "SKILL_IN_DOMAIN", "weight"),
                ("resource_skill_edges", "RESOURCE_TEACHES_SKILL", "strength"),
                ("skill_lib_edges", "SKILL_USES_LIB", "relevance"),
            ]

            for section, edge_type, weight_attr in edge_sections:
                rows = merged.get(section, [])
                if not isinstance(rows, list):
                    continue
                for row in rows:
                    if not isinstance(row, dict):
                        continue

                    attrs = row.get("attributes", {})
                    if not isinstance(attrs, dict):
                        attrs = {}

                    src_id = str(row.get("from_id", row.get("source", ""))).strip()
                    tgt_id = str(row.get("to_id", row.get("target", ""))).strip()
                    src_type = str(row.get("from_type", "")).strip()
                    tgt_type = str(row.get("to_type", "")).strip()

                    if not src_id or not tgt_id:
                        continue

                    if not src_type or not tgt_type:
                        # Infer common edge endpoints when type metadata is omitted.
                        inferred = {
                            "ROLE_REQUIRES_SKILL": ("RoleNode", "SkillNode"),
                            "TRAIT_ALIGNS_ROLE": ("TraitNode", "RoleNode"),
                            "SKILL_RELATES_TO_SKILL": ("SkillNode", "SkillNode"),
                            "SKILL_IN_DOMAIN": ("SkillNode", "DomainNode"),
                            "RESOURCE_TEACHES_SKILL": ("LearningResourceNode", "SkillNode"),
                            "SKILL_USES_LIB": ("SkillNode", "LibNode"),
                        }
                        src_type, tgt_type = inferred.get(edge_type, (src_type, tgt_type))

                    raw_weight = attrs.get(weight_attr, attrs.get("weight", 0.5))
                    if isinstance(raw_weight, list) and raw_weight:
                        raw_weight = raw_weight[0]
                    try:
                        weight = float(raw_weight)
                    except Exception:
                        weight = 0.5
                    weight = min(1.0, max(0.0, weight))

                    key = (edge_type, src_id, tgt_id)
                    if key in edge_index:
                        continue

                    edge_index[key] = {
                        "edge_type": edge_type,
                        "src_id": src_id,
                        "src_type": src_type,
                        "tgt_id": tgt_id,
                        "tgt_type": tgt_type,
                        "weight": weight,
                    }

            parsed_nodes = list(node_index.values())
            parsed_edges = list(edge_index.values())

            return {
                "nodes": parsed_nodes,
                "edges": parsed_edges,
                "node_count": len(parsed_nodes),
                "edge_count": len(parsed_edges),
            }
        except Exception as exc:
            raise TigerGraphError("run_skill_discovery failed", exc) from exc


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _chunks(lst: list, size: int):
    """Yield successive ``size``-length slices of ``lst``."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]

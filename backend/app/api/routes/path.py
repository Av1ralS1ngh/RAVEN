"""Module 1 API routes — Network Path Finder.

Endpoints:
  POST /api/v1/path/find   — discover the shortest LinkedIn connection path
  GET  /api/v1/path/health — liveness + TigerGraph connectivity check
"""

from __future__ import annotations

import logging
from collections import deque
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import SettingsDep, get_tg_client
from app.data.famous_person_graph import (
    FAMOUS_INDEX,
    FAMOUS_INDEX_BY_URL,
    FAMOUS_PEOPLE,
    build_famous_adjacency,
)
from app.models.path_models import (
    PathRequest,
    PathResponse,
    PathResult,
    PersonSummary,
)
from app.services.linkedin_scraper import (
    LinkedInAuthError,
    LinkedInRateLimitError,
    LinkedInScraper,
)
from app.services.tigergraph_client import (
    PersonNode,
    TigerGraphClient,
    TigerGraphError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# POST /find
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/find",
    response_model=PathResponse,
    summary="Find shortest LinkedIn connection path",
)
async def find_path(
    request_body: PathRequest,
    settings: SettingsDep,
    tg_client: TigerGraphClient = Depends(get_tg_client),
) -> PathResponse:
    """Discover the shortest connection path between the caller and a recruiter.

    Flow:
      1. Authenticate with LinkedIn and fetch the recruiter's profile.
      2. Crawl the caller's 2-hop connection graph.
      3. Upsert all discovered persons + edges into TigerGraph (PersonGraph).
      4. Run the ``shortestPath`` installed query.
      5. Map the raw TigerGraph result into a typed PathResult.

    Error mapping:
      - 401  LinkedInAuthError (bad credentials / expired session)
      - 429  LinkedInRateLimitError (persistent rate limiting)
      - 500  TigerGraphError or any unexpected exception
    """
    t_start = time.monotonic()

    # ── Demo / mock-data fast path ────────────────────────────────────────────
    # Activated when DEMO_MODE=true in .env OR when no LinkedIn credentials set.
    is_demo = getattr(settings, "demo_mode", False) or not getattr(settings, "linkedin_username", None)
    
    if is_demo:
        logger.info("[Path] DEMO_MODE active — bypassing LinkedIn auth and scraping.")
        # Re-use our realistic mock data for the node lookup
        from app.data.mock_graph import ADJACENCY, ALL_PERSONS, PERSON_INDEX

        all_persons = [*ALL_PERSONS, *FAMOUS_PEOPLE]
        person_index = {p.id: p for p in all_persons}

        # Merge baseline mock adjacency and famous extension adjacency.
        demo_adjacency: dict[str, set[str]] = {
            pid: set(neighbors) for pid, neighbors in ADJACENCY.items()
        }
        famous_adj = build_famous_adjacency(ALL_PERSONS)
        for pid, neighbors in famous_adj.items():
            demo_adjacency.setdefault(pid, set()).update(neighbors)
            for nbr in neighbors:
                demo_adjacency.setdefault(nbr, set()).add(pid)
        
        # 1. Resolve Recruiter
        norm_url = str(request_body.recruiter_url).rstrip("/").lower()
        recruiter_node = next((p for p in all_persons if p.linkedin_url.rstrip("/").lower() == norm_url), None)
        if recruiter_node is None:
            recruiter_node = FAMOUS_INDEX_BY_URL.get(norm_url)
        if not recruiter_node:
            slug = norm_url.rsplit("/in/", 1)[-1].split("?")[0]
            recruiter_node = PERSON_INDEX.get(slug)
            if recruiter_node is None:
                recruiter_node = FAMOUS_INDEX.get(slug)
        if not recruiter_node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recruiter not found in Demo graph. Please try a known founder or use realistic linkedin slug."
            )

        # In demo mode, keep founders discoverable even when clients send a
        # conservative hop limit.
        effective_max_hops = max(request_body.max_hops, 12)

        primary_ids = _bfs_shortest_path_ids(
            adjacency=demo_adjacency,
            src_id=request_body.your_linkedin_id,
            tgt_id=recruiter_node.id,
            max_hops=effective_max_hops,
        )
        if not primary_ids and effective_max_hops < 20:
            effective_max_hops = 20
            primary_ids = _bfs_shortest_path_ids(
                adjacency=demo_adjacency,
                src_id=request_body.your_linkedin_id,
                tgt_id=recruiter_node.id,
                max_hops=effective_max_hops,
            )
        if not primary_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No path found within max_hops in Demo graph.",
            )

        alternative_ids = _alternative_paths_ids(
            adjacency=demo_adjacency,
            src_id=request_body.your_linkedin_id,
            tgt_id=recruiter_node.id,
            primary_path=primary_ids,
            max_hops=effective_max_hops,
            max_alts=3,
        )

        query_time_ms = (time.monotonic() - t_start) * 1000
        primary_path = _map_ids_to_summaries(primary_ids, person_index)
        alt_paths = [_map_ids_to_summaries(path_ids, person_index) for path_ids in alternative_ids]

        result = PathResult(
            path=primary_path,
            hop_count=max(0, len(primary_ids) - 1),
            alternative_paths=alt_paths,
            total_connections_mapped=len(all_persons),
            query_time_ms=round(query_time_ms, 2),
        )
        return PathResponse(success=True, data=result)
    else:
        # ── 1. Scraper setup + recruiter profile ─────────────────────────────────
        try:
            scraper = LinkedInScraper(
                username=settings.linkedin_username,
                password=settings.linkedin_password,
            )
        except LinkedInAuthError as exc:
            logger.error("LinkedIn auth failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            ) from exc

        try:
            recruiter_node = await scraper.get_profile(str(request_body.recruiter_url))
        except LinkedInAuthError as exc:
            logger.warning("LinkedIn auth failed: %s", exc)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
        except LinkedInRateLimitError as exc:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        except Exception as exc:
            logger.exception("Unexpected error fetching recruiter profile")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

        # ── 2. Crawl caller's 2-hop graph ────────────────────────────────────────
        try:
            persons, edges = await scraper.get_connections(
                profile_id=request_body.your_linkedin_id,
                depth=2,
            )
        except LinkedInAuthError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
        except LinkedInRateLimitError as exc:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
        except Exception as exc:
            logger.exception("Error crawling connection graph")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

        all_persons = _merge_persons(persons, [recruiter_node])

    total_mapped = len(all_persons)

    # ── 3. Upsert into TigerGraph (Prod Only) ─────────────────────────────────
    if not is_demo:
        try:
            tg_client.upsert_persons(all_persons, edges)
        except TigerGraphError as exc:
            logger.error("TigerGraph upsert failed: %s", exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
        except Exception as exc:
            logger.exception("Unexpected error during upsert")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    # ── 4. Run shortest-path query ────────────────────────────────────────────
    try:
        tg_result = tg_client.run_shortest_path(
            src_id=request_body.your_linkedin_id,
            tgt_id=recruiter_node.id,
            max_hops=request_body.max_hops,
        )
    except TigerGraphError as exc:
        logger.error("Shortest path query failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error running shortest path query")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    # ── 5. Map result ─────────────────────────────────────────────────────────
    query_time_ms = (time.monotonic() - t_start) * 1000

    # Build an id→PersonNode lookup from our crawl results for enrichment.
    person_index: dict[str, PersonNode] = {p.id: p for p in all_persons}

    primary_path = _map_tg_path(tg_result.get("path", []), person_index)
    hop_count = int(tg_result.get("hop_count", len(primary_path) - 1))

    result = PathResult(
        path=primary_path,
        hop_count=hop_count,
        alternative_paths=[],        # TigerGraph shortestPath returns one path;
                                     # alternatives require k-path query (future).
        total_connections_mapped=total_mapped,
        query_time_ms=round(query_time_ms, 2),
    )

    return PathResponse(success=True, data=result)


# ─────────────────────────────────────────────────────────────────────────────
# GET /health
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/health", summary="Path module liveness check")
async def path_health(
    tg_client: TigerGraphClient = Depends(get_tg_client),
) -> dict[str, Any]:
    """Return liveness status and TigerGraph connectivity for PersonGraph."""
    tg_connected = False
    try:
        # Lightweight ping: echo an empty GSQL. Any successful response means
        # the connection is live.
        tg_client.conn_person.echo()
        tg_connected = True
    except Exception:
        pass

    return {
        "status": "ok",
        "graph": "PersonGraph",
        "tg_connected": tg_connected,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────


def _map_tg_path(
    raw_path: list[Any],
    index: dict[str, PersonNode],
) -> list[PersonSummary]:
    """Convert the raw TigerGraph path list to PersonSummary objects.

    TigerGraph may return path vertices as string IDs, or as dicts with
    ``v_id`` and ``attributes``. We enrich with our local crawl data where
    attributes may be richer.
    """
    summaries: list[PersonSummary] = []
    for entry in raw_path:
        if isinstance(entry, dict):
            v_id: str = entry.get("v_id", "")
            attrs: dict = entry.get("attributes", {})
        else:
            v_id = str(entry)
            attrs = {}
            
        node = index.get(v_id)

        summaries.append(
            PersonSummary(
                id=v_id,
                name=getattr(node, "name", attrs.get("name", v_id)),
                headline=getattr(node, "headline", attrs.get("headline", "")),
                company=getattr(node, "company", attrs.get("company", "")),
                linkedin_url=getattr(node, "linkedin_url", attrs.get("linkedin_url", f"https://linkedin.com/in/{v_id}")),
                mutual_count=getattr(node, "mutual_count", attrs.get("mutual_count", 0)),
            )
        )
    return summaries


def _merge_persons(
    existing: list[PersonNode],
    extras: list[PersonNode],
) -> list[PersonNode]:
    """Merge two PersonNode lists, deduplicating by id. Extras take priority."""
    index: dict[str, PersonNode] = {p.id: p for p in existing}
    for p in extras:
        index[p.id] = p
    return list(index.values())


def _map_ids_to_summaries(
    ids: list[str],
    index: dict[str, Any],
) -> list[PersonSummary]:
    """Map a path list of person IDs to API PersonSummary objects."""
    out: list[PersonSummary] = []
    for pid in ids:
        node = index.get(pid)
        if node is None:
            out.append(
                PersonSummary(
                    id=pid,
                    name=pid,
                    headline="",
                    company="",
                    linkedin_url=f"https://linkedin.com/in/{pid}",
                    mutual_count=0,
                )
            )
            continue

        out.append(
            PersonSummary(
                id=pid,
                name=getattr(node, "name", pid),
                headline=getattr(node, "headline", ""),
                company=getattr(node, "company", ""),
                linkedin_url=getattr(node, "linkedin_url", f"https://linkedin.com/in/{pid}"),
                mutual_count=int(getattr(node, "mutual_count", 0) or 0),
            )
        )
    return out


def _bfs_shortest_path_ids(
    adjacency: dict[str, set[str]],
    src_id: str,
    tgt_id: str,
    max_hops: int,
    blocked_edge: tuple[str, str] | None = None,
) -> list[str]:
    """Shortest path via BFS, with optional blocked undirected edge."""
    if src_id == tgt_id:
        return [src_id]
    if src_id not in adjacency or tgt_id not in adjacency:
        return []

    blocked: frozenset[str] | None = None
    if blocked_edge is not None:
        blocked = frozenset({blocked_edge[0], blocked_edge[1]})

    q: deque[tuple[str, list[str]]] = deque([(src_id, [src_id])])
    seen = {src_id}

    while q:
        current, path = q.popleft()
        hops = len(path) - 1
        if hops >= max_hops:
            continue

        for nbr in adjacency.get(current, set()):
            if blocked is not None and frozenset({current, nbr}) == blocked:
                continue
            if nbr in path:
                continue
            next_path = [*path, nbr]
            if nbr == tgt_id:
                return next_path
            if nbr in seen:
                continue
            seen.add(nbr)
            q.append((nbr, next_path))

    return []


def _alternative_paths_ids(
    adjacency: dict[str, set[str]],
    src_id: str,
    tgt_id: str,
    primary_path: list[str],
    max_hops: int,
    max_alts: int,
) -> list[list[str]]:
    """Generate and rank alternative paths by node count (shorter first)."""
    if len(primary_path) < 2:
        return []

    alternatives: list[list[str]] = []
    seen_paths = {tuple(primary_path)}

    for i in range(len(primary_path) - 1):
        blocked_edge = (primary_path[i], primary_path[i + 1])
        alt = _bfs_shortest_path_ids(
            adjacency=adjacency,
            src_id=src_id,
            tgt_id=tgt_id,
            max_hops=max_hops,
            blocked_edge=blocked_edge,
        )
        if not alt:
            continue
        t = tuple(alt)
        if t in seen_paths:
            continue
        seen_paths.add(t)
        alternatives.append(alt)

    # Rank by path length (node count), then lexicographically for stability.
    ranked = sorted(alternatives, key=lambda path: (len(path), path))

    return ranked[:max_alts]

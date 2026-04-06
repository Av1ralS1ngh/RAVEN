"""Startup seeding for PersonGraph: baseline mock graph + curated famous nodes."""

from __future__ import annotations

import logging

from app.data.famous_person_graph import FAMOUS_PEOPLE, build_famous_edges
from app.data.mock_graph import ADJACENCY, ALL_PERSONS, PERSON_INDEX
from app.services.tigergraph_client import ConnectionEdge, PersonNode, TigerGraphClient

logger = logging.getLogger(__name__)


def seed_famous_nodes(client: TigerGraphClient) -> tuple[int, int]:
    """Upsert baseline mock nodes + famous people and realistic connectivity.

    Returns:
        Tuple of ``(person_count, edge_count)`` upserted.
    """
    person_index: dict[str, PersonNode] = {}

    # Baseline mock graph persons.
    for p in ALL_PERSONS:
        person_index[p.id] = PersonNode(
            id=p.id,
            name=p.name,
            linkedin_url=p.linkedin_url,
            headline=p.headline,
            company=p.company,
        )

    # Famous extension persons (override duplicates with curated details).
    for p in FAMOUS_PEOPLE:
        person_index[p.id] = PersonNode(
            id=p.id,
            name=p.name,
            linkedin_url=p.linkedin_url,
            headline=p.headline,
            company=p.company,
        )

    # Build undirected unique edge map with max mutual count when duplicated.
    edge_index: dict[frozenset[str], ConnectionEdge] = {}

    def upsert_edge(src_id: str, tgt_id: str, mutual_count: int) -> None:
        if not src_id or not tgt_id or src_id == tgt_id:
            return
        key = frozenset({src_id, tgt_id})
        strength = round(min(1.0, max(0.1, mutual_count / 50)), 2)
        existing = edge_index.get(key)
        if existing is None or mutual_count > existing.mutual_count:
            edge_index[key] = ConnectionEdge(
                src_id=src_id,
                tgt_id=tgt_id,
                mutual_count=mutual_count,
                strength=strength,
            )

    # Baseline mock graph edges.
    for src, nbrs in ADJACENCY.items():
        for tgt in nbrs:
            mutual = PERSON_INDEX.get(tgt, ALL_PERSONS[0]).mutual_count
            upsert_edge(src, tgt, mutual)

    # Famous extension edges (realistic synthetic network + low-weight mock bridges).
    for src, tgt, mutual in build_famous_edges(ALL_PERSONS):
        upsert_edge(src, tgt, mutual)

    persons = list(person_index.values())
    edges = list(edge_index.values())

    logger.info(
        "Seeding PersonGraph with %d people and %d connections (mock + famous).",
        len(persons),
        len(edges),
    )
    client.upsert_persons(persons, edges)
    return len(persons), len(edges)

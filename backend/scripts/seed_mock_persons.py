#!/usr/bin/env python3
"""Seed TigerGraph PersonGraph with mock LinkedIn data.

Run from the backend/ directory:
    python -m scripts.seed_mock_persons

Or directly:
    cd backend && python scripts/seed_mock_persons.py
"""
from __future__ import annotations

import sys
import os
import logging

# Ensure backend/ is on the path when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    from app.config import get_settings
    from app.services.tigergraph_client import TigerGraphClient, ConnectionEdge, PersonNode
    from app.data.mock_graph import ALL_PERSONS, ADJACENCY

    settings = get_settings()
    if not settings.tigergraph_host:
        logger.error("TIGERGRAPH_HOST not set in .env — aborting.")
        sys.exit(1)

    client = TigerGraphClient(settings)

    # ── Convert MockPerson → PersonNode ──────────────────────────────────────
    person_nodes = [
        PersonNode(
            id=p.id,
            name=p.name,
            linkedin_url=p.linkedin_url,
            headline=p.headline,
            company=p.company,
        )
        for p in ALL_PERSONS
    ]

    # ── Convert ADJACENCY → ConnectionEdge list (de-dup) ─────────────────────
    seen: set[frozenset] = set()
    edges: list[ConnectionEdge] = []
    for src, nbrs in ADJACENCY.items():
        for tgt in nbrs:
            key = frozenset({src, tgt})
            if key not in seen:
                seen.add(key)
                # mutual_count from the target person
                from app.data.mock_graph import PERSON_INDEX
                edges.append(ConnectionEdge(
                    src_id=src,
                    tgt_id=tgt,
                    mutual_count=PERSON_INDEX.get(tgt, ALL_PERSONS[0]).mutual_count,
                    strength=round(min(1.0, PERSON_INDEX.get(tgt, ALL_PERSONS[0]).mutual_count / 50), 2),
                ))

    logger.info("Seeding %d persons and %d edges into PersonGraph …", len(person_nodes), len(edges))

    try:
        client.upsert_persons(person_nodes, edges)
        logger.info("✓ Seed complete.")
    except Exception as exc:
        logger.error("Seed failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()

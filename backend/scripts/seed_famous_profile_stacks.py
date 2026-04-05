#!/usr/bin/env python3
"""Seed curated famous-profile tech stacks into TigerGraph DepGraph.

Run from backend/:
    python -m scripts.seed_famous_profile_stacks

Or directly:
    cd backend && python scripts/seed_famous_profile_stacks.py
"""

from __future__ import annotations

import logging
import os
import re
import sys

# Ensure backend/ is on the path when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _slug_token(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    token = token.strip("_")
    return token or "unknown"


def main() -> None:
    from app.config import get_settings
    from app.services.famous_personality_stacks import all_seeded_profiles
    from app.services.tigergraph_client import DepEdge, FileNode, LibNode, TigerGraphClient

    settings = get_settings()
    if not settings.tigergraph_host:
        logger.error("TIGERGRAPH_HOST not set in .env — aborting.")
        sys.exit(1)

    seeded = all_seeded_profiles()
    if not seeded:
        logger.info("No seeded profiles configured. Nothing to do.")
        return

    files: list[FileNode] = []
    libs: list[LibNode] = []
    edges: list[DepEdge] = []

    for slug, tech_stack in seeded.items():
        slug_token = _slug_token(slug)
        profile_file_id = f"profile://linkedin/{slug_token}"
        files.append(FileNode(path=profile_file_id, repo="linkedin_profiles", language="profile"))

        seen: set[str] = set()
        for tech_name in tech_stack:
            key = tech_name.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)

            lib_id = f"profile_lib::{slug_token}::{_slug_token(tech_name)}"
            libs.append(LibNode(name=lib_id, version=tech_name, ecosystem="profile_seed"))
            edges.append(
                DepEdge(
                    edge_type="IMPORTS",
                    src_type="FileNode",
                    src_id=profile_file_id,
                    tgt_type="LibNode",
                    tgt_id=lib_id,
                    attrs={"import_count": 1},
                )
            )

    logger.info(
        "Seeding curated profile stacks into DepGraph: %d profiles, %d tech vertices",
        len(files),
        len(libs),
    )

    try:
        client = TigerGraphClient(settings)
        client.upsert_dep_graph(files=files, libs=libs, edges=edges)
        logger.info("✓ Seed complete.")
    except Exception as exc:
        logger.error("Seed failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()

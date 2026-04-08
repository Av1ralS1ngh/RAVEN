"""Manual seeding entrypoint for discovery graph entities."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure `app` imports resolve when executed as a script.
PROJECT_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_BACKEND_ROOT))

from app.config import get_settings
from app.services.skill_discovery_seed import seed_skill_discovery_graph
from app.services.tigergraph_client import TigerGraphClient


def main() -> None:
    settings = get_settings()
    client = TigerGraphClient(settings)
    client.install_schemas()
    client.install_queries()
    node_count, edge_count = seed_skill_discovery_graph(client)
    print(f"Seeded discovery graph with {node_count} nodes and {edge_count} edges")


if __name__ == "__main__":
    main()

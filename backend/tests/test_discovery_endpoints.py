from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_tg_client
from app.api.routes import discovery
from app.services.skill_discovery_seed import ROLE_SKILL_MAP
from app.services.tigergraph_client import TigerGraphError


class _FakeConn:
    def __init__(self, should_fail: bool = False) -> None:
        self._should_fail = should_fail

    def echo(self) -> None:
        if self._should_fail:
            raise RuntimeError("echo failed")


class _FakeTGClient:
    def __init__(
        self,
        by_role: dict[str, dict[str, Any]] | None = None,
        should_raise: bool = False,
        health_fail: bool = False,
    ) -> None:
        self._by_role = by_role or {}
        self._should_raise = should_raise
        self.conn_dep = _FakeConn(should_fail=health_fail)

    def run_skill_discovery(
        self,
        role_name: str,
        related_limit: int = 8,
        resource_limit: int = 4,
    ) -> dict[str, Any]:
        if self._should_raise:
            raise TigerGraphError("query failed")

        if role_name in self._by_role:
            return self._by_role[role_name]

        role_skills = ROLE_SKILL_MAP.get(role_name, [])
        nodes = [
            {
                "node_id": role_name,
                "node_type": "RoleNode",
                "label": role_name,
                "category": "role",
                "score": 1.0,
            }
        ]
        edges: list[dict[str, Any]] = []

        for idx, skill in enumerate(role_skills[: related_limit or 6]):
            score = max(0.45, 0.95 - idx * 0.08)
            nodes.append(
                {
                    "node_id": skill,
                    "node_type": "SkillNode",
                    "label": skill,
                    "category": "other",
                    "score": score,
                }
            )
            edges.append(
                {
                    "edge_type": "ROLE_REQUIRES_SKILL",
                    "src_id": role_name,
                    "src_type": "RoleNode",
                    "tgt_id": skill,
                    "tgt_type": "SkillNode",
                    "weight": score,
                }
            )

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }


def _build_client(fake_tg: _FakeTGClient) -> TestClient:
    app = FastAPI()
    app.include_router(discovery.router, prefix="/api/discovery")
    app.dependency_overrides[get_tg_client] = lambda: fake_tg
    return TestClient(app)


def _quiz_payload() -> dict[str, Any]:
    return {
        "answers": {
            "background": "logical",
            "intensity": "research",
            "solving": "code",
            "influence": "impact",
            "breadth": "specialist",
        },
        "related_limit": 6,
        "resource_limit": 3,
    }


def test_discovery_analyze_contract_and_minimum_graph_size() -> None:
    # Return intentionally sparse graph to verify route backfills to 7+ nodes.
    fake_tg = _FakeTGClient(
        by_role={
            "Graph Database & Backend Researcher": {
                "nodes": [
                    {
                        "node_id": "Graph Database & Backend Researcher",
                        "node_type": "RoleNode",
                        "label": "Graph Database & Backend Researcher",
                        "category": "role",
                        "score": 1.0,
                    },
                    {
                        "node_id": "TigerGraph",
                        "node_type": "SkillNode",
                        "label": "TigerGraph",
                        "category": "database",
                        "score": 0.9,
                    },
                ],
                "edges": [
                    {
                        "edge_type": "ROLE_REQUIRES_SKILL",
                        "src_id": "Graph Database & Backend Researcher",
                        "src_type": "RoleNode",
                        "tgt_id": "TigerGraph",
                        "tgt_type": "SkillNode",
                        "weight": 0.9,
                    }
                ],
                "node_count": 2,
                "edge_count": 1,
            }
        }
    )

    client = _build_client(fake_tg)
    response = client.post("/api/discovery/analyze", json=_quiz_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"] is not None

    data = payload["data"]
    assert isinstance(data["recommendation_title"], str)
    assert isinstance(data["recommendation_desc"], str)
    assert isinstance(data["query_time_ms"], (int, float))

    graph = data["graph"]
    assert isinstance(graph["nodes"], list)
    assert isinstance(graph["edges"], list)
    assert graph["node_count"] == len(graph["nodes"])
    assert graph["edge_count"] == len(graph["edges"])
    assert graph["node_count"] >= 7

    node_types = {node["node_type"] for node in graph["nodes"]}
    assert "RoleNode" in node_types
    assert "SkillNode" in node_types

    assert isinstance(data["clusters"], list)


def test_discovery_trending_contract() -> None:
    client = _build_client(_FakeTGClient())
    response = client.get("/api/discovery/trending", params={"limit": 6})

    assert response.status_code == 200
    payload = response.json()

    assert payload["success"] is True
    assert payload["data"] is not None

    data = payload["data"]
    assert isinstance(data["query_time_ms"], (int, float))
    assert isinstance(data["skills"], list)
    assert len(data["skills"]) <= 6

    if data["skills"]:
        first = data["skills"][0]
        assert {"name", "category", "score", "connected_roles"}.issubset(first.keys())
        assert isinstance(first["connected_roles"], list)


def test_discovery_health_contract() -> None:
    client = _build_client(_FakeTGClient())
    response = client.get("/api/discovery/health")

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["module"] == "discovery"
    assert payload["graph"] == "DepGraph"
    assert payload["tg_connected"] is True

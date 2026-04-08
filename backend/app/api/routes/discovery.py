"""Module 3 API routes — Skill Discovery graph analysis."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_tg_client
from app.models.discovery_models import (
    DiscoveryAnalyzeRequest,
    DiscoveryAnalyzeResponse,
    DiscoveryAnalyzeResult,
    DiscoveryEdge,
    DiscoveryGraph,
    DiscoveryNode,
    SkillCluster,
    TrendingSkillItem,
    TrendingSkillsResponse,
    TrendingSkillsResult,
)
from app.services.skill_discovery_seed import ROLE_SKILL_MAP, SKILL_CATEGORY_MAP
from app.services.tigergraph_client import TigerGraphClient, TigerGraphError

logger = logging.getLogger(__name__)

router = APIRouter()

_MAX_GRAPH_NODES = 140
_MAX_GRAPH_EDGES = 420

_ALLOWED_NODE_TYPES = {
    "FileNode",
    "RoleNode",
    "SkillNode",
    "DomainNode",
    "TraitNode",
    "LearningResourceNode",
    "LibNode",
}

_ALLOWED_EDGE_TYPES = {
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


@router.post(
    "/analyze",
    response_model=DiscoveryAnalyzeResponse,
    summary="Run quiz-driven skill discovery graph analysis",
)
async def analyze_discovery(
    request_body: DiscoveryAnalyzeRequest,
    tg_client: TigerGraphClient = Depends(get_tg_client),
) -> DiscoveryAnalyzeResponse:
    """Build a role-centered discovery graph from quiz answers."""
    t_start = time.monotonic()

    recommendation_title, recommendation_desc = _recommendation_from_answers(
        request_body.answers.model_dump()
    )

    warning: str | None = None
    raw_nodes: list[dict[str, Any]] = []
    raw_edges: list[dict[str, Any]] = []

    try:
        raw_result = tg_client.run_skill_discovery(
            role_name=recommendation_title,
            related_limit=request_body.related_limit,
            resource_limit=request_body.resource_limit,
        )
        raw_nodes = _as_dict_list(raw_result.get("nodes", []))
        raw_edges = _as_dict_list(raw_result.get("edges", []))
    except TigerGraphError as exc:
        warning = (
            "TigerGraph discovery query failed; using seeded fallback graph for this recommendation."
        )
        logger.warning("Skill discovery query failed for %s: %s", recommendation_title, exc)

    nodes = _normalize_nodes(raw_nodes)
    edges = _normalize_edges(raw_edges)
    nodes, edges = _ensure_minimum_graph(recommendation_title, nodes, edges)
    nodes, edges = _trim_graph_density(nodes, edges)

    graph = DiscoveryGraph(
        nodes=nodes,
        edges=edges,
        node_count=len(nodes),
        edge_count=len(edges),
    )

    result = DiscoveryAnalyzeResult(
        recommendation_title=recommendation_title,
        recommendation_desc=recommendation_desc,
        graph=graph,
        clusters=_build_skill_clusters(nodes),
        query_time_ms=round((time.monotonic() - t_start) * 1000, 2),
    )

    return DiscoveryAnalyzeResponse(success=True, data=result, error=warning)


@router.get(
    "/trending",
    response_model=TrendingSkillsResponse,
    summary="Get trending skill clusters from discovery graph",
)
async def trending_skills(
    limit: int = Query(default=8, ge=4, le=20),
    tg_client: TigerGraphClient = Depends(get_tg_client),
) -> TrendingSkillsResponse:
    """Aggregate trending skills across core discovery recommendation roles."""
    t_start = time.monotonic()

    frequency: dict[str, int] = defaultdict(int)
    categories: dict[str, str] = {}
    role_links: dict[str, set[str]] = defaultdict(set)

    for role_name in ROLE_SKILL_MAP:
        skill_nodes: list[DiscoveryNode] = []
        try:
            raw = tg_client.run_skill_discovery(
                role_name=role_name,
                related_limit=6,
                resource_limit=2,
            )
            skill_nodes = [
                n
                for n in _normalize_nodes(_as_dict_list(raw.get("nodes", [])))
                if n.node_type == "SkillNode"
            ]
        except TigerGraphError:
            # Fallback to seeded mapping when query is unavailable.
            skill_nodes = [
                DiscoveryNode(
                    id=skill,
                    node_type="SkillNode",
                    label=skill,
                    category=SKILL_CATEGORY_MAP.get(skill, "other"),
                    score=0.65,
                )
                for skill in ROLE_SKILL_MAP.get(role_name, [])
            ]

        for node in skill_nodes:
            frequency[node.label] += 1
            categories.setdefault(node.label, node.category)
            role_links[node.label].add(role_name)

    ranked = sorted(
        frequency.items(),
        key=lambda item: (item[1], len(role_links[item[0]]), item[0]),
        reverse=True,
    )

    items = [
        TrendingSkillItem(
            name=name,
            category=categories.get(name, "other"),
            score=round(count + len(role_links[name]) * 0.15, 2),
            connected_roles=sorted(role_links[name]),
        )
        for name, count in ranked[:limit]
    ]

    return TrendingSkillsResponse(
        success=True,
        data=TrendingSkillsResult(
            skills=items,
            query_time_ms=round((time.monotonic() - t_start) * 1000, 2),
        ),
        error=None,
    )


@router.get("/health", summary="Discovery module liveness check")
async def discovery_health(
    tg_client: TigerGraphClient = Depends(get_tg_client),
) -> dict[str, Any]:
    """Return liveness status and TigerGraph connectivity for discovery graph."""
    tg_connected = False
    try:
        tg_client.conn_dep.echo()
        tg_connected = True
    except Exception:
        pass

    return {
        "status": "ok",
        "graph": "DepGraph",
        "module": "discovery",
        "tg_connected": tg_connected,
    }


def _recommendation_from_answers(answers: dict[str, str]) -> tuple[str, str]:
    """Mirror frontend quiz recommendation logic for backend-driven graphing."""
    background = answers.get("background")
    solving = answers.get("solving")
    influence = answers.get("influence")
    intensity = answers.get("intensity")
    breadth = answers.get("breadth")

    if background == "people" and solving == "strategy" and influence == "impact":
        return (
            "AI Product Lead",
            "You excel at connecting people, strategy, and execution. Build product strategy, LLM operations, and cross-functional leadership depth.",
        )

    if background == "creative" or solving == "ux":
        if breadth == "specialist":
            return (
                "Design Systems Architect",
                "You are optimized for precision and craft. Focus on design systems, motion systems, and scalable interface governance.",
            )
        return (
            "Creative Frontend Engineer",
            "You combine expressive design with implementation. Focus on modern frontend architecture and user-centric experiences.",
        )

    if background == "logical" and solving == "code":
        if intensity == "research" or breadth == "specialist":
            return (
                "Graph Database & Backend Researcher",
                "You thrive in deep systems work. Focus on graph data systems, backend performance, and distributed design.",
            )
        return (
            "Full-Stack Solutions Architect",
            "You think in end-to-end systems. Focus on API architecture, frontend integration, and scalable platform composition.",
        )

    return (
        "Technical Generalist / PM",
        "Your profile favors synthesis and team alignment. Build broad technical literacy with execution and product prioritization depth.",
    )


def _as_dict_list(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _normalize_nodes(items: list[dict[str, Any]]) -> list[DiscoveryNode]:
    nodes: list[DiscoveryNode] = []
    seen: set[tuple[str, str]] = set()

    for item in items:
        node_type = str(item.get("node_type", "")).strip()
        node_id = str(item.get("node_id", "")).strip()
        label = str(item.get("label", node_id)).strip() or node_id
        category = str(item.get("category", "other")).strip() or "other"

        if node_type not in _ALLOWED_NODE_TYPES or not node_id:
            continue

        score = _score(item.get("score", 0.5), default=0.5)
        key = (node_id, node_type)
        if key in seen:
            continue
        seen.add(key)

        nodes.append(
            DiscoveryNode(
                id=node_id,
                node_type=node_type,
                label=label,
                category=category,
                score=score,
            )
        )

    return nodes


def _normalize_edges(items: list[dict[str, Any]]) -> list[DiscoveryEdge]:
    edges: list[DiscoveryEdge] = []
    seen: set[tuple[str, str, str]] = set()

    for item in items:
        edge_type = str(item.get("edge_type", "")).strip()
        src_id = str(item.get("src_id", "")).strip()
        src_type = str(item.get("src_type", "")).strip()
        tgt_id = str(item.get("tgt_id", "")).strip()
        tgt_type = str(item.get("tgt_type", "")).strip()

        if edge_type not in _ALLOWED_EDGE_TYPES:
            continue
        if not src_id or not tgt_id or not src_type or not tgt_type:
            continue

        key = (edge_type, src_id, tgt_id)
        if key in seen:
            continue
        seen.add(key)

        edges.append(
            DiscoveryEdge(
                edge_type=edge_type,
                src_id=src_id,
                src_type=src_type,
                tgt_id=tgt_id,
                tgt_type=tgt_type,
                weight=_score(item.get("weight", 0.5), default=0.5),
            )
        )

    return edges


def _score(value: Any, default: float) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, score))


def _ensure_minimum_graph(
    recommendation_title: str,
    nodes: list[DiscoveryNode],
    edges: list[DiscoveryEdge],
    minimum_nodes: int = 7,
) -> tuple[list[DiscoveryNode], list[DiscoveryEdge]]:
    """Guarantee a minimally rich graph for downstream visualization."""
    node_index: dict[tuple[str, str], DiscoveryNode] = {
        (node.id, node.node_type): node for node in nodes
    }
    edge_index: dict[tuple[str, str, str], DiscoveryEdge] = {
        (edge.edge_type, edge.src_id, edge.tgt_id): edge for edge in edges
    }

    role_key = (recommendation_title, "RoleNode")
    if role_key not in node_index:
        node_index[role_key] = DiscoveryNode(
            id=recommendation_title,
            node_type="RoleNode",
            label=recommendation_title,
            category="role",
            score=1.0,
        )

    seed_skills = ROLE_SKILL_MAP.get(recommendation_title, [])

    for idx, skill in enumerate(seed_skills):
        skill_key = (skill, "SkillNode")
        if skill_key not in node_index:
            node_index[skill_key] = DiscoveryNode(
                id=skill,
                node_type="SkillNode",
                label=skill,
                category=SKILL_CATEGORY_MAP.get(skill, "other"),
                score=max(0.45, round(0.95 - idx * 0.08, 2)),
            )

        edge_key = ("ROLE_REQUIRES_SKILL", recommendation_title, skill)
        if edge_key not in edge_index:
            edge_index[edge_key] = DiscoveryEdge(
                edge_type="ROLE_REQUIRES_SKILL",
                src_id=recommendation_title,
                src_type="RoleNode",
                tgt_id=skill,
                tgt_type="SkillNode",
                weight=max(0.45, round(0.95 - idx * 0.08, 2)),
            )

    # Add lightweight skill-to-skill links if there are not enough edges.
    for i in range(len(seed_skills) - 1):
        left = seed_skills[i]
        right = seed_skills[i + 1]
        edge_key = ("SKILL_RELATES_TO_SKILL", left, right)
        if edge_key not in edge_index:
            edge_index[edge_key] = DiscoveryEdge(
                edge_type="SKILL_RELATES_TO_SKILL",
                src_id=left,
                src_type="SkillNode",
                tgt_id=right,
                tgt_type="SkillNode",
                weight=0.68,
            )

    # Backfill with cross-role skills if we still have too few nodes.
    if len(node_index) < minimum_nodes:
        for role_skills in ROLE_SKILL_MAP.values():
            for skill in role_skills:
                skill_key = (skill, "SkillNode")
                if skill_key in node_index:
                    continue
                node_index[skill_key] = DiscoveryNode(
                    id=skill,
                    node_type="SkillNode",
                    label=skill,
                    category=SKILL_CATEGORY_MAP.get(skill, "other"),
                    score=0.52,
                )
                edge_key = ("SKILL_RELATES_TO_SKILL", seed_skills[0] if seed_skills else recommendation_title, skill)
                edge_index.setdefault(
                    edge_key,
                    DiscoveryEdge(
                        edge_type="SKILL_RELATES_TO_SKILL",
                        src_id=seed_skills[0] if seed_skills else recommendation_title,
                        src_type="SkillNode" if seed_skills else "RoleNode",
                        tgt_id=skill,
                        tgt_type="SkillNode",
                        weight=0.55,
                    ),
                )
                if len(node_index) >= minimum_nodes:
                    break
            if len(node_index) >= minimum_nodes:
                break

    return list(node_index.values()), list(edge_index.values())


def _build_skill_clusters(nodes: list[DiscoveryNode]) -> list[SkillCluster]:
    grouped: dict[str, set[str]] = defaultdict(set)

    for node in nodes:
        if node.node_type != "SkillNode":
            continue
        grouped[node.category].add(node.label)

    clusters = [
        SkillCluster(category=category, skills=sorted(skills))
        for category, skills in grouped.items()
    ]
    clusters.sort(key=lambda c: (len(c.skills), c.category), reverse=True)
    return clusters


def _trim_graph_density(
    nodes: list[DiscoveryNode],
    edges: list[DiscoveryEdge],
    max_nodes: int = _MAX_GRAPH_NODES,
    max_edges: int = _MAX_GRAPH_EDGES,
) -> tuple[list[DiscoveryNode], list[DiscoveryEdge]]:
    """Cap large graph payloads while preserving high-signal structure."""
    if len(nodes) <= max_nodes and len(edges) <= max_edges:
        return nodes, edges

    ranked_nodes = sorted(
        nodes,
        key=lambda node: (
            1 if node.node_type == "RoleNode" else 0,
            1 if node.node_type == "SkillNode" else 0,
            node.score,
            node.label,
        ),
        reverse=True,
    )
    kept_nodes = ranked_nodes[:max_nodes]
    kept_ids = {(node.id, node.node_type) for node in kept_nodes}

    filtered_edges = [
        edge
        for edge in edges
        if (edge.src_id, edge.src_type) in kept_ids and (edge.tgt_id, edge.tgt_type) in kept_ids
    ]

    if len(filtered_edges) <= max_edges:
        return kept_nodes, filtered_edges

    # Preserve representational diversity so lower-weight edge families still
    # appear in the visual graph when available.
    by_type: dict[str, list[DiscoveryEdge]] = defaultdict(list)
    for edge in filtered_edges:
        by_type[edge.edge_type].append(edge)

    for edge_type in by_type:
        by_type[edge_type].sort(
            key=lambda edge: (edge.weight, edge.src_id, edge.tgt_id),
            reverse=True,
        )

    per_type_keep = max(8, max_edges // max(1, len(by_type) * 3))
    selected: list[DiscoveryEdge] = []
    seen_keys: set[tuple[str, str, str, str, str]] = set()

    for edge_type in sorted(by_type):
        for edge in by_type[edge_type][:per_type_keep]:
            key = (edge.edge_type, edge.src_type, edge.src_id, edge.tgt_type, edge.tgt_id)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            selected.append(edge)

    if len(selected) < max_edges:
        remainder = sorted(
            filtered_edges,
            key=lambda edge: (
                edge.weight,
                edge.edge_type,
                edge.src_id,
                edge.tgt_id,
            ),
            reverse=True,
        )
        for edge in remainder:
            key = (edge.edge_type, edge.src_type, edge.src_id, edge.tgt_type, edge.tgt_id)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            selected.append(edge)
            if len(selected) >= max_edges:
                break

    return kept_nodes, selected[:max_edges]

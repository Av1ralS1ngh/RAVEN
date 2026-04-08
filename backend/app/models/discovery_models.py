"""Pydantic request/response models for Skill Discovery module."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SkillQuizAnswers(BaseModel):
    """Normalized answers from the discovery quiz flow."""

    model_config = ConfigDict(extra="forbid")

    background: Literal["creative", "logical", "people"]
    intensity: Literal["startup", "corporate", "research"]
    solving: Literal["code", "ux", "strategy"]
    influence: Literal["impact", "elegance", "creation"]
    breadth: Literal["generalist", "specialist"]


class DiscoveryAnalyzeRequest(BaseModel):
    """Input payload for POST /api/discovery/analyze."""

    model_config = ConfigDict(extra="forbid")

    answers: SkillQuizAnswers
    related_limit: int = Field(default=8, ge=2, le=20)
    resource_limit: int = Field(default=4, ge=1, le=12)


class DiscoveryNode(BaseModel):
    """One node in a discovery recommendation graph."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    node_type: Literal[
        "RoleNode",
        "SkillNode",
        "DomainNode",
        "TraitNode",
        "LearningResourceNode",
        "LibNode",
        "FileNode",
    ]
    label: str
    category: str
    score: float = Field(ge=0.0, le=1.0)


class DiscoveryEdge(BaseModel):
    """One typed edge in a discovery recommendation graph."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    edge_type: Literal[
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
    ]
    src_id: str
    src_type: str
    tgt_id: str
    tgt_type: str
    weight: float = Field(ge=0.0, le=1.0)


class SkillCluster(BaseModel):
    """UI-friendly grouped skills by category."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    category: str
    skills: list[str]


class DiscoveryGraph(BaseModel):
    """Graph payload returned to frontend for visualization."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    nodes: list[DiscoveryNode]
    edges: list[DiscoveryEdge]
    node_count: int = Field(ge=0)
    edge_count: int = Field(ge=0)


class DiscoveryAnalyzeResult(BaseModel):
    """Full discovery analysis result from one quiz submission."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    recommendation_title: str
    recommendation_desc: str
    graph: DiscoveryGraph
    clusters: list[SkillCluster]
    query_time_ms: float = Field(ge=0.0)


class DiscoveryAnalyzeResponse(BaseModel):
    """Top-level API response envelope for /analyze."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    data: DiscoveryAnalyzeResult | None = None
    error: str | None = None


class TrendingSkillItem(BaseModel):
    """One trending skill item shown in discovery UI."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    category: str
    score: float = Field(ge=0.0)
    connected_roles: list[str]


class TrendingSkillsResult(BaseModel):
    """Trending skills payload."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    skills: list[TrendingSkillItem]
    query_time_ms: float = Field(ge=0.0)


class TrendingSkillsResponse(BaseModel):
    """Top-level API response envelope for /trending."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    data: TrendingSkillsResult | None = None
    error: str | None = None

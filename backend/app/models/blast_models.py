"""Pydantic v2 request/response models for Module 2 — Tech Stack & Blast Radius.

All response models are frozen (immutable after construction) to prevent
accidental mutation in route handlers.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# ─────────────────────────────────────────────────────────────────────────────
# Shared item types
# ─────────────────────────────────────────────────────────────────────────────


class TechItem(BaseModel):
    """A single technology detected by the LLM extractor."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    confidence: float = Field(ge=0.0, le=1.0)
    category: Literal["language", "framework", "tool", "platform", "database", "other"]


class DepBlastEntry(BaseModel):
    """Blast radius summary for a single library.

    Severity is derived from ``affected_count``:
      - high   if affected_count > 15
      - medium if affected_count > 5
      - low    otherwise
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    lib_name: str
    affected_count: int = Field(ge=0)
    severity: Literal["high", "medium", "low"]


class FileImpactEntry(BaseModel):
    """A single file reached during a blast radius traversal."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    repo: str
    depth: int = Field(ge=0)
    language: str


class RepoAnalysisEntry(BaseModel):
    """Tech-stack overlap analysis for one GitHub repository."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    repo_name: str
    primary_language: str
    detected_stack: list[str]
    overlap_stack: list[str]
    missing_stack: list[str]
    overlap_score: float = Field(ge=0.0, le=1.0)
    file_count: int = Field(ge=0)
    dependency_count: int = Field(ge=0)


class MigrationShift(BaseModel):
    """One concrete stack shift needed to match recruiter preferences."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    from_tech: str
    to_tech: str
    category: Literal["language", "framework", "tool", "platform", "database"]
    reason: str
    estimated_impacted_files: int = Field(ge=0)
    affected_dependencies: list[str]


class BestContenderAnalysis(BaseModel):
    """Migration plan and effort estimate for the best repository candidate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    repo_name: str
    overlap_stack: list[str]
    missing_stack: list[str]
    migration_shifts: list[MigrationShift]
    blast_radius_score: int = Field(ge=1, le=10)
    blast_radius_label: Literal["low", "medium", "high", "critical"]
    blast_radius_justification: str


# ─────────────────────────────────────────────────────────────────────────────
# Requests
# ─────────────────────────────────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    """Input for POST /api/blast/analyze."""

    model_config = ConfigDict(extra="forbid")

    recruiter_url: HttpUrl
    github_username: str


class BlastDetailRequest(BaseModel):
    """Input for POST /api/blast/blast-detail — fetches per-file impact for one lib."""

    model_config = ConfigDict(extra="forbid")

    lib_name: str


# ─────────────────────────────────────────────────────────────────────────────
# Responses
# ─────────────────────────────────────────────────────────────────────────────


class AnalyzeResult(BaseModel):
    """Full analysis result combining LLM tech stack + dep blast data."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tech_stack: list[TechItem]
    """All detected technologies sorted by confidence descending."""

    top_tech_stack: list[TechItem]
    """Top 5 items by confidence — convenient subset for UI hero section."""

    recruiter_stack: list[str]
    """Canonical recruiter target stack used for matching and migration planning."""

    repo_analysis: list[RepoAnalysisEntry]
    """Per-repository overlap analysis against recruiter stack."""

    best_contender: BestContenderAnalysis | None
    """Best repository to showcase and migration effort plan."""

    dep_blast: list[DepBlastEntry]
    """One entry per unique library, with blast radius counts and severity."""

    file_impacts: list[FileImpactEntry]
    """Per-file impact entries across scanned repos, ranked by impact depth."""

    repos_analyzed: int
    """Number of GitHub repos that were processed."""

    query_time_ms: float
    """Total wall-clock latency of the full /analyze request in milliseconds."""


class AnalyzeResponse(BaseModel):
    """Top-level API response envelope for /analyze."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    data: AnalyzeResult | None = None
    error: str | None = None


class BlastDetailResponse(BaseModel):
    """Top-level API response envelope for /blast-detail."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    data: list[FileImpactEntry] | None = None
    error: str | None = None


def analyze_response_json_schema() -> dict:
    """Return strict JSON Schema for frontend/API contract generation."""
    return AnalyzeResponse.model_json_schema()

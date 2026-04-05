"""Pydantic v2 request/response models for Module 2 — Tech Stack & Blast Radius.

All response models are frozen (immutable after construction) to prevent
accidental mutation in route handlers.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, HttpUrl


# ─────────────────────────────────────────────────────────────────────────────
# Shared item types
# ─────────────────────────────────────────────────────────────────────────────


class TechItem(BaseModel):
    """A single technology detected by the LLM extractor."""

    model_config = ConfigDict(frozen=True)

    name: str
    confidence: float
    category: Literal["language", "framework", "tool", "platform", "database", "other"]


class DepBlastEntry(BaseModel):
    """Blast radius summary for a single library.

    Severity is derived from ``affected_count``:
      - high   if affected_count > 15
      - medium if affected_count > 5
      - low    otherwise
    """

    model_config = ConfigDict(frozen=True)

    lib_name: str
    affected_count: int
    severity: Literal["high", "medium", "low"]


class FileImpactEntry(BaseModel):
    """A single file reached during a blast radius traversal."""

    model_config = ConfigDict(frozen=True)

    path: str
    repo: str
    depth: int
    language: str


# ─────────────────────────────────────────────────────────────────────────────
# Requests
# ─────────────────────────────────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    """Input for POST /api/blast/analyze."""

    recruiter_url: HttpUrl
    github_username: str


class BlastDetailRequest(BaseModel):
    """Input for POST /api/blast/blast-detail — fetches per-file impact for one lib."""

    lib_name: str


# ─────────────────────────────────────────────────────────────────────────────
# Responses
# ─────────────────────────────────────────────────────────────────────────────


class AnalyzeResult(BaseModel):
    """Full analysis result combining LLM tech stack + dep blast data."""

    model_config = ConfigDict(frozen=True)

    tech_stack: list[TechItem]
    """All detected technologies sorted by confidence descending."""

    top_tech_stack: list[TechItem]
    """Top 5 items by confidence — convenient subset for UI hero section."""

    dep_blast: list[DepBlastEntry]
    """One entry per unique library, with blast radius counts and severity."""

    file_impacts: list[FileImpactEntry]
    """Per-file impact entries — empty until /blast-detail is called."""

    repos_analyzed: int
    """Number of GitHub repos that were processed."""

    query_time_ms: float
    """Total wall-clock latency of the full /analyze request in milliseconds."""


class AnalyzeResponse(BaseModel):
    """Top-level API response envelope for /analyze."""

    success: bool
    data: AnalyzeResult | None = None
    error: str | None = None


class BlastDetailResponse(BaseModel):
    """Top-level API response envelope for /blast-detail."""

    success: bool
    data: list[FileImpactEntry] | None = None
    error: str | None = None

"""Pydantic v2 request/response models for Module 1 — Network Path Finder.

All response models are frozen (immutable after construction) to prevent
accidental mutation in route handlers.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# ─────────────────────────────────────────────────────────────────────────────
# Request
# ─────────────────────────────────────────────────────────────────────────────


class PathRequest(BaseModel):
    """Input for the POST /find endpoint.

    Attributes:
        recruiter_url: Full LinkedIn profile URL of the target recruiter.
        your_linkedin_id: The caller's own LinkedIn public identifier
            (e.g. ``"john-doe-123"``), used as the path source vertex.
        max_hops: BFS depth limit. Clamped to 1–12.
    """

    recruiter_url: HttpUrl
    your_linkedin_id: str
    max_hops: int = Field(default=12, ge=1, le=12)


# ─────────────────────────────────────────────────────────────────────────────
# Response building blocks
# ─────────────────────────────────────────────────────────────────────────────


class PersonSummary(BaseModel):
    """A single person node as returned in a path result.

    Frozen so that path lists cannot be accidentally mutated by route logic.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    headline: str
    company: str
    linkedin_url: str
    mutual_count: int


class PathResult(BaseModel):
    """The computed path and supporting metadata.

    Attributes:
        path: Ordered list of people from the caller → … → recruiter.
        hop_count: Number of edges in the primary path.
        alternative_paths: Up to 3 alternative routes of equal or greater
            length (may be empty if the graph has no alternatives).
        total_connections_mapped: How many unique Person vertices were upserted
            into TigerGraph during this request.
        query_time_ms: Total wall-clock time for the full request in ms.
    """

    model_config = ConfigDict(frozen=True)

    path: list[PersonSummary]
    hop_count: int
    alternative_paths: list[list[PersonSummary]]
    total_connections_mapped: int
    query_time_ms: float


# ─────────────────────────────────────────────────────────────────────────────
# Envelope
# ─────────────────────────────────────────────────────────────────────────────


class PathResponse(BaseModel):
    """Top-level API response envelope for all path-finder endpoints."""

    success: bool
    data: PathResult | None = None
    error: str | None = None

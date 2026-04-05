"""Module 2 API routes — Tech Stack Analyzer & Dependency Blast Radius.

Endpoints:
  POST /api/blast/analyze       — scrape recruiter profile + parse GitHub repos
  POST /api/blast/blast-detail  — drill into per-file impact for one library
  GET  /api/blast/health        — liveness + TigerGraph DepGraph connectivity
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from playwright.async_api import async_playwright

from app.api.deps import SettingsDep, get_tg_client
from app.models.blast_models import (
    AnalyzeRequest,
    AnalyzeResponse,
    AnalyzeResult,
    BlastDetailRequest,
    BlastDetailResponse,
    DepBlastEntry,
    FileImpactEntry,
    TechItem,
)
from app.services.github_parser import GitHubParser
from app.services.llm_extractor import LLMExtractor
from app.services.tigergraph_client import TigerGraphClient, TigerGraphError

logger = logging.getLogger(__name__)
# Ensure logger output goes to stdout (uvicorn output)
if not logger.handlers:
    # Just setting level is fine, uvicorn configures the root logger
    pass

router = APIRouter()

# Concurrency limit per request for repo dep-file fetching.
_REPO_SEM_LIMIT = 5


# ─────────────────────────────────────────────────────────────────────────────
# POST /analyze
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze recruiter tech stack + GitHub dependency blast radius",
)
async def analyze(
    request_body: AnalyzeRequest,
    settings: SettingsDep,
    tg_client: TigerGraphClient = Depends(get_tg_client),
) -> AnalyzeResponse:
    """Full pipeline:
      1. Scrape recruiter LinkedIn profile (Playwright, public page).
      2. Parse GitHub repos for deps and source file imports.
      3. Both run concurrently via asyncio.gather.
      4. Upsert dep graph into TigerGraph.
      5. Run blast radius for all discovered libs.
      6. Return combined result.
    """
    t_start = time.monotonic()

    # ── 1. Concurrent: LinkedIn scrape + GitHub parse ─────────────────────────
    try:
        tech_items_raw, (all_libs, all_files, all_edges, repos_count) = (
            await asyncio.gather(
                _scrape_and_extract(str(request_body.recruiter_url), settings.groq_api_key),
                _parse_github(request_body.github_username, settings.github_token),
            )
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error during concurrent scrape/parse")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    # ── 2. Upsert dep graph ───────────────────────────────────────────────────
    logger.info("Upserting: %d files, %d libs, %d edges", len(all_files), len(all_libs), len(all_edges))
    try:
        tg_client.upsert_dep_graph(
            files=all_files,
            libs=all_libs,
            edges=all_edges,
        )
    except TigerGraphError as exc:
        logger.error("TigerGraph upsert failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    # ── 3. Blast radius for all libs ──────────────────────────────────────────
    dep_blast: list[DepBlastEntry] = []
    sem = asyncio.Semaphore(_REPO_SEM_LIMIT)

    async def _blast_one(lib_name: str) -> DepBlastEntry | None:
        async with sem:
            try:
                result = tg_client.run_blast_radius(lib_name, max_hops=4)
                affected = len(result.get("blast_radius", []))
                return DepBlastEntry(
                    lib_name=lib_name,
                    affected_count=affected,
                    severity=_severity(affected),
                )
            except TigerGraphError as exc:
                logger.warning("Blast radius skipped for %s: %s", lib_name, exc)
                return None

    # Only run blast for lib names that are unique (dedup by name).
    unique_lib_names = list({lb.name for lb in all_libs})
    blast_results = await asyncio.gather(*[_blast_one(n) for n in unique_lib_names])
    dep_blast = sorted(
        [r for r in blast_results if r is not None],
        key=lambda e: e.affected_count,
        reverse=True,
    )

    # ── 4. Build response ─────────────────────────────────────────────────────
    query_time_ms = round((time.monotonic() - t_start) * 1000, 2)

    tech_sorted = sorted(tech_items_raw, key=lambda t: t.confidence, reverse=True)

    result = AnalyzeResult(
        tech_stack=tech_sorted,
        top_tech_stack=tech_sorted[:5],
        dep_blast=dep_blast,
        file_impacts=[],  # Populated on /blast-detail
        repos_analyzed=repos_count,
        query_time_ms=query_time_ms,
    )

    return AnalyzeResponse(success=True, data=result)


# ─────────────────────────────────────────────────────────────────────────────
# POST /blast-detail
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/blast-detail",
    response_model=BlastDetailResponse,
    summary="Get per-file impact detail for a single library",
)
async def blast_detail(
    request_body: BlastDetailRequest,
    tg_client: TigerGraphClient = Depends(get_tg_client),
) -> BlastDetailResponse:
    """Drill into which files are affected by a specific library change."""
    try:
        raw = tg_client.run_blast_radius(request_body.lib_name, max_hops=4)
    except TigerGraphError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    items = [
        FileImpactEntry(
            path=entry.get("file_path", ""),
            repo=entry.get("repo", ""),
            depth=int(entry.get("depth", 0)),
            language="",  # Not returned by GSQL; can be enriched from FileNode attrs
        )
        for entry in raw.get("blast_radius", [])
    ]

    return BlastDetailResponse(success=True, data=items)


# ─────────────────────────────────────────────────────────────────────────────
# GET /health
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/health", summary="Blast module liveness check")
async def blast_health(
    tg_client: TigerGraphClient = Depends(get_tg_client),
) -> dict[str, Any]:
    """Return liveness status and TigerGraph connectivity for DepGraph."""
    tg_connected = False
    try:
        tg_client.conn_dep.echo()
        tg_connected = True
    except Exception:
        pass

    return {
        "status": "ok",
        "graph": "DepGraph",
        "tg_connected": tg_connected,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Private pipeline helpers
# ─────────────────────────────────────────────────────────────────────────────


async def _scrape_and_extract(profile_url: str, gemini_api_key: str) -> list[TechItem]:
    """Scrape LinkedIn public profile page with Playwright, then extract tech.

    Uses a headless Chromium browser to GET the public page (no login needed
    for public profiles). Extracts all visible text, then sends it to Gemini.

    Returns:
        List of TechItem objects, or [] if Playwright or Gemini fails.
    """
    profile_text = ""
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(profile_url, wait_until="domcontentloaded", timeout=20_000)
            # Extract all visible text from the page body.
            profile_text = await page.evaluate(
                "() => document.body.innerText"
            )
            await browser.close()
    except Exception as exc:
        logger.warning("Playwright scrape failed for %s: %s", profile_url, exc)
        # Non-fatal — proceed with empty profile text.

    if not profile_text.strip():
        logger.info("Empty profile text from %s — skipping LLM extraction.", profile_url)
        return []

    extractor = LLMExtractor(api_key=gemini_api_key)
    raw_items = await extractor.extract_tech_stack(profile_text)

    return [
        TechItem(
            name=item.name,
            confidence=item.confidence,
            category=_normalise_category(item.category),
        )
        for item in raw_items
    ]


async def _parse_github(
    github_username: str,
    github_token: str,
) -> tuple[list, list, list, int]:
    """Fetch and parse all repos for a GitHub user.

    Returns:
        ``(all_libs, all_files, all_edges, repos_count)``
    """
    all_libs: list = []
    all_files: list = []
    all_edges: list = []

    async with GitHubParser(github_token) as parser:
        repos = await parser.get_user_repos(github_username)
        if not repos:
            return all_libs, all_files, all_edges, 0

        sem = asyncio.Semaphore(_REPO_SEM_LIMIT)

        async def process_repo(repo):
            async with sem:
                dep_files = await parser.get_dep_files(repo.full_name, repo.default_branch)
                return await parser.parse_dependencies(
                    dep_files, repo.full_name, repo.default_branch
                )

        results = await asyncio.gather(
            *[process_repo(r) for r in repos],
            return_exceptions=True,
        )

        for res in results:
            if isinstance(res, BaseException):
                logger.warning("Repo parse error (skipped): %s", res)
                continue
            libs, files, edges = res
            all_libs.extend(libs)
            all_files.extend(files)
            all_edges.extend(edges)

    # Deduplicate libs by name (keep first seen).
    seen: set[str] = set()
    deduped_libs = []
    for lb in all_libs:
        if lb.name not in seen:
            seen.add(lb.name)
            deduped_libs.append(lb)

    return deduped_libs, all_files, all_edges, len(repos)


# ─────────────────────────────────────────────────────────────────────────────
# Utility functions
# ─────────────────────────────────────────────────────────────────────────────


def _severity(count: int) -> str:
    """Convert an affected-file count into a severity label."""
    if count > 15:
        return "high"
    if count > 5:
        return "medium"
    return "low"


def _normalise_category(raw: str) -> str:
    """Map any raw category string to a TechItem Literal-safe value."""
    valid = {"language", "framework", "tool", "platform", "database"}
    return raw if raw in valid else "other"

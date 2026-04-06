"""Module 2 API routes — Tech Stack Analyzer & Dependency Blast Radius.

Endpoints:
  POST /api/blast/analyze       — scrape recruiter profile + parse GitHub repos
  POST /api/blast/blast-detail  — drill into per-file impact for one library
  GET  /api/blast/health        — liveness + TigerGraph DepGraph connectivity
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from playwright.async_api import async_playwright

from app.api.deps import SettingsDep, get_tg_client
from app.models.blast_models import (
    AnalyzeRequest,
    AnalyzeResponse,
    AnalyzeResult,
    BestContenderAnalysis,
    BlastDetailRequest,
    BlastDetailResponse,
    DepBlastEntry,
    FileImpactEntry,
    MigrationShift,
    RepoAnalysisEntry,
    TechItem,
)
from app.services.analysis_run_logger import log_analyze_run
from app.services.famous_personality_stacks import (
    get_seeded_stack_for_linkedin_url,
    linkedin_slug_from_url,
)
from app.services.github_parser import GitHubParser
from app.services.llm_extractor import LLMExtractor
from app.services.tech_taxonomy import category_of, strict_dedupe_stack
from app.services.tigergraph_client import (
    DepEdge,
    FileNode,
    LibNode,
    TigerGraphClient,
    TigerGraphError,
)

logger = logging.getLogger(__name__)
# Ensure logger output goes to stdout (uvicorn output)
if not logger.handlers:
    # Just setting level is fine, uvicorn configures the root logger
    pass

router = APIRouter()

# Concurrency limit per request for repo dep-file fetching.
_REPO_SEM_LIMIT = 5
_MIN_TECH_STACK_ITEMS = 8
_MAX_TECH_STACK_ITEMS = 8
_MIN_TECH_STACK_FILL = [
    "Python",
    "TypeScript",
    "Docker",
    "Kubernetes",
    "AWS",
    "PostgreSQL",
    "GitHub Actions",
    "OpenAPI",
    "Redis",
    "GraphQL",
]


@dataclass(slots=True)
class _RepoScan:
    """Internal aggregate for one parsed repository."""

    repo_name: str
    primary_language: str
    stack: list[str]
    dependency_names: list[str]
    file_count: int
    dependency_count: int


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
        (tech_items_raw, extraction_warning, extraction_source), (all_libs, all_files, all_edges, repos_count, repo_scans) = (
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

    # Upsert recruiter-stack fingerprint separately for known/derived profiles.
    if tech_items_raw:
        try:
            _upsert_recruiter_stack_profile(
                tg_client=tg_client,
                profile_url=str(request_body.recruiter_url),
                tech_items=tech_items_raw,
            )
        except TigerGraphError as exc:
            logger.warning("Recruiter stack upsert skipped: %s", exc)

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

    recruiter_stack = [item.name for item in tech_sorted]
    repo_analysis, best_contender = _build_repo_and_migration_analysis(
        repo_scans=repo_scans,
        recruiter_stack=recruiter_stack,
        dep_blast=dep_blast,
    )

    result = AnalyzeResult(
        tech_stack=tech_sorted,
        top_tech_stack=tech_sorted[:5],
        recruiter_stack=recruiter_stack,
        repo_analysis=repo_analysis,
        best_contender=best_contender,
        dep_blast=dep_blast,
        file_impacts=_build_repo_file_impacts(
            files=all_files,
            edges=all_edges,
            dep_blast=dep_blast,
            recruiter_stack=recruiter_stack,
        ),
        repos_analyzed=repos_count,
        query_time_ms=query_time_ms,
    )

    # Best-effort telemetry for building supervised ML datasets.
    log_analyze_run(
        recruiter_url=str(request_body.recruiter_url),
        github_username=request_body.github_username,
        analyze_result=result.model_dump(mode="json"),
        metadata={
            "source": "api/blast/analyze",
            "repo_scans_count": len(repo_scans),
            "libs_count": len(all_libs),
            "files_count": len(all_files),
            "edges_count": len(all_edges),
            "recruiter_stack_source": extraction_source,
            "recruiter_stack_count": len(tech_items_raw),
        },
    )

    return AnalyzeResponse(success=True, data=result, error=extraction_warning)


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
            change_score=_score_from_depth(int(entry.get("depth", 0))),
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


async def _scrape_and_extract(
    profile_url: str,
    gemini_api_key: str,
) -> tuple[list[TechItem], str | None, str]:
    """Scrape LinkedIn public profile page with Playwright, then extract tech.

    Uses a headless Chromium browser to GET the public page (no login needed
    for public profiles). Extracts all visible text, then sends it to Gemini.

    Returns:
        Tuple of ``(tech_items, warning_message, source_tag)``.
    """
    profile_text = ""
    warning: str | None = None
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(profile_url, wait_until="domcontentloaded", timeout=20_000)
            # Give dynamic sections a moment to render.
            await page.wait_for_timeout(1500)
            # Prefer profile content containers over full-body navigation noise.
            profile_text = await page.evaluate(
                """
                () => {
                    const chunks = [];
                    const selectors = ["main", "section", "article"];
                    for (const sel of selectors) {
                        for (const el of document.querySelectorAll(sel)) {
                            const txt = (el.innerText || "").trim();
                            if (txt.length > 0) {
                                chunks.push(txt);
                            }
                        }
                    }
                    const preferred = chunks.join("\n\n").trim();
                    const fallback = (document.body && document.body.innerText) ? document.body.innerText : "";
                    const merged = preferred || fallback;
                    return merged.replace(/\\s+/g, " ").trim();
                }
                """
            )
            await browser.close()
    except Exception as exc:
        logger.warning("Playwright scrape failed for %s: %s", profile_url, exc)
        # Non-fatal — proceed with empty profile text.

    if not profile_text.strip():
        logger.info("Empty profile text from %s — skipping LLM extraction.", profile_url)
        return await _fallback_recruiter_stack(
            profile_url=profile_url,
            gemini_api_key=gemini_api_key,
            warning=(
                "Could not read recruiter profile content from LinkedIn (page returned empty text)."
            ),
        )

    if _looks_like_linkedin_authwall(profile_text):
        return await _fallback_recruiter_stack(
            profile_url=profile_url,
            gemini_api_key=gemini_api_key,
            warning=(
                "LinkedIn blocked profile scraping with an authwall/challenge page, so recruiter tech stack "
                "could not be extracted."
            ),
        )

    # Guard against tiny or login/challenge pages that produce noisy false positives.
    if len(profile_text) < 250 or len(profile_text.split()) < 40:
        logger.info("Low-signal profile text from %s — skipping LLM extraction.", profile_url)
        warning = "LinkedIn returned very low-signal profile text; recruiter stack extraction may be incomplete."

    extractor = LLMExtractor(api_key=gemini_api_key)
    raw_items = await extractor.extract_tech_stack(profile_text)

    items = [
        TechItem(
            name=item.name,
            confidence=item.confidence,
            category=_normalise_category(item.category),
        )
        for item in raw_items
    ]
    items = _ensure_minimum_tech_items(profile_url, items)

    if not items:
        fallback_warning = warning or (
            "No reliable technology signals were found in the recruiter profile text. "
            "This often happens when LinkedIn content is restricted."
        )
        return await _fallback_recruiter_stack(
            profile_url=profile_url,
            gemini_api_key=gemini_api_key,
            warning=fallback_warning,
        )

    return items, warning, "linkedin_scrape"


async def _parse_github(
    github_username: str,
    github_token: str,
) -> tuple[list, list, list, int, list[_RepoScan]]:
    """Fetch and parse all repos for a GitHub user.

    Returns:
        ``(all_libs, all_files, all_edges, repos_count, repo_scans)``
    """
    all_libs: list = []
    all_files: list = []
    all_edges: list = []
    repo_scans: list[_RepoScan] = []

    async with GitHubParser(github_token) as parser:
        repos = await parser.get_user_repos(github_username)
        if not repos:
            return all_libs, all_files, all_edges, 0, repo_scans

        sem = asyncio.Semaphore(_REPO_SEM_LIMIT)

        async def process_repo(repo):
            async with sem:
                dep_files = await parser.get_dep_files(repo.full_name, repo.default_branch)
                libs, files, edges = await parser.parse_dependencies(
                    dep_files, repo.full_name, repo.default_branch
                )
                return repo, libs, files, edges

        results = await asyncio.gather(
            *[process_repo(r) for r in repos],
            return_exceptions=True,
        )

        for res in results:
            if isinstance(res, BaseException):
                logger.warning("Repo parse error (skipped): %s", res)
                continue
            repo, libs, files, edges = res
            all_libs.extend(libs)
            all_files.extend(files)
            all_edges.extend(edges)

            raw_stack = [repo.language, *[f.language for f in files], *[lb.name for lb in libs]]
            canonical_stack = strict_dedupe_stack(raw_stack)
            dependency_names = strict_dedupe_stack([lb.name for lb in libs])

            repo_scans.append(
                _RepoScan(
                    repo_name=repo.full_name,
                    primary_language=(repo.language or "").strip(),
                    stack=canonical_stack,
                    dependency_names=dependency_names,
                    file_count=len(files),
                    dependency_count=len(dependency_names),
                )
            )

    # Deduplicate libs by name (keep first seen).
    seen: set[str] = set()
    deduped_libs = []
    for lb in all_libs:
        if lb.name not in seen:
            seen.add(lb.name)
            deduped_libs.append(lb)

    return deduped_libs, all_files, all_edges, len(repos), repo_scans


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


def _looks_like_linkedin_authwall(text: str) -> bool:
    """Detect LinkedIn authwall/challenge HTML rendered instead of profile content."""
    lower = text.lower()
    markers = (
        "authwall",
        "sessionredirect",
        "trkinfo",
        "window.location.href",
        "linkedin.com/authwall",
    )
    return any(marker in lower for marker in markers)


async def _fallback_recruiter_stack(
    profile_url: str,
    gemini_api_key: str,
    warning: str,
) -> tuple[list[TechItem], str | None, str]:
    """Fallback to curated famous-profile stacks, then optional LLM inference."""
    seeded = strict_dedupe_stack(get_seeded_stack_for_linkedin_url(profile_url))
    if seeded:
        items = [
            TechItem(
                name=name,
                confidence=0.66,
                category=_normalise_category(category_of(name)),
            )
            for name in seeded
        ]
        items = _ensure_minimum_tech_items(profile_url, items)
        return (
            items,
            warning + " Using curated stack seed for this known profile.",
            "curated_seed",
        )

    extractor = LLMExtractor(api_key=gemini_api_key)
    inferred = await extractor.infer_tech_stack_from_profile_url(profile_url)
    if inferred:
        items = [
            TechItem(
                name=item.name,
                confidence=min(item.confidence, 0.7),
                category=_normalise_category(item.category),
            )
            for item in inferred
        ]
        items = _ensure_minimum_tech_items(profile_url, items)
        return (
            items,
            warning + " Using LLM inferred stack fallback from profile URL.",
            "llm_inferred",
        )

    # Final safety net: always provide a minimally useful stack for UI.
    return _ensure_minimum_tech_items(profile_url, []), warning, "unavailable"


def _ensure_minimum_tech_items(profile_url: str, items: list[TechItem]) -> list[TechItem]:
    """Ensure recruiter stack always has at least _MIN_TECH_STACK_ITEMS entries."""
    best_by_name: dict[str, TechItem] = {}
    for item in items:
        key = item.name.strip().lower()
        if not key:
            continue
        prev = best_by_name.get(key)
        if prev is None or item.confidence > prev.confidence:
            best_by_name[key] = item

    fill_candidates = [
        *strict_dedupe_stack(get_seeded_stack_for_linkedin_url(profile_url)),
        *strict_dedupe_stack(_MIN_TECH_STACK_FILL),
    ]

    for name in fill_candidates:
        if len(best_by_name) >= _MIN_TECH_STACK_ITEMS:
            break
        key = name.lower()
        if key in best_by_name:
            continue
        best_by_name[key] = TechItem(
            name=name,
            confidence=0.61,
            category=_normalise_category(category_of(name)),
        )

    ranked = sorted(best_by_name.values(), key=lambda item: item.confidence, reverse=True)
    return ranked[:_MAX_TECH_STACK_ITEMS]


def _upsert_recruiter_stack_profile(
    tg_client: TigerGraphClient,
    profile_url: str,
    tech_items: list[TechItem],
) -> None:
    """Persist recruiter stack as profile-scoped vertices in DepGraph.

    We use profile-scoped LibNode IDs so these entries never affect blast counts
    for regular repository dependency libraries.
    """
    slug = linkedin_slug_from_url(profile_url)
    if not slug or not tech_items:
        return

    slug_token = _slug_token(slug)
    profile_file_id = f"profile://linkedin/{slug_token}"
    files = [FileNode(path=profile_file_id, repo="linkedin_profiles", language="profile")]

    libs: list[LibNode] = []
    edges: list[DepEdge] = []
    seen: set[str] = set()
    for item in tech_items:
        tech_name = item.name.strip()
        if not tech_name:
            continue
        key = tech_name.lower()
        if key in seen:
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

    if not libs:
        return

    tg_client.upsert_dep_graph(files=files, libs=libs, edges=edges)


def _slug_token(value: str) -> str:
    """Create safe lowercase identifier tokens for synthetic vertex IDs."""
    token = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    token = token.strip("_")
    return token or "unknown"


def _build_repo_and_migration_analysis(
    repo_scans: list[_RepoScan],
    recruiter_stack: list[str],
    dep_blast: list[DepBlastEntry],
) -> tuple[list[RepoAnalysisEntry], BestContenderAnalysis | None]:
    """Produce per-repo overlap stats and a migration plan for best contender."""
    recruiter_set = set(recruiter_stack)
    blast_count_map = {entry.lib_name.lower(): entry.affected_count for entry in dep_blast}

    repo_analysis: list[RepoAnalysisEntry] = []
    scan_by_repo: dict[str, _RepoScan] = {}
    for scan in repo_scans:
        scan_by_repo[scan.repo_name] = scan
        overlap = sorted(recruiter_set.intersection(scan.stack), key=str.lower)
        missing = sorted(recruiter_set.difference(scan.stack), key=str.lower)
        score = _compute_overlap_score(
            overlap_count=len(overlap),
            recruiter_count=len(recruiter_set),
            repo_count=len(scan.stack),
        )
        repo_analysis.append(
            RepoAnalysisEntry(
                repo_name=scan.repo_name,
                primary_language=scan.primary_language,
                detected_stack=scan.stack,
                overlap_stack=overlap,
                missing_stack=missing,
                overlap_score=score,
                file_count=scan.file_count,
                dependency_count=scan.dependency_count,
            )
        )

    repo_analysis.sort(
        key=lambda item: (item.overlap_score, len(item.overlap_stack), item.dependency_count),
        reverse=True,
    )

    if not repo_analysis:
        return repo_analysis, None

    top_repo = repo_analysis[0]
    top_scan = scan_by_repo.get(top_repo.repo_name)
    if top_scan is None:
        return repo_analysis, None

    migration_shifts = _build_migration_shifts(
        top_scan=top_scan,
        missing_stack=top_repo.missing_stack,
        blast_count_map=blast_count_map,
    )
    score, label = _blast_score(top_scan, migration_shifts)
    justification = _build_justification(top_scan, migration_shifts, score, label)

    best_contender = BestContenderAnalysis(
        repo_name=top_repo.repo_name,
        overlap_stack=top_repo.overlap_stack,
        missing_stack=top_repo.missing_stack,
        migration_shifts=migration_shifts,
        blast_radius_score=score,
        blast_radius_label=label,
        blast_radius_justification=justification,
    )
    return repo_analysis, best_contender


def _build_repo_file_impacts(
    files: list,
    edges: list,
    dep_blast: list[DepBlastEntry],
    recruiter_stack: list[str],
) -> list[FileImpactEntry]:
    """Build per-file impact entries for all scanned repos.

    ``change_score`` is a 0-100 effort estimate derived from:
      - dependency blast risk (TigerGraph reach)
      - dependency concentration in the file
      - alignment with recruiter stack signals

    ``depth`` remains for grouped UI display and is derived from score.
    """
    blast_count_by_lib = {entry.lib_name.lower(): entry.affected_count for entry in dep_blast}
    recruiter_terms = {name.lower() for name in strict_dedupe_stack(recruiter_stack)}
    recruiter_categories = {
        cat
        for cat in (category_of(name) for name in recruiter_stack)
        if cat in {"language", "framework", "database", "platform", "tool"}
    }

    libs_by_path: dict[str, set[str]] = {}
    for edge in edges:
        if getattr(edge, "edge_type", "") != "IMPORTS":
            continue
        if getattr(edge, "src_type", "") != "FileNode":
            continue
        if getattr(edge, "tgt_type", "") != "LibNode":
            continue
        src_id = str(getattr(edge, "src_id", "")).strip()
        tgt_id = str(getattr(edge, "tgt_id", "")).strip()
        if not src_id or not tgt_id:
            continue
        libs_by_path.setdefault(src_id, set()).add(tgt_id)

    dedup: dict[tuple[str, str], FileImpactEntry] = {}
    for file_node in files:
        path = str(getattr(file_node, "path", "")).strip()
        repo = str(getattr(file_node, "repo", "")).strip()
        language = str(getattr(file_node, "language", "")).strip()
        if not path or not repo:
            continue

        imported_libs = libs_by_path.get(path, set())
        score = _compute_file_change_score(
            imported_libs=imported_libs,
            blast_count_by_lib=blast_count_by_lib,
            recruiter_terms=recruiter_terms,
            recruiter_categories=recruiter_categories,
        )
        depth = _depth_from_score(score)

        key = (repo, path)
        prev = dedup.get(key)
        candidate = FileImpactEntry(
            path=path,
            repo=repo,
            depth=depth,
            change_score=score,
            language=language,
        )
        if (
            prev is None
            or candidate.depth < prev.depth
            or (candidate.depth == prev.depth and candidate.change_score > prev.change_score)
        ):
            dedup[key] = candidate

    return sorted(
        dedup.values(),
        key=lambda item: (item.repo.lower(), item.depth, -item.change_score, item.path.lower()),
    )


def _compute_file_change_score(
    imported_libs: set[str],
    blast_count_by_lib: dict[str, int],
    recruiter_terms: set[str],
    recruiter_categories: set[str],
) -> int:
    """Compute a per-file migration effort score in [0, 100].

    The score intentionally stretches the middle range so repos don't appear
    artificially "all low" when multiple files have moderate impact.
    """
    imported_lib_count = len(imported_libs)
    if imported_lib_count <= 0:
        return 14

    blast_counts = [blast_count_by_lib.get(lib.lower(), 0) for lib in imported_libs]
    max_blast = max(blast_counts) if blast_counts else 0
    avg_blast = (sum(blast_counts) / max(1, imported_lib_count)) if blast_counts else 0.0
    blast_risk = min(1.0, ((0.55 * max_blast) + (0.45 * avg_blast)) / 25.0)

    dependency_concentration = min(1.0, imported_lib_count / 10.0)

    exact_matches = 0
    category_matches = 0
    for lib in imported_libs:
        lib_key = lib.lower()
        if lib_key in recruiter_terms:
            exact_matches += 1
        if category_of(lib) in recruiter_categories:
            category_matches += 1

    if recruiter_terms:
        exact_ratio = exact_matches / imported_lib_count
        category_ratio = category_matches / imported_lib_count
        alignment_ratio = min(1.0, (0.65 * category_ratio) + (0.35 * exact_ratio))
        mismatch_pressure = 1.0 - alignment_ratio
    else:
        mismatch_pressure = 0.0

    # Weighted risk blend in [0, 1].
    raw_score = (0.5 * blast_risk) + (0.35 * mismatch_pressure) + (0.15 * dependency_concentration)

    # Non-linear stretch gives more separation in the mid-range.
    stretched = raw_score**0.78
    score = int(round(14 + (stretched * 84)))

    # Boost clear high-impact signals.
    if max_blast >= 20:
        score += 10
    elif max_blast >= 10:
        score += 6

    if imported_lib_count >= 8:
        score += 6
    elif imported_lib_count >= 5:
        score += 3

    if mismatch_pressure >= 0.65:
        score += 8
    elif mismatch_pressure >= 0.45:
        score += 4

    return max(14, min(98, score))


def _depth_from_score(score: int) -> int:
    """Map 0-100 score to stable impact depth buckets for grouping UI."""
    if score >= 78:
        return 1
    if score >= 56:
        return 2
    if score >= 32:
        return 3
    return 4


def _score_from_depth(depth: int) -> int:
    """Fallback score for endpoints that only have traversal depth."""
    if depth <= 1:
        return 88
    if depth == 2:
        return 66
    if depth == 3:
        return 44
    return 22


def _compute_overlap_score(overlap_count: int, recruiter_count: int, repo_count: int) -> float:
    """F1-style overlap score in [0, 1], balancing precision and recall."""
    if recruiter_count == 0 or repo_count == 0 or overlap_count == 0:
        return 0.0

    precision = overlap_count / repo_count
    recall = overlap_count / recruiter_count
    if precision + recall == 0:
        return 0.0
    return round((2 * precision * recall) / (precision + recall), 3)


def _build_migration_shifts(
    top_scan: _RepoScan,
    missing_stack: list[str],
    blast_count_map: dict[str, int],
) -> list[MigrationShift]:
    """Build specific technical shifts to align one repo with recruiter stack."""
    shifts: list[MigrationShift] = []
    repo_stack = set(top_scan.stack)

    for target in missing_stack:
        target_category = category_of(target)
        source = _pick_source_tech(target_category=target_category, repo_stack=repo_stack)
        affected = _estimate_impacted_files(
            source_tech=source,
            target_category=target_category,
            file_count=top_scan.file_count,
            blast_count_map=blast_count_map,
        )
        impacted_deps = _dependencies_for_shift(
            source_tech=source,
            dependency_names=top_scan.dependency_names,
        )

        shifts.append(
            MigrationShift(
                from_tech=source,
                to_tech=target,
                category=target_category,
                reason=f"Align {target_category} stack with recruiter preference for {target}.",
                estimated_impacted_files=affected,
                affected_dependencies=impacted_deps,
            )
        )

    return shifts


def _pick_source_tech(target_category: str, repo_stack: set[str]) -> str:
    """Choose a source technology from repo stack that best matches category."""
    for tech in sorted(repo_stack, key=str.lower):
        if category_of(tech) == target_category:
            return tech
    for tech in sorted(repo_stack, key=str.lower):
        if category_of(tech) in {"framework", "tool"}:
            return tech
    return "core stack"


def _estimate_impacted_files(
    source_tech: str,
    target_category: str,
    file_count: int,
    blast_count_map: dict[str, int],
) -> int:
    """Estimate impacted files using TigerGraph blast counts with safe fallback."""
    known = blast_count_map.get(source_tech.lower(), 0)
    if known > 0:
        return known

    if file_count <= 0:
        return 0

    category_ratio = {
        "language": 0.7,
        "framework": 0.45,
        "database": 0.35,
        "platform": 0.25,
        "tool": 0.2,
    }.get(target_category, 0.2)
    return max(1, int(round(file_count * category_ratio)))


def _dependencies_for_shift(source_tech: str, dependency_names: list[str]) -> list[str]:
    """Return up to 5 dependencies most related to the source technology."""
    src = source_tech.lower()
    matches = [dep for dep in dependency_names if src and src in dep.lower()]
    if matches:
        return matches[:5]
    return dependency_names[:5]


def _blast_score(top_scan: _RepoScan, shifts: list[MigrationShift]) -> tuple[int, str]:
    """Convert migration complexity into a 1-10 blast radius score + label."""
    if not shifts:
        return 1, "low"

    total_impacted = sum(shift.estimated_impacted_files for shift in shifts)
    normalized_impact = total_impacted / max(1, top_scan.file_count)
    dep_pressure = top_scan.dependency_count / 15
    shift_pressure = len(shifts) * 0.9

    raw_score = 1 + (normalized_impact * 4.5) + dep_pressure + shift_pressure
    score = max(1, min(10, int(round(raw_score))))

    if score <= 3:
        label = "low"
    elif score <= 6:
        label = "medium"
    elif score <= 8:
        label = "high"
    else:
        label = "critical"
    return score, label


def _build_justification(
    top_scan: _RepoScan,
    shifts: list[MigrationShift],
    score: int,
    label: str,
) -> str:
    """Human-readable score rationale anchored on concrete replacement shifts."""
    if not shifts:
        return (
            "No migration shifts are required because this repository already aligns "
            "with the recruiter stack."
        )

    top_shift = sorted(shifts, key=lambda item: item.estimated_impacted_files, reverse=True)[:3]
    details = ", ".join(
        f"{shift.from_tech} -> {shift.to_tech} ({shift.estimated_impacted_files} files)"
        for shift in top_shift
    )
    return (
        f"Score {score}/10 ({label}) is driven by {len(shifts)} required stack shifts "
        f"across {top_scan.file_count} files and {top_scan.dependency_count} dependencies. "
        f"Highest-impact replacements: {details}."
    )

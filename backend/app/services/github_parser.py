"""GitHub repository parser using the GitHub REST API (httpx, no SDK).

Responsibilities:
  - List a user's non-fork repos.
  - Fetch dependency manifests (Cargo.toml, package.json, requirements.txt, …).
  - Walk the file tree and parse import statements from source files.
  - Return typed LibNode / FileNode / DepEdge dataclasses ready for TigerGraph.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
import tomllib
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.services.tigergraph_client import DepEdge, FileNode, LibNode

logger = logging.getLogger(__name__)

# GitHub API base — all paths are relative to this.
_GH_BASE = "https://api.github.com"

# How many source files to fetch text for (to parse imports).
_MAX_SRC_FILES = 50
# Per-file size limit in bytes before skipping.
_MAX_FILE_BYTES = 50_000
# Maximum repos to process.
_MAX_REPOS = 20
# Concurrency limit when fetching dep files per repo.
_REPO_SEMAPHORE_LIMIT = 5

# Dependency manifest filenames we care about, in priority order.
_DEP_MANIFESTS: list[tuple[str, str]] = [
    ("Cargo.toml", "cargo"),
    ("Cargo.lock", "cargo_lock"),
    ("package.json", "npm"),
    ("requirements.txt", "pip"),
    ("pyproject.toml", "pip"),
    ("go.mod", "go"),
]

# Source file extensions and their ecosystem tag.
_SRC_EXTENSIONS: dict[str, str] = {
    ".rs": "rust",
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
}

# Per-language regex for detecting import statements.
_IMPORT_PATTERNS: dict[str, re.Pattern] = {
    "rust":       re.compile(r"^use\s+([\w]+)", re.MULTILINE),
    "python":     re.compile(r"^(?:from|import)\s+([\w]+)", re.MULTILINE),
    "typescript": re.compile(r"""from\s+['"]([^./][^'"]+)['"]"""),
    "javascript": re.compile(r"""(?:from|require\()\s+['"]([^./][^'"]+)['"]"""),
}


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(slots=True)
class RepoInfo:
    """Lightweight metadata about a GitHub repository."""

    name: str
    full_name: str
    language: str
    default_branch: str


@dataclass(slots=True)
class DepFileInfo:
    """A fetched dependency manifest file."""

    path: str
    content: str
    ecosystem: str


# ─────────────────────────────────────────────────────────────────────────────
# Parser
# ─────────────────────────────────────────────────────────────────────────────


class GitHubParser:
    """Async GitHub REST API client for dependency and source-file parsing.

    Usage (preferred — async context manager closes the HTTP client cleanly):

        async with GitHubParser(token) as parser:
            repos = await parser.get_user_repos("some-user")
            ...
    """

    def __init__(self, github_token: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=_GH_BASE,
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )

    # ── Context manager ───────────────────────────────────────────────────────

    async def __aenter__(self) -> "GitHubParser":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._client.aclose()

    # ── Public API ────────────────────────────────────────────────────────────

    async def get_user_repos(self, username: str) -> list[RepoInfo]:
        """Return up to 20 non-fork repos for ``username``, sorted by push date.

        Args:
            username: GitHub username or org name.

        Returns:
            List of RepoInfo objects, most recently pushed first.
        """
        resp = await self._get(
            f"/users/{username}/repos",
            params={"per_page": 100, "sort": "pushed"},
        )
        repos: list[RepoInfo] = []
        for r in resp:
            if r.get("fork"):
                continue
            repos.append(
                RepoInfo(
                    name=r["name"],
                    full_name=r["full_name"],
                    language=r.get("language") or "",
                    default_branch=r.get("default_branch", "main"),
                )
            )
            if len(repos) >= _MAX_REPOS:
                break
        return repos

    async def get_dep_files(
        self, full_name: str, branch: str
    ) -> list[DepFileInfo]:
        """Fetch all recognised dependency manifest files from a repo.

        Files are tried concurrently; 404s are silently skipped.

        Args:
            full_name: ``owner/repo`` string (e.g. ``"torvalds/linux"``).
            branch: Branch name (e.g. ``"main"``).

        Returns:
            List of DepFileInfo objects for every manifest that exists.
        """
        tasks = [
            self._try_fetch_manifest(full_name, filename, ecosystem)
            for filename, ecosystem in _DEP_MANIFESTS
            if ecosystem != "cargo_lock"  # skip lock files — too large
        ]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    async def parse_dependencies(
        self,
        dep_files: list[DepFileInfo],
        full_name: str,
        branch: str,
    ) -> tuple[list[LibNode], list[FileNode], list[DepEdge]]:
        """Parse manifests + source imports into graph primitives.

        Args:
            dep_files:  Manifest files fetched by ``get_dep_files``.
            full_name:  ``owner/repo`` — used as ``repo`` field on FileNodes.
            branch:     Branch to walk for source file import scanning.

        Returns:
            ``(libs, files, edges)`` deduplicated tuples.
        """
        lib_index: dict[str, LibNode] = {}
        file_index: dict[str, FileNode] = {}
        edges: list[DepEdge] = []

        # ── 1. Parse manifests ────────────────────────────────────────────────
        for dep_file in dep_files:
            manifest_node = FileNode(
                path=dep_file.path,
                repo=full_name,
                language=dep_file.ecosystem,
            )
            file_index[dep_file.path] = manifest_node

            deps = _parse_manifest(dep_file)
            for lib_name, version, is_dev in deps:
                key = f"{lib_name}@{dep_file.ecosystem}"
                if key not in lib_index:
                    lib_index[key] = LibNode(
                        name=lib_name,
                        version=version,
                        ecosystem=dep_file.ecosystem,
                    )
                edges.append(
                    DepEdge(
                        edge_type="IMPORTS",
                        src_type="FileNode",
                        src_id=dep_file.path,
                        tgt_type="LibNode",
                        tgt_id=lib_name,
                        attrs={"import_count": 1},
                    )
                )

        # ── 2. Walk source files and parse import statements ──────────────────
        src_files = await self._list_source_files(full_name, branch)
        sem = asyncio.Semaphore(_REPO_SEMAPHORE_LIMIT)

        async def fetch_src(tree_entry: dict) -> tuple[str, str, str] | None:
            path: str = tree_entry["path"]
            ext = "." + path.rsplit(".", 1)[-1] if "." in path else ""
            language = _SRC_EXTENSIONS.get(ext, "")
            if not language:
                return None
            size = tree_entry.get("size", 0)
            if size > _MAX_FILE_BYTES:
                return None
            async with sem:
                content = await self._fetch_raw(full_name, path)
            return path, content, language

        src_results = await asyncio.gather(*[fetch_src(e) for e in src_files])

        for item in src_results:
            if item is None:
                continue
            path, content, language = item
            file_node = FileNode(path=path, repo=full_name, language=language)
            file_index[path] = file_node

            # Extract import targets.
            pattern = _IMPORT_PATTERNS.get(language)
            if pattern:
                for m in pattern.finditer(content):
                    pkg = m.group(1).split("/")[0].split("::")[0]
                    if not pkg or pkg.startswith("_"):
                        continue
                    # Link to a LibNode if we know about it, else create stub.
                    lib_key = f"{pkg}@{language}"
                    if lib_key not in lib_index:
                        lib_index[lib_key] = LibNode(name=pkg, ecosystem=language)
                    edges.append(
                        DepEdge(
                            edge_type="IMPORTS",
                            src_type="FileNode",
                            src_id=path,
                            tgt_type="LibNode",
                            tgt_id=pkg,
                            attrs={"import_count": 1},
                        )
                    )

        return (
            list(lib_index.values()),
            list(file_index.values()),
            edges,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _get(self, path: str, params: dict | None = None) -> Any:
        """Issue a GET and return the parsed JSON body.

        Raises:
            httpx.HTTPStatusError: On 4xx/5xx responses.
        """
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def _try_fetch_manifest(
        self, full_name: str, filename: str, ecosystem: str
    ) -> DepFileInfo | None:
        """Try to fetch a single manifest file; return None on 404."""
        try:
            data = await self._get(f"/repos/{full_name}/contents/{filename}")
            raw = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            return DepFileInfo(path=filename, content=raw, ecosystem=ecosystem)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            logger.warning("GitHub %s for %s/%s: %s", exc.response.status_code, full_name, filename, exc)
            return None
        except Exception as exc:
            logger.warning("Error fetching %s/%s: %s", full_name, filename, exc)
            return None

    async def _list_source_files(
        self, full_name: str, branch: str
    ) -> list[dict]:
        """Return up to ``_MAX_SRC_FILES`` source file tree entries."""
        try:
            data = await self._get(
                f"/repos/{full_name}/git/trees/{branch}",
                params={"recursive": "1"},
            )
        except Exception as exc:
            logger.warning("Could not list tree for %s@%s: %s", full_name, branch, exc)
            return []

        src_exts = set(_SRC_EXTENSIONS.keys())
        files = [
            e for e in data.get("tree", [])
            if e.get("type") == "blob"
            and any(e["path"].endswith(ext) for ext in src_exts)
        ]
        return files[:_MAX_SRC_FILES]

    async def _fetch_raw(self, full_name: str, path: str) -> str:
        """Fetch raw text content of a file via the contents API."""
        try:
            data = await self._get(f"/repos/{full_name}/contents/{path}")
            if isinstance(data, dict) and data.get("encoding") == "base64":
                return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            return ""
        except Exception:
            return ""


# ─────────────────────────────────────────────────────────────────────────────
# Per-ecosystem manifest parsers
# ─────────────────────────────────────────────────────────────────────────────


def _parse_manifest(dep_file: DepFileInfo) -> list[tuple[str, str, bool]]:
    """Parse a dependency manifest and return ``(name, version, is_dev)`` tuples."""
    try:
        if dep_file.ecosystem == "cargo":
            return _parse_cargo_toml(dep_file.content)
        if dep_file.ecosystem == "npm":
            return _parse_package_json(dep_file.content)
        if dep_file.ecosystem == "pip" and dep_file.path == "requirements.txt":
            return _parse_requirements_txt(dep_file.content)
        if dep_file.ecosystem == "pip" and dep_file.path == "pyproject.toml":
            return _parse_pyproject_toml(dep_file.content)
        if dep_file.ecosystem == "go":
            return _parse_go_mod(dep_file.content)
    except Exception as exc:
        logger.warning("Failed to parse %s: %s", dep_file.path, exc)
    return []


def _parse_cargo_toml(content: str) -> list[tuple[str, str, bool]]:
    data = tomllib.loads(content)
    result: list[tuple[str, str, bool]] = []
    for name, spec in data.get("dependencies", {}).items():
        version = spec if isinstance(spec, str) else spec.get("version", "")
        result.append((name, version, False))
    for name, spec in data.get("dev-dependencies", {}).items():
        version = spec if isinstance(spec, str) else spec.get("version", "")
        result.append((name, version, True))
    return result


def _parse_package_json(content: str) -> list[tuple[str, str, bool]]:
    data = json.loads(content)
    result: list[tuple[str, str, bool]] = []
    for name, ver in data.get("dependencies", {}).items():
        result.append((name, ver, False))
    for name, ver in data.get("devDependencies", {}).items():
        result.append((name, ver, True))
    return result


def _parse_requirements_txt(content: str) -> list[tuple[str, str, bool]]:
    result: list[tuple[str, str, bool]] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Split on version specifiers: ==, >=, <=, !=, ~=, >
        name = re.split(r"[=<>!~;]", line)[0].strip()
        version_match = re.search(r"==([^\s,]+)", line)
        version = version_match.group(1) if version_match else ""
        if name:
            result.append((name, version, False))
    return result


def _parse_pyproject_toml(content: str) -> list[tuple[str, str, bool]]:
    data = tomllib.loads(content)
    result: list[tuple[str, str, bool]] = []
    deps: list[str] = (
        data.get("project", {}).get("dependencies", [])
        or data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    )
    if isinstance(deps, list):
        for dep_str in deps:
            name = re.split(r"[=<>!~;(\s]", dep_str)[0].strip()
            if name:
                result.append((name, "", False))
    elif isinstance(deps, dict):
        for name, spec in deps.items():
            if name.lower() == "python":
                continue
            version = spec if isinstance(spec, str) else spec.get("version", "")
            result.append((name, version, False))
    return result


def _parse_go_mod(content: str) -> list[tuple[str, str, bool]]:
    result: list[tuple[str, str, bool]] = []
    in_require = False
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("require ("):
            in_require = True
            continue
        if in_require and line == ")":
            in_require = False
            continue
        if in_require or line.startswith("require "):
            parts = line.lstrip("require").strip().split()
            if len(parts) >= 2:
                result.append((parts[0], parts[1], False))
    return result

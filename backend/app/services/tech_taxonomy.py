"""Canonical technology taxonomy and strict normalization helpers.

This module aggressively filters non-technical or generic terms so downstream
analysis only operates on software technologies that can be actioned.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

# Canonical format:
#   key: normalized token
#   name: display name for API responses
#   category: one of the Blast TechItem categories
#   aliases: accepted variants that normalize to this key
_TECH_CATALOG: dict[str, dict[str, object]] = {
    "python": {"name": "Python", "category": "language", "aliases": {"py"}},
    "typescript": {"name": "TypeScript", "category": "language", "aliases": {"ts"}},
    "javascript": {"name": "JavaScript", "category": "language", "aliases": {"js"}},
    "rust": {"name": "Rust", "category": "language", "aliases": set()},
    "go": {"name": "Go", "category": "language", "aliases": {"golang"}},
    "java": {"name": "Java", "category": "language", "aliases": set()},
    "kotlin": {"name": "Kotlin", "category": "language", "aliases": set()},
    "swift": {"name": "Swift", "category": "language", "aliases": set()},
    "c": {"name": "C", "category": "language", "aliases": set()},
    "c++": {"name": "C++", "category": "language", "aliases": {"cpp"}},
    "c#": {"name": "C#", "category": "language", "aliases": {"csharp"}},
    "scala": {"name": "Scala", "category": "language", "aliases": set()},
    "react": {"name": "React", "category": "framework", "aliases": {"reactjs"}},
    "next.js": {"name": "Next.js", "category": "framework", "aliases": {"nextjs"}},
    "vue": {"name": "Vue", "category": "framework", "aliases": {"vue.js", "vuejs"}},
    "angular": {"name": "Angular", "category": "framework", "aliases": set()},
    "svelte": {"name": "Svelte", "category": "framework", "aliases": set()},
    "node.js": {"name": "Node.js", "category": "platform", "aliases": {"nodejs"}},
    "express": {"name": "Express", "category": "framework", "aliases": {"expressjs"}},
    "nestjs": {"name": "NestJS", "category": "framework", "aliases": set()},
    ".net": {"name": ".NET", "category": "framework", "aliases": {"dotnet", "asp.net", "aspnet", "net framework"}},
    "fastapi": {"name": "FastAPI", "category": "framework", "aliases": set()},
    "flask": {"name": "Flask", "category": "framework", "aliases": set()},
    "django": {"name": "Django", "category": "framework", "aliases": set()},
    "spring": {"name": "Spring", "category": "framework", "aliases": {"springboot", "spring boot"}},
    "gin": {"name": "Gin", "category": "framework", "aliases": set()},
    "echo": {"name": "Echo", "category": "framework", "aliases": set()},
    "axum": {"name": "Axum", "category": "framework", "aliases": set()},
    "actix": {"name": "Actix", "category": "framework", "aliases": {"actix-web"}},
    "rocket": {"name": "Rocket", "category": "framework", "aliases": set()},
    "tokio": {"name": "Tokio", "category": "framework", "aliases": set()},
    "redis": {"name": "Redis", "category": "database", "aliases": set()},
    "postgresql": {"name": "PostgreSQL", "category": "database", "aliases": {"postgres", "psql"}},
    "mysql": {"name": "MySQL", "category": "database", "aliases": set()},
    "sqlite": {"name": "SQLite", "category": "database", "aliases": set()},
    "mongodb": {"name": "MongoDB", "category": "database", "aliases": {"mongo"}},
    "elasticsearch": {"name": "Elasticsearch", "category": "database", "aliases": {"elastic"}},
    "dynamodb": {"name": "DynamoDB", "category": "database", "aliases": set()},
    "kafka": {"name": "Kafka", "category": "tool", "aliases": set()},
    "rabbitmq": {"name": "RabbitMQ", "category": "tool", "aliases": set()},
    "docker": {"name": "Docker", "category": "platform", "aliases": set()},
    "kubernetes": {"name": "Kubernetes", "category": "platform", "aliases": {"k8s"}},
    "terraform": {"name": "Terraform", "category": "tool", "aliases": set()},
    "ansible": {"name": "Ansible", "category": "tool", "aliases": set()},
    "aws": {"name": "AWS", "category": "platform", "aliases": {"amazon web services"}},
    "gcp": {"name": "GCP", "category": "platform", "aliases": {"google cloud", "google cloud platform"}},
    "azure": {"name": "Azure", "category": "platform", "aliases": {"microsoft azure"}},
    "github actions": {"name": "GitHub Actions", "category": "tool", "aliases": {"gh actions", "githubactions"}},
    "gitlab ci": {"name": "GitLab CI", "category": "tool", "aliases": set()},
    "jenkins": {"name": "Jenkins", "category": "tool", "aliases": set()},
    "nginx": {"name": "Nginx", "category": "tool", "aliases": set()},
    "pandas": {"name": "Pandas", "category": "library", "aliases": set()},
    "numpy": {"name": "NumPy", "category": "library", "aliases": set()},
    "scikit-learn": {"name": "scikit-learn", "category": "library", "aliases": {"sklearn"}},
    "tensorflow": {"name": "TensorFlow", "category": "library", "aliases": set()},
    "pytorch": {"name": "PyTorch", "category": "library", "aliases": {"torch"}},
    "axios": {"name": "Axios", "category": "library", "aliases": set()},
    "tailwind css": {"name": "Tailwind CSS", "category": "framework", "aliases": {"tailwind"}},
    "vite": {"name": "Vite", "category": "tool", "aliases": set()},
    "webpack": {"name": "Webpack", "category": "tool", "aliases": set()},
    "pytest": {"name": "pytest", "category": "tool", "aliases": set()},
    "playwright": {"name": "Playwright", "category": "tool", "aliases": set()},
    "selenium": {"name": "Selenium", "category": "tool", "aliases": set()},
    "pydantic": {"name": "Pydantic", "category": "library", "aliases": set()},
    "sqlalchemy": {"name": "SQLAlchemy", "category": "library", "aliases": set()},
    "prisma": {"name": "Prisma", "category": "library", "aliases": set()},
    "graphql": {"name": "GraphQL", "category": "tool", "aliases": set()},
    "grpc": {"name": "gRPC", "category": "tool", "aliases": set()},
    "prometheus": {"name": "Prometheus", "category": "tool", "aliases": set()},
    "grafana": {"name": "Grafana", "category": "tool", "aliases": set()},
    "openapi": {"name": "OpenAPI", "category": "tool", "aliases": {"swagger"}},
}

# Convert internal "library" entries to API-safe category names.
_CATEGORY_MAP = {
    "library": "tool",
    "language": "language",
    "framework": "framework",
    "tool": "tool",
    "platform": "platform",
    "database": "database",
}

# Terms we should never return as technologies.
_BLOCKLIST = {
    "ai",
    "ml",
    "machine learning",
    "deep learning",
    "public health",
    "healthcare",
    "health",
    "research",
    "analysis",
    "analytics",
    "engineering",
    "developer",
    "software",
    "company",
    "startup",
    "product",
    "university",
    "paper",
    "study",
    "bmc",
}

# Some tech names are common English words; require nearby technical hints.
_AMBIGUOUS_TECH_HINTS: dict[str, set[str]] = {
    "swift": {"ios", "iphone", "ipad", "xcode", "swiftui", "apple"},
    "go": {"golang", "go.mod", "goroutine", "go build", "go test", "gin"},
    "c": {"c language", "gcc", "clang", "c11", "c99"},
}

# Build alias lookup for canonicalization.
_ALIAS_TO_CANONICAL: dict[str, str] = {}
for canonical, spec in _TECH_CATALOG.items():
    _ALIAS_TO_CANONICAL[canonical] = canonical
    for alias in spec.get("aliases", set()):
        _ALIAS_TO_CANONICAL[str(alias)] = canonical

# Compile lightweight text-detection patterns once.
_DETECTION_PATTERNS: dict[str, re.Pattern[str]] = {}
for alias in _ALIAS_TO_CANONICAL:
    escaped = re.escape(alias)
    _DETECTION_PATTERNS[alias] = re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")


def normalize_token(value: str) -> str:
    """Return lowercase cleaned token suitable for canonical lookups."""
    raw = value.strip().lower()
    if not raw:
        return ""

    # Remove obvious version suffixes: python3.11 -> python
    raw = re.sub(r"\b(v?\d+(?:\.\d+){0,2})\b", "", raw)
    raw = raw.replace("_", " ").replace("-", "-").strip()
    raw = re.sub(r"\s+", " ", raw)
    return raw


def canonicalize_tech(value: str) -> tuple[str, str] | None:
    """Map free-form text to (display_name, category) if valid, else None."""
    token = normalize_token(value)
    if not token or token in _BLOCKLIST:
        return None

    canonical = _ALIAS_TO_CANONICAL.get(token)
    if canonical is None:
        return None

    spec = _TECH_CATALOG[canonical]
    category = _CATEGORY_MAP.get(str(spec["category"]), "tool")
    return str(spec["name"]), category


def strict_dedupe_stack(items: Iterable[str]) -> list[str]:
    """Canonicalize, deduplicate, and sort technologies in display format."""
    dedup: dict[str, str] = {}
    for item in items:
        mapped = canonicalize_tech(item)
        if mapped is None:
            continue
        display, _ = mapped
        dedup[display.lower()] = display
    return sorted(dedup.values(), key=str.lower)


def detect_stack_from_text(text: str) -> list[tuple[str, str]]:
    """Deterministically detect canonical technologies directly from raw text."""
    haystack = text.lower()
    found: dict[str, tuple[str, str]] = {}
    for alias, canonical in _ALIAS_TO_CANONICAL.items():
        pattern = _DETECTION_PATTERNS[alias]
        match = pattern.search(haystack)
        if match is None:
            continue

        if canonical in _AMBIGUOUS_TECH_HINTS:
            window = haystack[max(0, match.start() - 80):match.end() + 80]
            if not any(hint in window for hint in _AMBIGUOUS_TECH_HINTS[canonical]):
                continue

        spec = _TECH_CATALOG[canonical]
        display = str(spec["name"])
        category = _CATEGORY_MAP.get(str(spec["category"]), "tool")
        found[display.lower()] = (display, category)
    return sorted(found.values(), key=lambda item: item[0].lower())


def category_of(value: str) -> str:
    """Return canonical category for a known technology or 'tool' fallback."""
    mapped = canonicalize_tech(value)
    if mapped is None:
        return "tool"
    return mapped[1]

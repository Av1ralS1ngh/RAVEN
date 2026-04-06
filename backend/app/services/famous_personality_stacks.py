"""Curated recruiter-stack seeds for known public personalities.

These are pragmatic fallback stacks when LinkedIn profile scraping is blocked.
They are intentionally broad and should be treated as inferred, not guaranteed.
"""

from __future__ import annotations

from urllib.parse import urlparse

from app.data.famous_person_graph import FAMOUS_PEOPLE
from app.services.tech_taxonomy import strict_dedupe_stack

_MIN_STACK_SIZE = 8
_DEFAULT_STACK = [
    "Python",
    "TypeScript",
    "Docker",
    "Kubernetes",
    "AWS",
    "PostgreSQL",
    "GitHub Actions",
    "OpenAPI",
]
_FILLER_STACK = [
    "Go",
    "Java",
    "GraphQL",
    "Redis",
    "Kafka",
    "Terraform",
    "GCP",
    "Azure",
]

# Keys are LinkedIn slugs from /in/<slug>/
_FAMOUS_STACKS: dict[str, list[str]] = {
    "williamhgates": [
        "C#",
        ".NET",
        "Azure",
        "C++",
        "TypeScript",
        "Python",
        "Kubernetes",
        "Docker",
        "GitHub Actions",
        "OpenAPI",
    ],
    "satyanadella": [
        "C#",
        ".NET",
        "Azure",
        "TypeScript",
        "Python",
        "Kubernetes",
        "Docker",
        "OpenAPI",
        "GitHub Actions",
    ],
    "sundarpichai": [
        "Java",
        "Python",
        "Go",
        "Kubernetes",
        "Docker",
        "GCP",
        "TensorFlow",
        "gRPC",
    ],
    "elonmusk": [
        "Python",
        "C++",
        "Rust",
        "Docker",
        "Kubernetes",
        "AWS",
        "PostgreSQL",
    ],
    "zuck": [
        "Python",
        "JavaScript",
        "React",
        "TypeScript",
        "GraphQL",
        "Kubernetes",
        "Docker",
    ],
}

# Company/domain hints used to auto-seed stacks for all curated founders.
_COMPANY_STACK_HINTS: dict[str, list[str]] = {
    "nvidia": ["C++", "Python", "Kubernetes", "Docker", "GCP", "AWS", "TensorFlow", "PyTorch", "Prometheus"],
    "stripe": ["Java", "Go", "TypeScript", "Kubernetes", "Docker", "AWS", "PostgreSQL", "Kafka", "gRPC"],
    "anthropic": ["Python", "PyTorch", "TensorFlow", "Kubernetes", "Docker", "AWS", "Redis", "PostgreSQL"],
    "openai": ["Python", "PyTorch", "Kubernetes", "Docker", "AWS", "Azure", "Redis", "PostgreSQL"],
    "perplexity": ["Python", "TypeScript", "Node.js", "React", "Docker", "Kubernetes", "AWS", "PostgreSQL"],
    "google": ["Python", "Go", "Java", "Kubernetes", "Docker", "GCP", "TensorFlow", "gRPC"],
    "alphabet": ["Python", "Go", "Java", "Kubernetes", "Docker", "GCP", "TensorFlow", "gRPC"],
    "microsoft": ["C#", ".NET", "TypeScript", "Azure", "Kubernetes", "Docker", "GitHub Actions", "OpenAPI"],
    "apple": ["Swift", "C++", "Python", "Kubernetes", "Docker", "AWS", "SQLite", "GitHub Actions"],
    "meta": ["Python", "TypeScript", "React", "GraphQL", "Kubernetes", "Docker", "PyTorch", "Redis"],
    "amazon": ["Java", "Python", "TypeScript", "AWS", "Kubernetes", "Docker", "DynamoDB", "OpenAPI"],
    "aws": ["Java", "Python", "TypeScript", "AWS", "Kubernetes", "Docker", "DynamoDB", "Terraform"],
    "airbnb": ["JavaScript", "TypeScript", "React", "GraphQL", "Node.js", "Kubernetes", "Docker", "AWS"],
    "shopify": ["TypeScript", "JavaScript", "React", "Node.js", "GraphQL", "Kubernetes", "Docker", "AWS"],
    "uber": ["Go", "Java", "Python", "Kubernetes", "Docker", "Kafka", "Redis", "PostgreSQL"],
    "dropbox": ["Python", "TypeScript", "Go", "Kubernetes", "Docker", "AWS", "MySQL", "Nginx"],
    "slack": ["TypeScript", "Node.js", "React", "Kubernetes", "Docker", "AWS", "Redis", "MySQL"],
    "twitter": ["Scala", "Java", "Python", "Kubernetes", "Docker", "Kafka", "Redis", "MySQL"],
    "spotify": ["Java", "Python", "TypeScript", "Kubernetes", "Docker", "GCP", "Kafka", "PostgreSQL"],
    "robinhood": ["Python", "Java", "TypeScript", "AWS", "Kubernetes", "Docker", "PostgreSQL", "Redis"],
    "notion": ["TypeScript", "React", "Node.js", "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS"],
    "twitch": ["Go", "Python", "TypeScript", "Kubernetes", "Docker", "AWS", "Redis", "PostgreSQL"],
    "lyft": ["Go", "Python", "Java", "Kubernetes", "Docker", "AWS", "Kafka", "Redis"],
    "salesforce": ["Java", "TypeScript", "React", "Kubernetes", "Docker", "AWS", "PostgreSQL", "OpenAPI"],
    "oracle": ["Java", "C", "C++", "Kubernetes", "Docker", "PostgreSQL", "MySQL", "OpenAPI"],
    "deepmind": ["Python", "PyTorch", "TensorFlow", "Kubernetes", "Docker", "GCP", "Redis", "PostgreSQL"],
    "databricks": ["Scala", "Python", "Java", "Kafka", "Kubernetes", "Docker", "AWS", "GCP"],
    "coinbase": ["Go", "Rust", "Python", "TypeScript", "AWS", "Kubernetes", "Docker", "PostgreSQL"],
    "canva": ["TypeScript", "React", "Node.js", "Go", "AWS", "Kubernetes", "Docker", "PostgreSQL"],
    "doordash": ["Java", "Kotlin", "TypeScript", "Go", "Kubernetes", "Docker", "AWS", "PostgreSQL"],
    "instacart": ["Python", "TypeScript", "React", "Node.js", "AWS", "Kubernetes", "Docker", "PostgreSQL"],
    "discord": ["TypeScript", "React", "Go", "Rust", "Kubernetes", "Docker", "AWS", "PostgreSQL"],
    "pinterest": ["Python", "Java", "TypeScript", "React", "Kubernetes", "Docker", "AWS", "Redis"],
    "whatsapp": ["Go", "C++", "Java", "Kubernetes", "Docker", "AWS", "MySQL", "Redis"],
    "quora": ["Python", "TypeScript", "React", "MySQL", "Redis", "Kubernetes", "Docker", "AWS"],
    "scale": ["Python", "TypeScript", "Node.js", "Kubernetes", "Docker", "AWS", "PostgreSQL", "OpenAPI"],
    "infosys": ["Java", "Python", "TypeScript", "AWS", "Azure", "Kubernetes", "Docker", "OpenAPI"],
    "razorpay": ["Java", "Python", "Go", "AWS", "Kubernetes", "Docker", "PostgreSQL", "Redis"],
    "default": _DEFAULT_STACK,
}

_PERSON_OVERRIDES: dict[str, list[str]] = {
    "jenhsunhuang": ["C++", "Python", "Kubernetes", "Docker", "GCP", "AWS", "PyTorch", "TensorFlow"],
    "patrickcollison": ["TypeScript", "Java", "Go", "PostgreSQL", "Kafka", "Kubernetes", "Docker", "AWS"],
    "johnbcollison": ["TypeScript", "Java", "Go", "PostgreSQL", "Kafka", "Kubernetes", "Docker", "AWS"],
    "dario-amodei-3934934": ["Python", "PyTorch", "TensorFlow", "Kubernetes", "Docker", "AWS", "Redis", "PostgreSQL"],
    "daniela-amodei-790bb22a": ["Python", "PyTorch", "TensorFlow", "Kubernetes", "Docker", "AWS", "Redis", "PostgreSQL"],
    "reidhoffman": ["TypeScript", "Python", "C#", "Azure", "Kubernetes", "Docker", "PostgreSQL", "GraphQL"],
    "brianchesky": ["TypeScript", "React", "Node.js", "Kubernetes", "Docker", "AWS", "GraphQL", "PostgreSQL"],
    "tobiaslutke": ["TypeScript", "React", "Node.js", "GraphQL", "Kubernetes", "Docker", "AWS", "PostgreSQL"],
    "aravind-srinivas-16051987": ["Python", "TypeScript", "Node.js", "React", "Kubernetes", "Docker", "AWS", "PostgreSQL"],
    "dylanfield": ["TypeScript", "React", "Node.js", "GraphQL", "Kubernetes", "Docker", "AWS", "PostgreSQL"],
}


def linkedin_slug_from_url(url: str) -> str:
    """Extract the LinkedIn profile slug from a URL, or empty string."""
    try:
        parsed = urlparse(url)
    except Exception:
        return ""

    path = parsed.path.strip("/")
    if not path:
        return ""

    parts = path.split("/")
    if len(parts) >= 2 and parts[0].lower() == "in":
        return parts[1].strip().lower()
    return ""


def _stack_for_company(company: str) -> list[str]:
    lowered = (company or "").strip().lower()
    for token, stack in _COMPANY_STACK_HINTS.items():
        if token == "default":
            continue
        if token in lowered:
            return list(stack)
    return list(_COMPANY_STACK_HINTS["default"])


def _ensure_minimum_stack(stack: list[str]) -> list[str]:
    """Canonicalize and guarantee at least _MIN_STACK_SIZE stack entries."""
    merged = strict_dedupe_stack(stack)
    if len(merged) < _MIN_STACK_SIZE:
        for tech in strict_dedupe_stack([*_DEFAULT_STACK, *_FILLER_STACK]):
            if tech in merged:
                continue
            merged.append(tech)
            if len(merged) >= _MIN_STACK_SIZE:
                break

    # Keep founder stacks concise and readable in UI.
    return merged[:_MIN_STACK_SIZE]


def _build_generated_founder_stacks() -> dict[str, list[str]]:
    """Generate stack seeds for all famous founders from profile + company hints."""
    generated: dict[str, list[str]] = {}
    for person in FAMOUS_PEOPLE:
        slug = linkedin_slug_from_url(person.linkedin_url)
        if not slug:
            continue

        stack: list[str] = []
        person_specific = _PERSON_OVERRIDES.get(slug, [])
        if person_specific:
            # For known profiles, trust curated person-specific stack first.
            stack.extend(person_specific)
        else:
            stack.extend(_stack_for_company(person.company))

        headline = f"{person.headline} {person.company}".lower()
        if any(token in headline for token in {"ai", "anthropic", "openai", "deepmind", "perplexity", "scale"}):
            stack.extend(["Python", "PyTorch", "TensorFlow", "Kubernetes"])
        if any(token in headline for token in {"cloud", "aws", "azure", "gcp"}):
            stack.extend(["AWS", "Azure", "GCP", "Terraform"])
        if any(token in headline for token in {"fintech", "payments", "stripe", "coinbase", "robinhood", "klarna", "revolut", "wise"}):
            stack.extend(["PostgreSQL", "Kafka", "Redis", "OpenAPI"])

        generated[slug] = _ensure_minimum_stack(stack)

    return generated


_GENERATED_FOUNDER_STACKS: dict[str, list[str]] = _build_generated_founder_stacks()


def get_seeded_stack_for_linkedin_url(url: str) -> list[str]:
    """Return curated stack list for a known LinkedIn URL slug, else empty."""
    slug = linkedin_slug_from_url(url)
    if not slug:
        return []

    if slug in _FAMOUS_STACKS:
        return _ensure_minimum_stack(list(_FAMOUS_STACKS[slug]))

    generated = _GENERATED_FOUNDER_STACKS.get(slug)
    if generated:
        return _ensure_minimum_stack(list(generated))

    return []


def all_seeded_profiles() -> dict[str, list[str]]:
    """Expose all seed data for one-time TigerGraph seeding scripts."""
    merged: dict[str, list[str]] = {
        slug: _ensure_minimum_stack(list(stack))
        for slug, stack in _GENERATED_FOUNDER_STACKS.items()
    }
    for slug, stack in _FAMOUS_STACKS.items():
        merged[slug] = _ensure_minimum_stack(list(stack))
    return merged

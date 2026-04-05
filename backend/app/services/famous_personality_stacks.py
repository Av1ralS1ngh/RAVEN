"""Curated recruiter-stack seeds for known public personalities.

These are pragmatic fallback stacks when LinkedIn profile scraping is blocked.
They are intentionally broad and should be treated as inferred, not guaranteed.
"""

from __future__ import annotations

from urllib.parse import urlparse

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


def get_seeded_stack_for_linkedin_url(url: str) -> list[str]:
    """Return curated stack list for a known LinkedIn URL slug, else empty."""
    slug = linkedin_slug_from_url(url)
    return list(_FAMOUS_STACKS.get(slug, []))


def all_seeded_profiles() -> dict[str, list[str]]:
    """Expose all seed data for one-time TigerGraph seeding scripts."""
    return {slug: list(stack) for slug, stack in _FAMOUS_STACKS.items()}

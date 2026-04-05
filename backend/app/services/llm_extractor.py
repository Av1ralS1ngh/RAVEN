"""LLM-based tech stack extraction using Groq (llama-3.3-70b-versatile).

Uses the groq Python SDK with async support. Accepts either a plain text
string (LinkedIn profile text) or a dict[filepath→content] for repo-based
extraction.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from groq import AsyncGroq

from app.services.tech_taxonomy import canonicalize_tech, detect_stack_from_text

logger = logging.getLogger(__name__)

_MODEL = "llama-3.3-70b-versatile"
_MAX_TOKENS = 800

_SYSTEM_PROMPT = (
    "You are a strict software stack extraction engine. Extract ONLY concrete "
    "software technologies explicitly mentioned in the text. Allowed items are "
    "programming languages, frameworks, libraries, cloud platforms, databases, "
    "dev tools, and runtimes. Return ONLY a JSON array, no other text, "
    "in this exact format:\n"
    '[{"name": "Rust", "confidence": 0.95, "category": "language"}, ...]\n'
    "Valid categories: language, framework, tool, platform, database.\n"
    "Hard exclusions: industry/domain words, company names, paper titles, "
    "role labels, and generic buzzwords (e.g., AI, ML, analytics, public "
    "health, startup).\n"
    "Never infer domain concepts as technologies.\n"
    "Confidence reflects explicitness (0.0–1.0). Only include confidence >= 0.7."
)

_INFER_FROM_URL_PROMPT = (
    "You are a technical recruiter analyst. The LinkedIn page content is unavailable, "
    "but the profile URL belongs to a known public personality. Infer a probable software "
    "technology stack from widely known engineering context only. Return ONLY a JSON array, "
    "no other text, in this exact format:\n"
    '[{"name": "C#", "confidence": 0.62, "category": "language"}, ...]\n'
    "Valid categories: language, framework, tool, platform, database.\n"
    "Constraints: do not include generic words, domains, companies, or titles. "
    "Keep confidence conservative (0.35–0.8)."
)

_VALID_CATEGORIES = {"language", "framework", "tool", "platform", "database"}


# ─────────────────────────────────────────────────────────────────────────────
# Domain model
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(slots=True)
class TechItem:
    """A single technology detected in a profile or file set."""

    name: str
    confidence: float   # 0.0–1.0
    category: str       # language | framework | tool | platform | database


# ─────────────────────────────────────────────────────────────────────────────
# Extractor
# ─────────────────────────────────────────────────────────────────────────────


class LLMExtractor:
    """Uses Groq (llama-3.3-70b-versatile) to identify technologies from text.

    Args:
        api_key: Groq API key injected via Settings.GROQ_API_KEY.
    """

    def __init__(self, api_key: str) -> None:
        self._client = AsyncGroq(api_key=api_key)

    async def extract_tech_stack(
        self,
        profile_text: str | dict[str, str],
    ) -> list[TechItem]:
        """Send text to Groq and return a parsed list of TechItem objects.

        If ``profile_text`` is a dict, file contents are concatenated (up to
        8 000 chars total) before being sent to the model.

        Returns:
            List of TechItem objects with confidence >= 0.5, or [] on failure.
            Never raises — errors are logged and an empty list is returned.
        """
        if isinstance(profile_text, dict):
            combined_full = "\n\n".join(
                f"# {path}\n{content}"
                for path, content in profile_text.items()
            )
        else:
            combined_full = str(profile_text)

        text_input = _build_model_input(combined_full)

        if not text_input.strip():
            return []

        try:
            completion = await self._client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": f"Text:\n{text_input}"},
                ],
                max_tokens=_MAX_TOKENS,
                temperature=0.2,
            )
            raw_text: str = completion.choices[0].message.content or ""
        except Exception as exc:
            logger.error("Groq API call failed: %s", exc)
            return []

        return _parse_response(raw_text, source_text=combined_full[:50_000])

    async def infer_tech_stack_from_profile_url(
        self,
        profile_url: str,
    ) -> list[TechItem]:
        """Infer a probable stack from profile URL when scraping content is blocked."""
        hint = str(profile_url).strip()
        if not hint:
            return []

        try:
            completion = await self._client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {"role": "system", "content": _INFER_FROM_URL_PROMPT},
                    {"role": "user", "content": f"LinkedIn URL: {hint}"},
                ],
                max_tokens=500,
                temperature=0.15,
            )
            raw_text: str = completion.choices[0].message.content or ""
        except Exception as exc:
            logger.error("Groq fallback infer call failed: %s", exc)
            return []

        return _parse_response(
            raw_text,
            source_text="",
            min_confidence=0.35,
            include_deterministic_fallback=False,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Parsing helper
# ─────────────────────────────────────────────────────────────────────────────


def _parse_response(
    raw: str,
    source_text: str = "",
    min_confidence: float = 0.7,
    include_deterministic_fallback: bool = True,
) -> list[TechItem]:
    """Parse the raw model output into TechItem objects.

    Strips optional ```json … ``` markdown fences before JSON decode.
    Logs and returns [] on any parse error — never raises.
    """
    cleaned = raw.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        inner = lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:]
        cleaned = "\n".join(inner).strip()

    try:
        items: list[dict] = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning(
            "LLMExtractor: failed to parse Groq JSON response. Raw: %r",
            raw[:400],
        )
        if not include_deterministic_fallback:
            return []
        return [
            TechItem(name=name, confidence=0.76, category=category)
            for name, category in detect_stack_from_text(source_text)
        ]

    dedup: dict[str, TechItem] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        try:
            confidence = float(item.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0

        if not name or confidence < min_confidence:
            continue

        canonical = canonicalize_tech(name)
        if canonical is None:
            continue

        display_name, canonical_category = canonical
        if canonical_category not in _VALID_CATEGORIES:
            canonical_category = "tool"

        key = display_name.lower()
        previous = dedup.get(key)
        item_obj = TechItem(
            name=display_name,
            confidence=min(confidence, 0.99),
            category=canonical_category,
        )
        if previous is None or item_obj.confidence > previous.confidence:
            dedup[key] = item_obj

    # Deterministic safety net: include explicit canonical tech names found in text.
    if include_deterministic_fallback:
        for display_name, category in detect_stack_from_text(source_text):
            key = display_name.lower()
            if key in dedup:
                continue
            dedup[key] = TechItem(name=display_name, confidence=0.76, category=category)

    return sorted(dedup.values(), key=lambda item: item.confidence, reverse=True)


def _build_model_input(text: str) -> str:
    """Build a balanced prompt slice so we don't overfit to the first page chunk."""
    normalized = text.strip()
    if not normalized:
        return ""

    max_chars = 14_000
    if len(normalized) <= max_chars:
        return normalized

    # Sample beginning/middle/end to improve recall when relevant details are lower.
    segment = max_chars // 3
    head = normalized[:segment]
    mid_start = max(0, (len(normalized) // 2) - (segment // 2))
    mid = normalized[mid_start:mid_start + segment]
    tail = normalized[-segment:]
    return "\n\n".join([head, mid, tail])

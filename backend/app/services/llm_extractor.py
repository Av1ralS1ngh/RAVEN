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

logger = logging.getLogger(__name__)

_MODEL = "llama-3.3-70b-versatile"
_MAX_TOKENS = 800

_SYSTEM_PROMPT = (
    "You are a technical recruiter analyst. Extract all technical tools, "
    "programming languages, frameworks, platforms, and databases mentioned or "
    "implied in the provided text. Return ONLY a JSON array, no other text, "
    "in this exact format:\n"
    '[{"name": "Rust", "confidence": 0.95, "category": "language"}, ...]\n'
    "Valid categories: language, framework, tool, platform, database.\n"
    "Confidence reflects how explicitly mentioned vs inferred (0.0–1.0). "
    "Only include items with confidence >= 0.5."
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
            combined = "\n\n".join(
                f"# {path}\n{content}"
                for path, content in profile_text.items()
            )
            text_input = combined[:8_000]
        else:
            text_input = str(profile_text)[:8_000]

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

        return _parse_response(raw_text)


# ─────────────────────────────────────────────────────────────────────────────
# Parsing helper
# ─────────────────────────────────────────────────────────────────────────────


def _parse_response(raw: str) -> list[TechItem]:
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
        return []

    result: list[TechItem] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        category = str(item.get("category", "tool")).strip().lower()
        try:
            confidence = float(item.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0

        if not name or confidence < 0.5:
            continue
        if category not in _VALID_CATEGORIES:
            category = "tool"

        result.append(TechItem(name=name, confidence=confidence, category=category))

    return result

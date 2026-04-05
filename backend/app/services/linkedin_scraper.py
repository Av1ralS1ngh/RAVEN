"""LinkedIn profile scraper using the linkedin-api package.

Provides async methods to fetch person profiles and connection graphs,
mapping raw API responses into the typed PersonNode / ConnectionEdge
dataclasses defined in tigergraph_client.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from linkedin_api import Linkedin
from linkedin_api.client import Client as _LIClient

# Reuse the shared domain dataclasses — no coupling to Pydantic here.
from app.services.tigergraph_client import ConnectionEdge, PersonNode

logger = logging.getLogger(__name__)

# Requests per second cap: sleep between 2nd-degree fetches to avoid 429s.
_BETWEEN_REQUEST_SLEEP = 0.5  # seconds
_MAX_2ND_DEGREE_PER_PERSON = 100
# If rate-limited: sleep this long before one retry.
_RATE_LIMIT_BACKOFF = 30  # seconds

# Regex to extract the public identifier from any LinkedIn /in/ URL.
_LI_URL_RE = re.compile(
    r"linkedin\.com/in/([A-Za-z0-9\-_%]+?)(?:[/?#]|$)"
)


# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────


class LinkedInAuthError(Exception):
    """Raised when LinkedIn rejects credentials or the session expires."""


class LinkedInRateLimitError(Exception):
    """Raised after exhausting the 429 retry budget."""


# ─────────────────────────────────────────────────────────────────────────────
# Scraper
# ─────────────────────────────────────────────────────────────────────────────


class LinkedInScraper:
    """Async wrapper around the ``linkedin-api`` package.

    Authentication happens eagerly in ``__init__`` so that downstream callers
    get an immediate ``LinkedInAuthError`` instead of a confusing failure deep
    inside a request chain.

    Args:
        username: LinkedIn email address.
        password: LinkedIn account password.
    """

    def __init__(self, username: str, password: str) -> None:
        try:
            self._api = Linkedin(username, password)
        except Exception as exc:
            # linkedin_api raises its own exceptions on bad credentials;
            # wrap them so callers only need to know about ours.
            raise LinkedInAuthError(
                f"LinkedIn authentication failed for {username!r}: {exc}"
            ) from exc

    # ── Public interface ─────────────────────────────────────────────────────

    async def get_profile(self, linkedin_url: str) -> PersonNode:
        """Fetch a single LinkedIn profile by URL and return a PersonNode.

        Args:
            linkedin_url: Full LinkedIn profile URL (e.g.
                ``https://linkedin.com/in/some-person``).

        Raises:
            ValueError: If the URL doesn't contain a parseable identifier.
            LinkedInAuthError: If the session is no longer valid.
            LinkedInRateLimitError: If rate-limited after one retry.
        """
        identifier = _extract_public_id(linkedin_url)
        raw = await self._fetch_with_retry(
            self._api.get_profile, public_id=identifier
        )
        return _map_profile_to_node(raw)

    async def get_connections(
        self,
        profile_id: str,
        depth: int = 2,
    ) -> tuple[list[PersonNode], list[ConnectionEdge]]:
        """Crawl the connection graph up to ``depth`` hops from ``profile_id``.

        - Depth 1: direct connections of ``profile_id``.
        - Depth 2: for each 1st-degree connection, also fetch their
          connections (capped at ``_MAX_2ND_DEGREE_PER_PERSON`` to respect
          rate limits). A 0.5 s sleep is inserted between each outer request.

        Deduplication is performed by LinkedIn URN before returning, so the
        same person only appears once even if reachable via multiple paths.

        Args:
            profile_id: The LinkedIn public identifier (not a URL).
            depth: How many hops to expand. Only 1 and 2 are supported;
                higher values are clamped to 2.

        Returns:
            ``(persons, edges)`` where:
            - ``persons`` is a flat, deduplicated list of PersonNode objects.
            - ``edges`` is a list of ConnectionEdge objects encoding who
              is connected to whom.

        Raises:
            LinkedInAuthError: On session expiry.
            LinkedInRateLimitError: On repeated 429s.
        """
        seen_ids: set[str] = set()
        persons: list[PersonNode] = []
        edges: list[ConnectionEdge] = []

        # ── Depth 1: direct connections ──────────────────────────────────────
        raw_1st = await self._fetch_with_retry(
            self._api.get_profile_connections, public_id=profile_id
        )
        first_degree: list[PersonNode] = []

        for raw in raw_1st:
            node = _map_connection_to_node(raw)
            if node.id in seen_ids:
                continue
            seen_ids.add(node.id)
            persons.append(node)
            first_degree.append(node)
            mutual = _get_mutual_count(raw)
            edges.append(
                ConnectionEdge(
                    src_id=profile_id,
                    tgt_id=node.id,
                    mutual_count=mutual,
                    strength=_mutual_to_strength(mutual),
                )
            )

        if depth < 2:
            return persons, edges

        # ── Depth 2: connections-of-connections ──────────────────────────────
        for first_deg_node in first_degree:
            await asyncio.sleep(_BETWEEN_REQUEST_SLEEP)

            try:
                raw_2nd = await self._fetch_with_retry(
                    self._api.get_profile_connections,
                    public_id=first_deg_node.id,
                )
            except (LinkedInAuthError, LinkedInRateLimitError):
                raise
            except Exception as exc:
                # Per-person 2nd-degree failures are logged but non-fatal.
                logger.warning(
                    "Skipped 2nd-degree connections for %s: %s",
                    first_deg_node.id,
                    exc,
                )
                continue

            for raw in raw_2nd[:_MAX_2ND_DEGREE_PER_PERSON]:
                node = _map_connection_to_node(raw)
                if node.id in seen_ids:
                    continue
                seen_ids.add(node.id)
                persons.append(node)
                mutual = _get_mutual_count(raw)
                edges.append(
                    ConnectionEdge(
                        src_id=first_deg_node.id,
                        tgt_id=node.id,
                        mutual_count=mutual,
                        strength=_mutual_to_strength(mutual),
                    )
                )

        return persons, edges

    # ── Private helpers ──────────────────────────────────────────────────────

    async def _fetch_with_retry(self, fn, **kwargs) -> Any:
        """Call a linkedin-api function, retrying once on HTTP 429.

        linkedin-api is synchronous, so we run it in a thread pool to avoid
        blocking the event loop.

        Raises:
            LinkedInAuthError: On 4xx auth failure.
            LinkedInRateLimitError: If 429 persists after one retry.
        """
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, lambda: fn(**kwargs))
        except Exception as exc:
            exc_str = str(exc).lower()

            if "unauthorized" in exc_str or "403" in exc_str or "401" in exc_str:
                raise LinkedInAuthError(f"Session expired or invalid: {exc}") from exc

            if "429" in exc_str or "too many requests" in exc_str:
                logger.warning("Rate limited by LinkedIn — backing off %ds…", _RATE_LIMIT_BACKOFF)
                await asyncio.sleep(_RATE_LIMIT_BACKOFF)
                try:
                    return await loop.run_in_executor(None, lambda: fn(**kwargs))
                except Exception as retry_exc:
                    if "429" in str(retry_exc).lower():
                        raise LinkedInRateLimitError(
                            "LinkedIn rate limit persists after backoff"
                        ) from retry_exc
                    raise

            raise


# ─────────────────────────────────────────────────────────────────────────────
# Mapping helpers
# ─────────────────────────────────────────────────────────────────────────────


def _extract_public_id(url: str) -> str:
    """Extract the LinkedIn public identifier from a profile URL.

    Handles all common variants:
      - https://www.linkedin.com/in/john-doe
      - https://linkedin.com/in/john-doe/
      - https://linkedin.com/in/john-doe?miniProfile=…

    Raises:
        ValueError: If no identifier can be parsed.
    """
    m = _LI_URL_RE.search(url)
    if not m:
        raise ValueError(
            f"Cannot extract LinkedIn public ID from URL: {url!r}. "
            "Expected format: https://linkedin.com/in/<identifier>"
        )
    return m.group(1)


def _map_profile_to_node(raw: dict) -> PersonNode:
    """Map a linkedin-api get_profile() response to a PersonNode."""
    first = raw.get("firstName", "")
    last = raw.get("lastName", "")
    pub_id = raw.get("public_id") or raw.get("publicIdentifier", "")

    # URN is the stable graph primary key.
    urn: str = raw.get("profile_id") or raw.get("entityUrn", pub_id)
    # Strip the 'urn:li:fs_profile:' prefix if present.
    urn = re.sub(r"^urn:li:[^:]+:", "", urn)

    # Best-effort company from the first position.
    positions = (
        raw.get("experience", [{}])
        or raw.get("position", [{}])
    )
    company = ""
    if positions:
        company = positions[0].get("companyName", "")

    return PersonNode(
        id=urn or pub_id,
        name=f"{first} {last}".strip(),
        headline=raw.get("headline", ""),
        company=company,
        linkedin_url=f"https://linkedin.com/in/{pub_id}" if pub_id else "",
        profile_image_url=_get_profile_image(raw),
    )


def _map_connection_to_node(raw: dict) -> PersonNode:
    """Map a single entry from get_profile_connections() to a PersonNode."""
    first = raw.get("firstName", "")
    last = raw.get("lastName", "")
    pub_id = (
        raw.get("publicIdentifier")
        or raw.get("public_id")
        or raw.get("miniProfile", {}).get("publicIdentifier", "")
    )
    urn = (
        raw.get("entityUrn")
        or raw.get("profile_id")
        or raw.get("miniProfile", {}).get("entityUrn", pub_id)
    )
    urn = re.sub(r"^urn:li:[^:]+:", "", urn or "")

    # Connections list entries nest inside a ``miniProfile`` key.
    mini = raw.get("miniProfile", {})
    if not first:
        first = mini.get("firstName", "")
    if not last:
        last = mini.get("lastName", "")
    if not pub_id:
        pub_id = mini.get("publicIdentifier", "")

    return PersonNode(
        id=urn or pub_id,
        name=f"{first} {last}".strip(),
        headline=raw.get("headline", mini.get("occupation", "")),
        company=raw.get("companyName", ""),
        linkedin_url=f"https://linkedin.com/in/{pub_id}" if pub_id else "",
        profile_image_url=_get_profile_image(raw) or _get_profile_image(mini),
    )


def _get_mutual_count(raw: dict) -> int:
    """Extract numSharedConnections from a connection entry, defaulting to 0."""
    return int(raw.get("numSharedConnections", 0))


def _mutual_to_strength(mutual: int) -> float:
    """Convert a mutual-connection count to a 0–1 edge strength score.

    Uses a simple logarithmic normalisation capped at 500 mutual connections
    as a rough upper bound.
    """
    import math
    if mutual <= 0:
        return 0.1
    return min(1.0, math.log10(mutual + 1) / math.log10(501))


def _get_profile_image(raw: dict) -> str:
    """Best-effort extraction of a profile image URL from any raw dict."""
    # linkedin-api nests images under several different key paths.
    for key in ("profilePicture", "picture", "img"):
        value = raw.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value
        if isinstance(value, dict):
            # Try to pull the largest artifact.
            artifacts = (
                value.get("displayImage~", {})
                .get("elements", [{}])
            )
            if artifacts:
                return artifacts[-1].get("identifiers", [{}])[0].get("identifier", "")
    return ""

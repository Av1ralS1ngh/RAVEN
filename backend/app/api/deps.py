"""FastAPI dependency injection for shared application resources.

Provides typed ``Depends``-compatible functions for:
  - Settings singleton
  - TigerGraphClient pulled from ``app.state`` (set during lifespan startup)
"""

from __future__ import annotations

from typing import Annotated, TYPE_CHECKING

from fastapi import Depends, Request

from app.config import Settings, get_settings

if TYPE_CHECKING:
    from app.services.tigergraph_client import TigerGraphClient

# Shorthand for annotated Settings dependency.
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_tg_client(request: Request) -> "TigerGraphClient":
    """Return the TigerGraphClient singleton stored on ``app.state``.

    The client is created once during the FastAPI lifespan startup event
    (see ``main.py``). Storing it on ``app.state`` is the idiomatic FastAPI
    pattern for request-scoped access to a shared long-lived resource without
    requiring ``lru_cache`` tricks in ``Depends``.

    Raises:
        RuntimeError: If called before the lifespan startup has run (e.g. in
            tests that don't use the full app).
    """
    client = getattr(request.app.state, "tg_client", None)
    if client is None:
        raise RuntimeError(
            "TigerGraphClient has not been initialised. "
            "Ensure the FastAPI lifespan context manager has run."
        )
    return client


# Annotated shorthand for route signatures.
TGClientDep = Annotated["TigerGraphClient", Depends(get_tg_client)]

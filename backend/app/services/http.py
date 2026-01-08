from __future__ import annotations

import httpx

from app.config.settings import Settings


def build_async_http_client(settings: Settings) -> httpx.AsyncClient:
    timeout = httpx.Timeout(settings.http_timeout_s)
    return httpx.AsyncClient(timeout=timeout)

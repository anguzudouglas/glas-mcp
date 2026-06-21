"""
web_fetch/helpers/redirect_handler.py

Follows all redirect types without relying on requests' built-in redirect
handling, so we can track the full chain and update Referer on every hop.

Handled:
  - HTTP 301 / 302 / 303 / 307 / 308
  - HTML <meta http-equiv="refresh" content="N; url=…">
  - JavaScript window.location / location.replace(…) patterns
  - Circular-redirect detection via visited-URL set
"""
from __future__ import annotations

import re
import time
from urllib.parse import urljoin
from typing import Tuple, List

import requests

MAX_REDIRECTS = 15
HTTP_REDIRECT_CODES = {301, 302, 303, 307, 308}

_META_REFRESH = re.compile(
    r'<meta[^>]+http-equiv=["\']?refresh["\']?[^>]*content=["\']?\d+;\s*url=([^"\'>\s]+)',
    re.IGNORECASE,
)
_JS_LOCATION = re.compile(
    r'(?:window\.location(?:\.href)?\s*=|location\.replace\()\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)


class RedirectError(Exception):
    def __init__(self, message: str, chain: List[str]):
        super().__init__(message)
        self.chain = chain


class TooManyRedirectsError(RedirectError):
    pass


def follow(
    url: str,
    session: requests.Session,
    timeout: int = 30,
    *,
    max_hops: int = MAX_REDIRECTS,
    delay_between_hops: float = 0.1,
) -> Tuple[requests.Response, str, List[str]]:
    """
    Follow all redirect types manually.
    Returns (final_response, final_url, redirect_chain).
    Maintains cookies and Referer header across hops.
    """
    visited: set = set()
    chain: List[str] = [url]
    current = url

    for _ in range(max_hops):
        if current in visited:
            raise TooManyRedirectsError(
                f"Circular redirect at: {current}", chain
            )
        visited.add(current)

        try:
            resp = session.get(current, timeout=timeout, allow_redirects=False)
        except requests.exceptions.RequestException as exc:
            raise RedirectError(str(exc), chain) from exc

        # HTTP redirect
        if resp.status_code in HTTP_REDIRECT_CODES:
            location = resp.headers.get("Location", "").strip()
            if not location:
                return resp, current, chain
            next_url = _resolve(current, location)
            session.headers["Referer"] = current
            chain.append(next_url)
            current = next_url
            if delay_between_hops:
                time.sleep(delay_between_hops)
            continue

        # Soft redirects inside HTML body
        if resp.status_code == 200:
            ct = resp.headers.get("Content-Type", "").lower()
            if "html" in ct:
                body = resp.text[:8000]

                m = _META_REFRESH.search(body)
                if m:
                    next_url = _resolve(current, m.group(1).strip().strip("'\""))
                    if next_url not in visited:
                        session.headers["Referer"] = current
                        chain.append(next_url)
                        current = next_url
                        continue

                m = _JS_LOCATION.search(body)
                if m:
                    next_url = _resolve(current, m.group(1).strip())
                    if next_url not in visited:
                        session.headers["Referer"] = current
                        chain.append(next_url)
                        current = next_url
                        continue

        return resp, current, chain

    raise TooManyRedirectsError(
        f"Exceeded {max_hops} redirects. Chain: {chain}", chain
    )


def _resolve(base: str, location: str) -> str:
    if location.startswith(("http://", "https://")):
        return location
    return urljoin(base, location)

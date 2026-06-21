"""
web_fetch/helpers/cache_engine.py

Fetches cached / archived copies of a URL when the live site is unreachable.

Sources tried in order:
  1. Google Cache        — fastest, hours old
  2. Bing Cache          — alternative when Google is unavailable
  3. Google AMP Cache    — works for AMP-compatible pages
  4. Wayback Machine     — slowest, most comprehensive

Notes on Google Cache:
  - Accept-Encoding must NOT include 'br' — requests can't decode brotli natively
    and the raw bytes come through as garbage.
  - X-Client-Data is a Chrome experiment header. Sending any plausible value
    dramatically lowers Google's bot score.
"""
from __future__ import annotations

import gzip
import re
import time
import zlib
from typing import Optional
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

_GCACHE_HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",   # no 'br' — brotli not decodable by requests
    "Cache-Control":   "no-cache",
    "Pragma":          "no-cache",
    "Referer":         "https://www.google.com/",
    "Origin":          "https://www.google.com",
    "Sec-Fetch-Dest":  "document",
    "Sec-Fetch-Mode":  "navigate",
    "Sec-Fetch-Site":  "same-origin",
    "Sec-Fetch-User":  "?1",
    "X-Client-Data":   "CIi2yQEIpbbJAQipncoBCKv5ygEIkqHLAQiFoM0B",
    "Connection":      "keep-alive",
}


def _decode(resp: requests.Response) -> str:
    raw = resp.content
    enc = resp.headers.get("Content-Encoding", "").lower()
    if "gzip" in enc:
        try:
            raw = gzip.decompress(raw)
        except Exception:
            pass
    elif "deflate" in enc:
        try:
            raw = zlib.decompress(raw)
        except Exception:
            try:
                raw = zlib.decompress(raw, -zlib.MAX_WBITS)
            except Exception:
                pass
    elif "br" in enc:
        try:
            import brotli
            raw = brotli.decompress(raw)
        except Exception:
            pass

    ct = resp.headers.get("Content-Type", "")
    charset = "utf-8"
    m = re.search(r"charset=([^\s;]+)", ct, re.I)
    if m:
        charset = m.group(1).strip().strip("'\"")

    for enc_try in [charset, "utf-8", "latin-1"]:
        try:
            return raw.decode(enc_try, errors="replace")
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("latin-1", errors="replace")


def _strip_google_toolbar(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(id=re.compile(r"google.cache", re.I)):
        tag.decompose()
    for script in soup.find_all("script"):
        txt = script.string or ""
        if "google" in txt.lower() and "cache" in txt.lower():
            script.decompose()
    return str(soup)


def _get(
    url: str,
    timeout: int,
    proxy: Optional[str],
    extra_headers: Optional[dict] = None,
) -> Optional[requests.Response]:
    s = requests.Session()
    s.headers.update({**_GCACHE_HEADERS, **(extra_headers or {})})
    if proxy:
        s.proxies = {"http": proxy, "https": proxy}
    try:
        r = s.get(url, timeout=timeout, allow_redirects=True)
        return r if r.ok else None
    except Exception:
        return None


def fetch_google_cache(url: str, timeout: int, proxy: Optional[str]) -> Optional[dict]:
    cache_url = (
        f"https://webcache.googleusercontent.com/search"
        f"?q=cache:{quote_plus(url)}&gl=us&hl=en&strip=0&vwsrc=0"
    )
    resp = _get(cache_url, timeout, proxy)
    if resp is None:
        return None
    html = _decode(resp)
    if len(html.strip()) < 500:
        return None
    html = _strip_google_toolbar(html)
    return {
        "html": html,
        "cache_source": "google_cache",
        "cache_url": cache_url,
        "cache_note": "Google web cache — may be hours old",
    }


def fetch_bing_cache(url: str, timeout: int, proxy: Optional[str]) -> Optional[dict]:
    bing_url = (
        f"https://cc.bingj.com/cache.aspx"
        f"?url={quote_plus(url)}&q={quote_plus(url)}&mkt=en-US&setlang=en-US"
    )
    bing_headers = {
        **_GCACHE_HEADERS,
        "Referer": "https://www.bing.com/",
        "Origin": "https://www.bing.com",
        "X-Client-Data": "",
    }
    resp = _get(bing_url, timeout, proxy, bing_headers)
    if resp is None:
        return None
    html = _decode(resp)
    if len(html.strip()) < 500:
        return None
    return {
        "html": html,
        "cache_source": "bing_cache",
        "cache_url": bing_url,
        "cache_note": "Bing web cache — may be hours old",
    }


def fetch_amp_cache(url: str, timeout: int, proxy: Optional[str]) -> Optional[dict]:
    parsed = urlparse(url)
    domain = parsed.netloc.replace(".", "-")
    path = parsed.path.lstrip("/")
    amp_url = f"https://{domain}.cdn.ampproject.org/c/s/{parsed.netloc}/{path}"
    resp = _get(amp_url, timeout, proxy)
    if resp is None:
        return None
    html = _decode(resp)
    if len(html.strip()) < 500:
        return None
    return {
        "html": html,
        "cache_source": "google_amp",
        "cache_url": amp_url,
        "cache_note": "Google AMP cache",
    }


def fetch_wayback(url: str, timeout: int, proxy: Optional[str]) -> Optional[dict]:
    s = requests.Session()
    s.headers.update(_GCACHE_HEADERS)
    if proxy:
        s.proxies = {"http": proxy, "https": proxy}
    try:
        avail = s.get(
            f"https://archive.org/wayback/available?url={quote_plus(url)}",
            timeout=min(timeout, 12),
        )
        if not avail.ok:
            return None
        snap = avail.json().get("archived_snapshots", {}).get("closest", {})
        if not snap.get("available") or not snap.get("url"):
            return None

        snap_url = snap["url"]
        raw_url = (
            snap_url.replace("//web.archive.org/web/", "//web.archive.org/web/")
            .split("/http")[0]
            + "id_/http"
            + snap_url.split("/http")[1]
        )
        resp = s.get(raw_url, timeout=timeout, allow_redirects=True)
        if not resp.ok:
            resp = s.get(snap_url, timeout=timeout, allow_redirects=True)
        if not resp.ok:
            return None

        html = _decode(resp)
        if len(html.strip()) < 500:
            return None

        return {
            "html": html,
            "cache_source": "wayback_machine",
            "cache_url": snap_url,
            "cache_note": f"Wayback Machine snapshot — {snap.get('timestamp', '?')}",
        }
    except Exception:
        return None


def fetch_best_cache(
    url: str,
    timeout: int = 30,
    proxy: Optional[str] = None,
) -> Optional[dict]:
    """Try all cache sources in speed/reliability order. Returns first hit."""
    for fetcher in [fetch_google_cache, fetch_bing_cache, fetch_amp_cache, fetch_wayback]:
        result = fetcher(url, timeout, proxy)
        if result:
            return result
        time.sleep(0.2)
    return None

"""
web_fetch/helpers/engines.py

Standard HTTP engine + JS-bypass multi-strategy engine.
Adapted from the WebVault scraper project — UI, auth, rate-limit, and
asset-rewriting code removed. All imports are self-contained within the tool.
"""
from __future__ import annotations

import json
import random
import re
import ssl
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import html2text
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter

from glas_mcp.tools.web_fetch.helpers.redirect_handler import follow, RedirectError
from glas_mcp.tools.web_fetch.helpers.cache_engine import fetch_best_cache

try:
    from urllib3.util.ssl_ import create_urllib3_context
    _HAS_CTX = True
except ImportError:
    _HAS_CTX = False

try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False

try:
    import cloudscraper
    _HAS_CS = True
except ImportError:
    _HAS_CS = False


# ── Browser header stacks ──────────────────────────────────────────────────────

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

_MOBILE_UAS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
]

_CHROME_HEADERS = {
    "User-Agent":                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept":                    "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language":           "en-US,en;q=0.9",
    "Accept-Encoding":           "gzip, deflate",
    "Cache-Control":             "max-age=0",
    "Sec-Ch-Ua":                 '"Chromium";v="124","Google Chrome";v="124","Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile":          "?0",
    "Sec-Ch-Ua-Platform":        '"Windows"',
    "Sec-Fetch-Dest":            "document",
    "Sec-Fetch-Mode":            "navigate",
    "Sec-Fetch-Site":            "none",
    "Sec-Fetch-User":            "?1",
    "Upgrade-Insecure-Requests": "1",
    "Connection":                "keep-alive",
}

_CHROME_CIPHERS = ":".join([
    "TLS_AES_128_GCM_SHA256", "TLS_AES_256_GCM_SHA384", "TLS_CHACHA20_POLY1305_SHA256",
    "ECDHE-ECDSA-AES128-GCM-SHA256", "ECDHE-RSA-AES128-GCM-SHA256",
    "ECDHE-ECDSA-AES256-GCM-SHA384", "ECDHE-RSA-AES256-GCM-SHA384",
    "ECDHE-ECDSA-CHACHA20-POLY1305", "ECDHE-RSA-CHACHA20-POLY1305",
    "ECDHE-RSA-AES128-SHA", "ECDHE-RSA-AES256-SHA",
    "AES128-GCM-SHA256", "AES256-GCM-SHA384", "AES128-SHA", "AES256-SHA",
])

# Patterns for extracting embedded state from SPA pages
_EMBEDDED_PATTERNS = [
    (r'<script id="__NEXT_DATA__"[^>]*>([\s\S]*?)</script>',         "Next.js __NEXT_DATA__"),
    (r'window\.__NUXT__\s*=\s*([\s\S]*?);?\s*</script>',             "Nuxt.js __NUXT__"),
    (r'window\.__APOLLO_STATE__\s*=\s*({[\s\S]*?});?\s*</script>',   "__APOLLO_STATE__"),
    (r'window\.__INITIAL_STATE__\s*=\s*({[\s\S]*?});?\s*</script>',  "__INITIAL_STATE__"),
    (r'window\.__PRELOADED_STATE__\s*=\s*({[\s\S]*?});?\s*</script>',"__PRELOADED_STATE__"),
    (r'window\.__REDUX_STATE__\s*=\s*({[\s\S]*?});?\s*</script>',    "__REDUX_STATE__"),
    (r'window\.__APP_STATE__\s*=\s*({[\s\S]*?});?\s*</script>',      "__APP_STATE__"),
    (r'window\.__DATA__\s*=\s*({[\s\S]*?});?\s*</script>',           "__DATA__"),
    (r'window\.__SERVER_DATA__\s*=\s*({[\s\S]*?});?\s*</script>',    "__SERVER_DATA__"),
    (r'window\.pageData\s*=\s*({[\s\S]*?});?\s*</script>',           "Gatsby pageData"),
    (r'data-page="([^"]+)"',                                          "Inertia.js"),
    (r'<script[^>]+type="application/ld\+json"[^>]*>([\s\S]*?)</script>', "JSON-LD"),
    (r'"initialData"\s*:\s*({[\s\S]*?})\s*[,}]',                    "initialData"),
]

_API_PATTERNS = [
    r'fetch\(["\`]([^"\'`]+)["\`]',
    r'axios\.(?:get|post|put|patch|delete)\(["\']([^"\']+)["\']',
    r'["\']((?:/api/|/graphql|/v\d+/)[a-zA-Z0-9/_\-?&=.%]+)["\']',
    r'baseURL["\']?\s*[=:]\s*["\']([^"\']+)["\']',
    r'endpoint["\']?\s*[=:]\s*["\']([^"\']+)["\']',
]

_RECOVERABLE_CODES = {403, 429, 503}
_TERMINAL_CODES    = {400, 401, 402, 404, 405, 410, 451}


# ── TLS adapter ────────────────────────────────────────────────────────────────

class _ChromeTLS(HTTPAdapter):
    def init_poolmanager(self, *a, **kw):
        ctx = (create_urllib3_context() if _HAS_CTX
               else ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT))
        try:
            ctx.set_ciphers(_CHROME_CIPHERS)
        except ssl.SSLError:
            pass
        try:
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        except AttributeError:
            pass
        kw["ssl_context"] = ctx
        super().init_poolmanager(*a, **kw)


def _chrome_session(proxy: Optional[str] = None) -> requests.Session:
    s = requests.Session()
    s.mount("https://", _ChromeTLS())
    s.headers.update(_CHROME_HEADERS)
    if proxy:
        s.proxies = {"http": proxy, "https": proxy}
    return s


# ── Shared HTML parser ─────────────────────────────────────────────────────────

def _parse_html(url: str, html: str, status: int, ua: str) -> Dict[str, Any]:
    """Convert raw HTML to the standard result dict (markdown, links, meta)."""
    soup = BeautifulSoup(html, "html.parser")

    title = (soup.title.string.strip()
             if soup.title and soup.title.string else urlparse(url).netloc)

    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = (desc_tag["content"].strip()
                   if desc_tag and desc_tag.get("content") else "")

    # Strip noise before converting to markdown
    for tag in soup(["style", "script", "noscript", "nav", "footer",
                     "header", "advertisement"]):
        tag.decompose()

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.body_width = 0
    markdown = h.handle(str(soup))

    # Extract all links from original (pre-stripped) HTML
    links: List[Dict[str, str]] = []
    seen: set = set()
    for a in BeautifulSoup(html, "html.parser").find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:")):
            continue
        if not href.startswith("http"):
            href = urljoin(url, href)
        if href not in seen:
            seen.add(href)
            links.append({
                "text": a.get_text(strip=True) or "(no text)",
                "href": href,
            })

    return {
        "success":        True,
        "url":            url,
        "status_code":    status,
        "title":          title,
        "description":    description,
        "markdown":       markdown,
        "raw_html":       html,
        "links":          links,
        "links_count":    len(links),
        "content_length": len(html),
        "ua_used":        ua,
        # True when the page HTML is a JS SPA shell with very little real text
        "is_spa_shell":   len(markdown.strip()) < 300 and len(html) > 5000,
    }


def _error(url: str, code: Optional[int], ua: Optional[str],
           error: str, *, recoverable: bool = False,
           extra: Optional[Dict] = None) -> Dict[str, Any]:
    d: Dict[str, Any] = {
        "success":        False,
        "url":            url,
        "status_code":    code,
        "recoverable":    recoverable,
        "error":          error,
        "title":          urlparse(url).netloc,
        "description":    "",
        "markdown":       "",
        "raw_html":       "",
        "links":          [],
        "links_count":    0,
        "ua_used":        ua,
        "content_length": 0,
    }
    if code:
        d[f"is_{code}"] = True
    if extra:
        d.update(extra)
    return d


# ══════════════════════════════════════════════════════════════════════════════
# STANDARD ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def scrape_standard(
    url: str,
    user_agent: Optional[str] = None,
    timeout: int = 30,
    proxy: Optional[str] = None,
    retries: int = 3,
) -> Dict[str, Any]:
    """Standard HTTP scraper with browser-like headers and retry logic."""
    if not url.startswith("http"):
        url = f"https://{url}"

    ua = user_agent or random.choice(_USER_AGENTS)
    session = requests.Session()
    session.headers.update({
        **_CHROME_HEADERS,
        "User-Agent": ua,
    })
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}

    last_error = "Unknown error"

    for attempt in range(1, retries + 1):
        try:
            resp, final_url, chain = follow(url, session, timeout)
            resp.raise_for_status()
            result = _parse_html(final_url, resp.text, resp.status_code, ua)
            result["final_url"] = final_url
            if len(chain) > 1:
                result["redirect_chain"] = chain
            return result

        except requests.exceptions.HTTPError as exc:
            code = exc.response.status_code if exc.response is not None else 0
            last_error = str(exc)
            if code == 403:
                return _error(url, 403, ua, "403 Forbidden", recoverable=True)
            if code == 429:
                ra = (exc.response.headers.get("Retry-After", "?")
                      if exc.response is not None else "?")
                return _error(url, 429, ua,
                              f"429 Rate Limited (Retry-After: {ra})",
                              recoverable=True, extra={"retry_after": ra})
            if code == 503:
                if attempt < retries:
                    time.sleep(2 ** attempt)
                    continue
                return _error(url, 503, ua, "503 Service Unavailable", recoverable=True)
            if code in _TERMINAL_CODES:
                return _error(url, code, ua, f"HTTP {code}", recoverable=False)
            if attempt < retries:
                time.sleep(2 ** attempt)

        except requests.exceptions.SSLError:
            last_error = "SSL error"
            try:
                session.verify = False
                resp, final_url, chain = follow(url, session, timeout)
                result = _parse_html(final_url, resp.text, resp.status_code, ua)
                result["final_url"] = final_url
                result["ssl_warning"] = "Certificate verification disabled"
                return result
            except Exception:
                pass

        except RedirectError as exc:
            return _error(url, None, ua,
                          f"Redirect error: {exc} (chain: {' → '.join(exc.chain[-3:])})",
                          recoverable=True)

        except requests.exceptions.RequestException as exc:
            last_error = str(exc)
            if attempt < retries:
                time.sleep(2 ** attempt)

    return _error(url, None, ua, last_error, recoverable=True)


# ══════════════════════════════════════════════════════════════════════════════
# JS BYPASS STRATEGIES
# ══════════════════════════════════════════════════════════════════════════════

def _strat_smart(url, timeout, proxy):
    s = _chrome_session(proxy)
    resp, final, chain = follow(url, s, timeout)
    resp.raise_for_status()
    r = _parse_html(final, resp.text, resp.status_code, s.headers["User-Agent"])
    r["final_url"] = final
    if len(chain) > 1:
        r["redirect_chain"] = chain
    return r


def _strat_warmup(url, timeout, proxy):
    parsed = urlparse(url)
    home = f"{parsed.scheme}://{parsed.netloc}"
    s = _chrome_session(proxy)
    try:
        s.get(home, timeout=min(timeout, 12), allow_redirects=True)
        time.sleep(random.uniform(0.7, 1.6))
    except Exception:
        pass
    s.headers.update({"Referer": home, "Origin": home})
    resp, final, chain = follow(url, s, timeout)
    resp.raise_for_status()
    r = _parse_html(final, resp.text, resp.status_code, s.headers["User-Agent"])
    r["final_url"] = final
    if len(chain) > 1:
        r["redirect_chain"] = chain
    return r


def _strat_referer(url, timeout, proxy):
    parsed = urlparse(url)
    s = _chrome_session(proxy)
    s.headers.update({
        "Referer":        f"https://www.google.com/search?q={parsed.netloc}",
        "Origin":         "https://www.google.com",
        "Sec-Fetch-Site": "cross-site",
    })
    resp, final, chain = follow(url, s, timeout)
    resp.raise_for_status()
    r = _parse_html(final, resp.text, resp.status_code, s.headers["User-Agent"])
    r["final_url"] = final
    if len(chain) > 1:
        r["redirect_chain"] = chain
    return r


def _strat_tls(url, timeout, proxy):
    s = _chrome_session(proxy)
    time.sleep(0.2)
    resp, final, chain = follow(url, s, timeout)
    resp.raise_for_status()
    r = _parse_html(final, resp.text, resp.status_code, s.headers["User-Agent"])
    r["final_url"] = final
    if len(chain) > 1:
        r["redirect_chain"] = chain
    return r


def _strat_http2(url, timeout, proxy):
    if not _HAS_HTTPX:
        return {"success": False, "error": "httpx not installed"}
    proxies = {"all://": proxy} if proxy else None
    with httpx.Client(http2=True, follow_redirects=True, proxies=proxies,
                      timeout=timeout, headers=_CHROME_HEADERS) as c:
        resp = c.get(url)
        resp.raise_for_status()
        r = _parse_html(str(resp.url), resp.text, resp.status_code,
                        _CHROME_HEADERS["User-Agent"])
        r["final_url"] = str(resp.url)
        return r


def _strat_cloudscraper(url, timeout, proxy):
    if not _HAS_CS:
        return {"success": False, "error": "cloudscraper not installed"}
    sc = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    if proxy:
        sc.proxies = {"http": proxy, "https": proxy}
    resp = sc.get(url, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()
    r = _parse_html(resp.url, resp.text, resp.status_code,
                    sc.headers.get("User-Agent", ""))
    r["final_url"] = resp.url
    return r


def _strat_mobile(url, timeout, proxy):
    s = _chrome_session(proxy)
    s.headers.update({
        "User-Agent":       random.choice(_MOBILE_UAS),
        "Sec-Ch-Ua-Mobile": "?1",
        "Sec-Ch-Ua-Platform": '"Android"',
    })
    resp, final, chain = follow(url, s, timeout)
    resp.raise_for_status()
    r = _parse_html(final, resp.text, resp.status_code, s.headers["User-Agent"])
    r["final_url"] = final
    if len(chain) > 1:
        r["redirect_chain"] = chain
    return r


def _strat_embedded_json(url, timeout, proxy):
    s = _chrome_session(proxy)
    resp, final, _ = follow(url, s, timeout)
    resp.raise_for_status()
    html = resp.text
    found = []
    for pat, label in _EMBEDDED_PATTERNS:
        for m in re.finditer(pat, html, re.DOTALL):
            raw = m.group(1).strip()
            try:
                found.append({"source": label, "data": json.loads(raw)})
            except Exception:
                if len(raw) > 30:
                    found.append({"source": label, "data": raw[:2000]})
    if not found:
        return {"success": False, "error": "No embedded JSON state found"}

    md = f"# Embedded Data — {url}\n\n"
    for item in found:
        md += (f"## {item['source']}\n\n```json\n"
               f"{json.dumps(item['data'], indent=2, ensure_ascii=False)[:5000]}"
               f"\n```\n\n")
    base = _parse_html(final, html, resp.status_code, s.headers["User-Agent"])
    base["final_url"] = final
    base["markdown"] = md + "\n\n---\n\n" + base.get("markdown", "")
    base["embedded_data"] = found
    base["embedded_count"] = len(found)
    return base


def _strat_api_discovery(url, timeout, proxy):
    s = _chrome_session(proxy)
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    resp, _, _ = follow(url, s, timeout)
    soup = BeautifulSoup(resp.text, "html.parser")

    js = "\n".join(t.string or "" for t in soup.find_all("script") if not t.get("src"))
    for tag in soup.find_all("script", src=True):
        src = tag["src"]
        if not src.startswith("http"):
            src = urljoin(base_url, src)
        name = src.split("/")[-1].split("?")[0].lower()
        if any(k in name for k in ("main", "app", "index", "chunk", "bundle")):
            try:
                rb = s.get(src, timeout=10)
                if rb.ok:
                    js += rb.text[:150_000]
            except Exception:
                pass

    endpoints: set = set()
    for pat in _API_PATTERNS:
        for m in re.finditer(pat, js):
            ep = m.group(1)
            if not ep.startswith("http"):
                ep = urljoin(base_url, ep)
            if parsed.netloc in ep:
                endpoints.add(ep)

    if not endpoints:
        return {"success": False, "error": "No API endpoints found in JS bundles"}

    api_results = []
    json_headers = {
        **_CHROME_HEADERS,
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    }
    for ep in list(endpoints)[:8]:
        try:
            rj = s.get(ep, headers=json_headers, timeout=10)
            if rj.ok and "json" in rj.headers.get("content-type", ""):
                api_results.append({"endpoint": ep, "data": rj.json()})
        except Exception:
            pass

    md = f"# API Discovery — {url}\n\n## Endpoints ({len(endpoints)})\n\n"
    md += "\n".join(f"- `{e}`" for e in sorted(endpoints))
    if api_results:
        md += "\n\n## Live Responses\n\n"
        for item in api_results:
            md += (f"### `{item['endpoint']}`\n```json\n"
                   f"{json.dumps(item['data'], indent=2)[:3000]}\n```\n\n")

    base = _parse_html(url, resp.text, resp.status_code, s.headers["User-Agent"])
    base["final_url"] = url
    base["markdown"] = md + "\n\n---\n\n" + base.get("markdown", "")
    base["discovered_endpoints"] = sorted(endpoints)
    base["api_results"] = api_results
    return base


def _strat_cache(url, timeout, proxy):
    hit = fetch_best_cache(url, timeout, proxy)
    if not hit:
        return {"success": False, "error": "All cache sources failed"}
    base = _parse_html(url, hit["html"], 200, "cache")
    base["final_url"] = url
    base.update({k: hit[k] for k in ("cache_source", "cache_url", "cache_note") if k in hit})
    return base


# ── Strategy registry ──────────────────────────────────────────────────────────

_STRATEGIES: Dict[str, Any] = {
    "smart_headers":   _strat_smart,
    "session_warmup":  _strat_warmup,
    "referer_bypass":  _strat_referer,
    "tls_ciphers":     _strat_tls,
    "http2":           _strat_http2,
    "cloudscraper":    _strat_cloudscraper,
    "mobile_bypass":   _strat_mobile,
    "embedded_json":   _strat_embedded_json,
    "api_discovery":   _strat_api_discovery,
    "cache_fallback":  _strat_cache,
}


def available_strategies() -> List[str]:
    strats = ["smart_headers", "session_warmup", "referer_bypass", "tls_ciphers"]
    if _HAS_HTTPX:
        strats.append("http2")
    if _HAS_CS:
        strats.append("cloudscraper")
    strats += ["mobile_bypass", "embedded_json", "api_discovery", "cache_fallback"]
    return strats


def _strategy_order(preferred: str) -> List[str]:
    available = available_strategies()
    if preferred != "auto" and preferred in available:
        available.remove(preferred)
        return [preferred] + available
    return available


# ══════════════════════════════════════════════════════════════════════════════
# JS ENGINE — cycles through all bypass strategies
# ══════════════════════════════════════════════════════════════════════════════

def scrape_js(
    url: str,
    timeout: int = 30,
    proxy: Optional[str] = None,
    preferred: str = "auto",
) -> Dict[str, Any]:
    """Try all JS bypass strategies in order. Returns first success."""
    if not url.startswith("http"):
        url = f"https://{url}"

    order = _strategy_order(preferred)
    errors: List[str] = []

    for name in order:
        try:
            result = _STRATEGIES[name](url, timeout, proxy)
            if result and result.get("success"):
                result["strategy_used"] = name
                result["strategies_tried"] = order
                return result
            if result and result.get("error"):
                errors.append(f"{name}: {result['error']}")
        except Exception as exc:
            errors.append(f"{name}: {exc}")

    return {
        **_error(url, None, None,
                 "All JS strategies failed. " + " | ".join(errors[-3:]),
                 recoverable=False),
        "strategy_used":    None,
        "strategies_tried": order,
    }

"""Weblate API client for l10n.elementaryos.org."""

import json
import os
import threading
import time
from pathlib import Path
from typing import Callable

import requests

BASE_URL = "https://l10n.elementaryos.org"
API = f"{BASE_URL}/api"

CONFIG_DIR = Path.home() / ".config" / "elementary-l10n"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_DIR = Path.home() / ".cache" / "elementary-l10n"
CACHE_FILE = CACHE_DIR / "cache.json"

REQUEST_DELAY = 0.6  # seconds between API calls


def load_config() -> dict:
    """Load config from ~/.config/elementary-l10n/config.json."""
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {}


def save_config(config: dict):
    """Save config to ~/.config/elementary-l10n/config.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def load_cache(language_code: str) -> tuple[list | None, float | None]:
    """Load cached data. Returns (data, timestamp) or (None, None)."""
    try:
        cache = json.loads(CACHE_FILE.read_text())
        if cache.get("language") == language_code:
            return cache["data"], cache["timestamp"]
    except Exception:
        pass
    return None, None


def save_cache(language_code: str, data: list):
    """Save data to cache with current timestamp."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps({
        "language": language_code,
        "data": data,
        "timestamp": time.time(),
    }, indent=2))


def _request_with_retry(session: requests.Session, url: str, max_retries: int = 4) -> requests.Response:
    """Make a GET request with exponential backoff on 429."""
    for attempt in range(max_retries):
        r = session.get(url, timeout=30)
        if r.status_code == 429:
            wait = 2 ** (attempt + 1)  # 2, 4, 8, 16
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r
    # Final attempt
    r = session.get(url, timeout=30)
    r.raise_for_status()
    return r


def _get_all(url: str, session: requests.Session) -> list:
    """Paginate through Weblate API results with rate limiting."""
    results = []
    while url:
        r = _request_with_retry(session, url)
        data = r.json()
        results.extend(data.get("results", []))
        url = data.get("next")
        if url:
            time.sleep(REQUEST_DELAY)
    return results


def _make_session(api_key: str | None = None) -> requests.Session:
    """Create a requests session with optional API key auth."""
    session = requests.Session()
    session.headers["User-Agent"] = "elementary-l10n/0.1.0"
    if api_key:
        session.headers["Authorization"] = f"Token {api_key}"
    return session


def fetch_projects(session: requests.Session) -> list[dict]:
    return _get_all(f"{API}/projects/", session)


def fetch_components(project_slug: str, session: requests.Session) -> list[dict]:
    return _get_all(f"{API}/projects/{project_slug}/components/", session)


def fetch_statistics(project_slug: str, component_slug: str,
                     language_code: str, session: requests.Session) -> dict:
    url = f"{API}/translations/{project_slug}/{component_slug}/{language_code}/statistics/"
    r = _request_with_retry(session, url)
    return r.json()


def fetch_component_statistics(project_slug: str, component_slug: str,
                               session: requests.Session) -> list[dict]:
    return _get_all(
        f"{API}/components/{project_slug}/{component_slug}/statistics/", session
    )


def component_web_url(project_slug: str, component_slug: str) -> str:
    return f"{BASE_URL}/projects/{project_slug}/{component_slug}/"


def component_translate_url(project_slug: str, component_slug: str,
                            language_code: str) -> str:
    return f"{BASE_URL}/projects/{project_slug}/{component_slug}/{language_code}/"


def fetch_all_data(language_code: str, callback: Callable, error_cb: Callable,
                   cache_cb: Callable | None = None):
    """Fetch all projects, components and stats in a background thread.

    callback(data) on fresh data.
    error_cb(exception) on failure.
    cache_cb(data, age_minutes) if cached data is available (<1h old).
    """
    # Check cache first
    cached_data, cached_ts = load_cache(language_code)
    if cached_data and cached_ts:
        age_seconds = time.time() - cached_ts
        if age_seconds < 3600:  # < 1 hour
            age_minutes = int(age_seconds / 60)
            if cache_cb:
                cache_cb(cached_data, age_minutes)

    def _worker():
        try:
            config = load_config()
            api_key = config.get("api_key")
            session = _make_session(api_key)

            projects = fetch_projects(session)
            rows = []

            for proj in projects:
                ps = proj["slug"]
                time.sleep(REQUEST_DELAY)
                components = fetch_components(ps, session)

                for comp in components:
                    cs = comp["slug"]
                    time.sleep(REQUEST_DELAY)
                    try:
                        stats = fetch_statistics(ps, cs, language_code, session)
                        pct = stats.get("translated_percent", 0.0)
                    except requests.HTTPError:
                        pct = 0.0

                    rows.append({
                        "project": proj["name"],
                        "project_slug": ps,
                        "component": comp["name"],
                        "component_slug": cs,
                        "translated_percent": pct,
                        "url": component_web_url(ps, cs),
                        "translate_url": component_translate_url(ps, cs, language_code),
                    })

            save_cache(language_code, rows)
            callback(rows)
        except Exception as e:
            error_cb(e)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()

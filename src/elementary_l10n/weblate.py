"""Weblate API client for l10n.elementaryos.org."""

import threading
from typing import Callable
import requests

BASE_URL = "https://l10n.elementaryos.org"
API = f"{BASE_URL}/api"


def _get_all(url: str, session: requests.Session) -> list:
    """Paginate through Weblate API results."""
    results = []
    while url:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        results.extend(data.get("results", []))
        url = data.get("next")
    return results


def fetch_projects(session: requests.Session) -> list[dict]:
    return _get_all(f"{API}/projects/", session)


def fetch_components(project_slug: str, session: requests.Session) -> list[dict]:
    return _get_all(f"{API}/projects/{project_slug}/components/", session)


def fetch_statistics(project_slug: str, component_slug: str,
                     language_code: str, session: requests.Session) -> dict:
    """Fetch stats for a specific component+language."""
    url = f"{API}/translations/{project_slug}/{component_slug}/{language_code}/statistics/"
    r = session.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_component_statistics(project_slug: str, component_slug: str,
                               session: requests.Session) -> list[dict]:
    """Fetch stats for all languages of a component."""
    return _get_all(
        f"{API}/components/{project_slug}/{component_slug}/statistics/", session
    )


def component_web_url(project_slug: str, component_slug: str) -> str:
    return f"{BASE_URL}/projects/{project_slug}/{component_slug}/"


def component_translate_url(project_slug: str, component_slug: str,
                            language_code: str) -> str:
    return f"{BASE_URL}/projects/{project_slug}/{component_slug}/{language_code}/"


def fetch_all_data(language_code: str, callback: Callable, error_cb: Callable):
    """Fetch all projects, components and stats in a background thread.
    
    callback(data) where data = list of dicts with keys:
        project, component, slug, component_slug, translated_percent, url, translate_url
    error_cb(exception) on failure.
    """
    def _worker():
        try:
            session = requests.Session()
            session.headers["User-Agent"] = "elementary-l10n/0.1.0"
            
            projects = fetch_projects(session)
            rows = []
            
            for proj in projects:
                ps = proj["slug"]
                components = fetch_components(ps, session)
                
                for comp in components:
                    cs = comp["slug"]
                    try:
                        stats = fetch_statistics(ps, cs, language_code, session)
                        pct = stats.get("translated_percent", 0.0)
                    except requests.HTTPError:
                        # Language might not exist for this component
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
            
            callback(rows)
        except Exception as e:
            error_cb(e)
    
    t = threading.Thread(target=_worker, daemon=True)
    t.start()

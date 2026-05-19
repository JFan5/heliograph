from __future__ import annotations

import html as html_lib
import os
from datetime import date, timedelta

import requests

from heliograph.components.base import BaseComponent, ComponentResult

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"


class GitHubTrendingComponent(BaseComponent):
    """Top recently-created GitHub repos by stars — a poor-man's 'trending'."""

    name = "github_trending"
    title = "GitHub Trending"
    order = 30

    def render(self) -> ComponentResult:
        days = int(self.config.get("days_window", 7))
        limit = int(self.config.get("limit", 5))
        language = self.config.get("language")  # e.g. "python", optional

        since = (date.today() - timedelta(days=days)).isoformat()
        query_parts = [f"created:>{since}"]
        if language:
            query_parts.append(f"language:{language}")
        params = {
            "q": " ".join(query_parts),
            "sort": "stars",
            "order": "desc",
            "per_page": limit,
        }
        headers = {"Accept": "application/vnd.github+json"}
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        resp = requests.get(GITHUB_SEARCH_URL, params=params, headers=headers, timeout=20)
        resp.raise_for_status()
        items = resp.json().get("items", [])

        html_rows = []
        text_rows = []
        for i, repo in enumerate(items, 1):
            full = repo["full_name"]
            stars = repo["stargazers_count"]
            desc = (repo.get("description") or "").strip()
            lang = repo.get("language") or ""
            url = repo["html_url"]
            html_rows.append(
                f'<div style="margin:6px 0;">'
                f'<a href="{url}" style="color:#2563eb;text-decoration:none;font-weight:600;">{html_lib.escape(full)}</a> '
                f'<span style="color:#9ca3af;font-size:12px;">★ {stars:,}'
                + (f' · {html_lib.escape(lang)}' if lang else "")
                + "</span>"
                + (f'<div style="color:#4b5563;font-size:13px;margin-top:2px;">{html_lib.escape(desc)}</div>' if desc else "")
                + "</div>"
            )
            text_rows.append(f"{i}. {full} (★{stars:,}{', ' + lang if lang else ''})\n   {desc}\n   {url}")

        if not html_rows:
            html = '<p style="color:#9ca3af;">(No trending repos returned)</p>'
            text = "(No trending repos returned)"
        else:
            html = "".join(html_rows)
            text = "\n".join(text_rows)
        return ComponentResult(
            name=self.name, title=self.title, html=html, text=text, order=self.order,
            meta={"window_days": days, "count": len(items)},
        )

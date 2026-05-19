from __future__ import annotations

import html as html_lib
import json
import re

import requests

from heliograph.components.base import BaseComponent, ComponentResult

SKILLS_URL = "https://www.skills.sh/trending"
# The Next.js Flight payload embeds the data as a JSON array of objects.
# Each escaped quote is `\"`, so we match the array literal between
# `\"initialSkills\":` and the next `]`.
_INITIAL_SKILLS_RE = re.compile(r'\\"initialSkills\\":(\[[^\]]*?\])')


def parse_skills_html(html: str) -> list[dict]:
    m = _INITIAL_SKILLS_RE.search(html)
    if not m:
        return []
    inner = m.group(1)
    # Un-escape the Flight payload string: \" -> ", \\ -> \, \n -> newline, etc.
    unescaped = bytes(inner, "utf-8").decode("unicode_escape")
    try:
        return json.loads(unescaped)
    except json.JSONDecodeError:
        return []


class SkillTrendingComponent(BaseComponent):
    """Trending skills from skills.sh (24h leaderboard)."""

    name = "skill_trending"
    title = "Trending Agent Skills"
    order = 35

    def render(self) -> ComponentResult:
        limit = int(self.config.get("limit", 5))
        resp = requests.get(SKILLS_URL, headers={"User-Agent": "heliograph/0.1"}, timeout=20)
        resp.raise_for_status()
        skills = parse_skills_html(resp.text)[:limit]

        html_rows = []
        text_rows = []
        for i, s in enumerate(skills, 1):
            name = s.get("name", "")
            source = s.get("source", "")
            installs = s.get("installs", 0)
            skill_id = s.get("skillId", name)
            url = f"https://www.skills.sh/{source}/{skill_id}" if source else "https://www.skills.sh/"
            badge = ' <span style="color:#f59e0b;font-size:11px;">official</span>' if s.get("isOfficial") else ""
            html_rows.append(
                f'<div style="margin:6px 0;">'
                f'<a href="{url}" style="color:#2563eb;text-decoration:none;font-weight:600;">{html_lib.escape(name)}</a>'
                f'{badge} '
                f'<span style="color:#9ca3af;font-size:12px;">{installs:,} installs</span>'
                f'<div style="color:#6b7280;font-size:12px;">{html_lib.escape(source)}</div>'
                f"</div>"
            )
            text_rows.append(f"{i}. {name} ({source}) — {installs:,} installs\n   {url}")

        if not html_rows:
            html = '<p style="color:#9ca3af;">(Could not parse skills.sh leaderboard)</p>'
            text = "(Could not parse skills.sh leaderboard)"
        else:
            html = "".join(html_rows)
            text = "\n".join(text_rows)
        return ComponentResult(
            name=self.name, title=self.title, html=html, text=text, order=self.order,
            meta={"count": len(skills)},
        )

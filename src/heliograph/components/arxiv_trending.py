from __future__ import annotations

import html as html_lib
import xml.etree.ElementTree as ET

import requests

from heliograph.components.base import BaseComponent, ComponentResult

ARXIV_URL = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom"}


class ArxivTrendingComponent(BaseComponent):
    """Most recent papers from one or more arXiv categories."""

    name = "arxiv_trending"
    title = "Latest from arXiv"
    order = 40

    def render(self) -> ComponentResult:
        categories = self.config.get("categories", ["cs.AI"])
        if isinstance(categories, str):
            categories = [categories]
        limit = int(self.config.get("limit", 5))

        query = " OR ".join(f"cat:{c}" for c in categories)
        params = {
            "search_query": query,
            "start": 0,
            "max_results": limit,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        resp = requests.get(ARXIV_URL, params=params, timeout=20)
        resp.raise_for_status()

        root = ET.fromstring(resp.text)
        entries = root.findall("atom:entry", NS)

        html_rows = []
        text_rows = []
        for i, entry in enumerate(entries, 1):
            title = (entry.findtext("atom:title", default="", namespaces=NS) or "").strip().replace("\n", " ")
            abs_url = (entry.findtext("atom:id", default="", namespaces=NS) or "").strip()
            summary = (entry.findtext("atom:summary", default="", namespaces=NS) or "").strip().replace("\n", " ")
            authors = [
                (a.findtext("atom:name", default="", namespaces=NS) or "").strip()
                for a in entry.findall("atom:author", NS)
            ]
            first_author = authors[0] if authors else ""
            more = f" + {len(authors) - 1} others" if len(authors) > 1 else ""

            # Trim summary to a sensible preview.
            preview = summary if len(summary) <= 220 else summary[:220].rsplit(" ", 1)[0] + "…"

            html_rows.append(
                f'<div style="margin:8px 0;">'
                f'<a href="{abs_url}" style="color:#2563eb;text-decoration:none;font-weight:600;">{html_lib.escape(title)}</a>'
                f'<div style="color:#6b7280;font-size:12px;margin-top:2px;">{html_lib.escape(first_author)}{html_lib.escape(more)}</div>'
                f'<div style="color:#4b5563;font-size:13px;margin-top:2px;">{html_lib.escape(preview)}</div>'
                f"</div>"
            )
            text_rows.append(f"{i}. {title}\n   {first_author}{more}\n   {abs_url}")

        if not html_rows:
            html = '<p style="color:#9ca3af;">(No arXiv entries returned)</p>'
            text = "(No arXiv entries returned)"
        else:
            html = "".join(html_rows)
            text = "\n".join(text_rows)
        return ComponentResult(
            name=self.name, title=self.title, html=html, text=text, order=self.order,
            meta={"categories": categories, "count": len(entries)},
        )

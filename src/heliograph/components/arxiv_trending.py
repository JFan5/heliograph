from __future__ import annotations

import html as html_lib
import xml.etree.ElementTree as ET

import requests

from heliograph.components.base import BaseComponent, ComponentResult
from heliograph.summarizer import translate_arxiv_batch

ARXIV_URL = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom"}


def _fetch_papers(categories: list[str], limit: int) -> list[dict]:
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
    out = []
    for entry in root.findall("atom:entry", NS):
        title = (entry.findtext("atom:title", default="", namespaces=NS) or "").strip().replace("\n", " ")
        abs_url = (entry.findtext("atom:id", default="", namespaces=NS) or "").strip()
        summary = (entry.findtext("atom:summary", default="", namespaces=NS) or "").strip().replace("\n", " ")
        authors = [
            (a.findtext("atom:name", default="", namespaces=NS) or "").strip()
            for a in entry.findall("atom:author", NS)
        ]
        out.append({"title": title, "url": abs_url, "summary": summary, "authors": authors})
    return out


class ArxivTrendingComponent(BaseComponent):
    """Most recent papers from one or more arXiv categories.

    Set `translate_to_zh: true` in config to have `claude -p` translate each
    paper's title and write a one-sentence Chinese summary (batched into a
    single CLI call). If translation fails, falls back to the English text.
    """

    name = "arxiv_trending"
    title = "Latest from arXiv"
    order = 40

    def render(self) -> ComponentResult:
        categories = self.config.get("categories", ["cs.AI"])
        if isinstance(categories, str):
            categories = [categories]
        limit = int(self.config.get("limit", 5))
        translate = bool(self.config.get("translate_to_zh", False))

        papers = _fetch_papers(categories, limit)

        translations: list[dict[str, str]] = []
        if translate and papers:
            translations = translate_arxiv_batch(papers)

        html_rows = []
        text_rows = []
        for i, paper in enumerate(papers):
            tr = translations[i] if i < len(translations) else {}
            title_zh = tr.get("title_zh", "")
            summary_zh = tr.get("summary_zh", "")

            title_en = paper["title"]
            display_title = title_zh or title_en
            authors = paper["authors"]
            first_author = authors[0] if authors else ""
            more = f" + {len(authors) - 1} others" if len(authors) > 1 else ""

            if summary_zh:
                preview = summary_zh
            else:
                en = paper["summary"]
                preview = en if len(en) <= 220 else en[:220].rsplit(" ", 1)[0] + "…"

            # If we have a Chinese title, keep the original English title as a small subtitle.
            subtitle_html = (
                f'<div style="color:#9ca3af;font-size:11px;font-style:italic;margin-top:1px;">{html_lib.escape(title_en)}</div>'
                if title_zh else ""
            )

            html_rows.append(
                f'<div style="margin:10px 0;">'
                f'<a href="{paper["url"]}" style="color:#2563eb;text-decoration:none;font-weight:600;">{html_lib.escape(display_title)}</a>'
                f'{subtitle_html}'
                f'<div style="color:#6b7280;font-size:12px;margin-top:2px;">{html_lib.escape(first_author)}{html_lib.escape(more)}</div>'
                f'<div style="color:#4b5563;font-size:13px;margin-top:2px;">{html_lib.escape(preview)}</div>'
                f"</div>"
            )
            if title_zh:
                text_rows.append(
                    f"{i+1}. {title_zh}\n   ({title_en})\n   {first_author}{more}\n   {preview}\n   {paper['url']}"
                )
            else:
                text_rows.append(
                    f"{i+1}. {title_en}\n   {first_author}{more}\n   {preview}\n   {paper['url']}"
                )

        if not html_rows:
            html = '<p style="color:#9ca3af;">(No arXiv entries returned)</p>'
            text = "(No arXiv entries returned)"
        else:
            html = "".join(html_rows)
            text = "\n".join(text_rows)
        return ComponentResult(
            name=self.name, title=self.title, html=html, text=text, order=self.order,
            meta={"categories": categories, "count": len(papers),
                  "translated": bool(translations and any(t for t in translations))},
        )

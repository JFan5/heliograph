from __future__ import annotations

import html as html_lib

import requests

from heliograph.components.base import BaseComponent, ComponentResult

HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{id}.json"
HN_DISCUSSION_URL = "https://news.ycombinator.com/item?id={id}"


class HNTopComponent(BaseComponent):
    """Top stories from Hacker News (Firebase API)."""

    name = "hn_top"
    title = "Hacker News Top"
    order = 50

    def render(self) -> ComponentResult:
        limit = int(self.config.get("limit", 5))
        timeout = int(self.config.get("timeout", 15))

        ids_resp = requests.get(HN_TOP_URL, timeout=timeout)
        ids_resp.raise_for_status()
        ids = ids_resp.json()[:limit]

        items = []
        for sid in ids:
            r = requests.get(HN_ITEM_URL.format(id=sid), timeout=timeout)
            if r.ok and r.json():
                items.append(r.json())

        html_rows: list[str] = []
        text_rows: list[str] = []
        for i, it in enumerate(items, 1):
            title = it.get("title", "(no title)")
            url = it.get("url") or HN_DISCUSSION_URL.format(id=it["id"])
            score = it.get("score", 0)
            ncomments = it.get("descendants", 0)
            by = it.get("by", "")
            discussion = HN_DISCUSSION_URL.format(id=it["id"])

            html_rows.append(
                f'<div style="margin:6px 0;">'
                f'<a href="{url}" style="color:#2563eb;text-decoration:none;font-weight:600;">{html_lib.escape(title)}</a>'
                f' <span style="color:#9ca3af;font-size:12px;">▲ {score} · '
                f'<a href="{discussion}" style="color:#9ca3af;text-decoration:none;">{ncomments} comments</a>'
                + (f' · {html_lib.escape(by)}' if by else "")
                + "</span></div>"
            )
            text_rows.append(f"{i}. {title}  (▲{score} · {ncomments} comments)\n   {url}")

        if not html_rows:
            html = '<p style="color:#9ca3af;">(No HN stories returned)</p>'
            text = "(No HN stories returned)"
        else:
            html = "".join(html_rows)
            text = "\n".join(text_rows)
        return ComponentResult(
            name=self.name, title=self.title, html=html, text=text, order=self.order,
            meta={"count": len(items)},
        )

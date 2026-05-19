from __future__ import annotations

from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from heliograph.components.base import ComponentResult

TEMPLATES_DIR = Path(__file__).parent / "templates"


class EmailRenderer:
    def __init__(self, template_name: str = "email.html") -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html"]),
        )
        self.template_name = template_name

    def render(self, sections: list[ComponentResult], title: str | None = None) -> tuple[str, str]:
        today = date.today()
        title = title or f"Heliograph · {today.isoformat()}"
        template = self.env.get_template(self.template_name)
        html = template.render(title=title, sections=sections, today=today)
        text_parts = [title, "=" * len(title), ""]
        for s in sections:
            text_parts.append(f"## {s.title}")
            text_parts.append(s.text or "(html-only section)")
            text_parts.append("")
        return html, "\n".join(text_parts)

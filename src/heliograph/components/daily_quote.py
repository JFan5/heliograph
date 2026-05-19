from __future__ import annotations

import random
from datetime import date

from heliograph.components.base import BaseComponent, ComponentResult

QUOTES = [
    ("The only way to do great work is to love what you do.", "Steve Jobs"),
    ("Simplicity is the ultimate sophistication.", "Leonardo da Vinci"),
    ("Stay hungry, stay foolish.", "Whole Earth Catalog"),
    ("What we think, we become.", "Buddha"),
    ("The best way out is always through.", "Robert Frost"),
    ("Make it work, make it right, make it fast.", "Kent Beck"),
]


class DailyQuoteComponent(BaseComponent):
    name = "daily_quote"
    title = "Quote of the Day"
    order = 10

    def render(self) -> ComponentResult:
        seed = self.config.get("seed")
        rng = random.Random(seed if seed is not None else date.today().toordinal())
        quote, author = rng.choice(QUOTES)
        html = (
            f'<blockquote style="margin:0;padding:12px 16px;border-left:4px solid #f59e0b;'
            f'background:#fffbeb;color:#1f2937;font-style:italic;">'
            f'"{quote}"<br><span style="font-style:normal;color:#6b7280;">— {author}</span>'
            f'</blockquote>'
        )
        text = f'"{quote}" — {author}'
        return ComponentResult(
            name=self.name, title=self.title, html=html, text=text, order=self.order
        )

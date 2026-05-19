from __future__ import annotations

import html as html_lib

import requests

from heliograph.components.base import BaseComponent, ComponentResult

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

# (label, yahoo_symbol, decimals_for_price)
DEFAULT_TICKERS: list[tuple[str, str, int]] = [
    ("S&P 500", "^GSPC", 2),
    ("Gold", "GC=F", 2),
    ("BTC", "BTC-USD", 0),
]


def _fetch_quote(symbol: str, timeout: int = 15) -> dict:
    r = requests.get(
        YAHOO_CHART_URL.format(symbol=requests.utils.quote(symbol, safe="")),
        params={"interval": "1d", "range": "2d"},
        headers={"User-Agent": "Mozilla/5.0 heliograph"},
        timeout=timeout,
    )
    r.raise_for_status()
    meta = r.json()["chart"]["result"][0]["meta"]
    price = float(meta["regularMarketPrice"])
    prev = float(meta.get("chartPreviousClose") or meta.get("previousClose") or price)
    return {"price": price, "prev": prev, "change": price - prev,
            "change_pct": (price - prev) / prev * 100 if prev else 0.0}


def _color(change: float) -> str:
    if change > 0:
        return "#16a34a"  # green
    if change < 0:
        return "#dc2626"  # red
    return "#6b7280"


class MarketsSummaryComponent(BaseComponent):
    """One-line summaries of S&P 500, Gold, and BTC (overridable in config)."""

    name = "markets_summary"
    title = "Markets"
    order = 20

    def render(self) -> ComponentResult:
        tickers_cfg = self.config.get("tickers")
        if tickers_cfg:
            tickers = [(t["label"], t["symbol"], int(t.get("decimals", 2))) for t in tickers_cfg]
        else:
            tickers = DEFAULT_TICKERS

        html_rows: list[str] = []
        text_rows: list[str] = []
        for label, symbol, decimals in tickers:
            try:
                q = _fetch_quote(symbol)
            except Exception as exc:  # noqa: BLE001
                html_rows.append(
                    f'<div style="margin:4px 0;color:#9ca3af;font-size:13px;">'
                    f'{html_lib.escape(label)}: <em>fetch failed ({html_lib.escape(str(exc))})</em></div>'
                )
                text_rows.append(f"{label}: fetch failed ({exc})")
                continue
            color = _color(q["change"])
            arrow = "▲" if q["change"] >= 0 else "▼"
            price_str = f"{q['price']:,.{decimals}f}"
            html_rows.append(
                f'<div style="margin:4px 0;font-size:14px;">'
                f'<span style="display:inline-block;min-width:80px;color:#6b7280;">{html_lib.escape(label)}</span>'
                f'<span style="font-weight:600;color:#111827;">{price_str}</span> '
                f'<span style="color:{color};font-size:13px;">{arrow} {q["change_pct"]:+.2f}%</span>'
                f"</div>"
            )
            text_rows.append(f"{label}: {price_str} ({arrow} {q['change_pct']:+.2f}%)")

        return ComponentResult(
            name=self.name, title=self.title,
            html="".join(html_rows), text="\n".join(text_rows),
            order=self.order,
        )

from __future__ import annotations

import html as html_lib

import requests

from heliograph.components.base import BaseComponent, ComponentResult

VIX_URL = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX"
FNG_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

# CNN's Fear & Greed rating strings → display color.
_FNG_COLORS = {
    "extreme fear": "#dc2626",
    "fear": "#ea580c",
    "neutral": "#6b7280",
    "greed": "#16a34a",
    "extreme greed": "#15803d",
}


def _fetch_vix() -> dict:
    """Return {price, prev_close, change, change_pct} for ^VIX from Yahoo Finance."""
    r = requests.get(
        VIX_URL,
        params={"interval": "1d", "range": "5d"},
        headers={"User-Agent": "Mozilla/5.0 heliograph"},
        timeout=20,
    )
    r.raise_for_status()
    meta = r.json()["chart"]["result"][0]["meta"]
    price = float(meta["regularMarketPrice"])
    prev = float(meta.get("chartPreviousClose") or meta.get("previousClose") or price)
    change = price - prev
    return {
        "price": price,
        "prev_close": prev,
        "change": change,
        "change_pct": (change / prev * 100) if prev else 0.0,
    }


def _fetch_fear_and_greed() -> dict:
    r = requests.get(
        FNG_URL,
        headers={
            "User-Agent": "Mozilla/5.0 heliograph",
            "Referer": "https://www.cnn.com/markets/fear-and-greed",
            "Accept": "application/json",
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json().get("fear_and_greed", {})


def _vix_color(price: float) -> str:
    if price < 15:
        return "#16a34a"  # calm
    if price < 20:
        return "#65a30d"
    if price < 25:
        return "#ca8a04"
    if price < 30:
        return "#ea580c"
    return "#dc2626"  # panic


class MarketFearComponent(BaseComponent):
    """Daily fear gauges: CBOE VIX + CNN Fear & Greed Index."""

    name = "market_fear"
    title = "Market Fear Gauges"
    order = 25

    def render(self) -> ComponentResult:
        # Either source can fail independently — render whatever we got.
        vix = None
        fng = None
        errors: list[str] = []
        try:
            vix = _fetch_vix()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"VIX: {exc}")
        try:
            fng = _fetch_fear_and_greed()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Fear & Greed: {exc}")

        html_parts: list[str] = []
        text_parts: list[str] = []

        if vix is not None:
            arrow = "▲" if vix["change"] >= 0 else "▼"
            color = _vix_color(vix["price"])
            html_parts.append(
                f'<div style="display:inline-block;margin-right:24px;vertical-align:top;">'
                f'<div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;">VIX</div>'
                f'<div style="font-size:24px;font-weight:700;color:{color};">{vix["price"]:.2f}</div>'
                f'<div style="font-size:12px;color:#6b7280;">{arrow} {vix["change"]:+.2f} ({vix["change_pct"]:+.2f}%) vs prev close</div>'
                f"</div>"
            )
            text_parts.append(
                f"VIX: {vix['price']:.2f} ({vix['change']:+.2f}, {vix['change_pct']:+.2f}% vs prev close {vix['prev_close']:.2f})"
            )

        if fng:
            score = float(fng.get("score", 0))
            rating = str(fng.get("rating", "unknown")).lower()
            color = _FNG_COLORS.get(rating, "#6b7280")
            week = fng.get("previous_1_week")
            month = fng.get("previous_1_month")
            html_parts.append(
                f'<div style="display:inline-block;vertical-align:top;">'
                f'<div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;">CNN Fear &amp; Greed</div>'
                f'<div style="font-size:24px;font-weight:700;color:{color};">{score:.0f} '
                f'<span style="font-size:13px;font-weight:500;">{html_lib.escape(rating)}</span></div>'
                + (
                    f'<div style="font-size:12px;color:#6b7280;">1w ago: {week:.0f} · 1m ago: {month:.0f}</div>'
                    if week is not None and month is not None
                    else ""
                )
                + "</div>"
            )
            text_parts.append(
                f"Fear & Greed: {score:.0f} ({rating})"
                + (f" — 1w {week:.0f}, 1m {month:.0f}" if week is not None and month is not None else "")
            )

        if errors:
            html_parts.append(
                '<div style="margin-top:8px;color:#9ca3af;font-size:11px;">'
                + html_lib.escape(" / ".join(errors))
                + "</div>"
            )
            text_parts.append("(" + " / ".join(errors) + ")")

        if not html_parts:
            html_parts.append('<p style="color:#9ca3af;">(No market data available)</p>')
            text_parts.append("(No market data available)")

        return ComponentResult(
            name=self.name,
            title=self.title,
            html="".join(html_parts),
            text="\n".join(text_parts),
            order=self.order,
            meta={"vix": vix, "fng_score": (fng or {}).get("score")},
        )

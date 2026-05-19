from __future__ import annotations

import platform
import shutil
from datetime import datetime

from heliograph.components.base import BaseComponent, ComponentResult


class SystemStatusComponent(BaseComponent):
    """Sample component that reports basic local-machine info."""

    name = "system_status"
    title = "System Status"
    order = 90

    def render(self) -> ComponentResult:
        total, used, free = shutil.disk_usage("/")
        gb = 1024 ** 3
        rows = [
            ("Host", platform.node()),
            ("OS", f"{platform.system()} {platform.release()}"),
            ("Python", platform.python_version()),
            ("Disk (free / total)", f"{free / gb:.1f} GB / {total / gb:.1f} GB"),
            ("Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ]
        rows_html = "".join(
            f'<tr><td style="padding:4px 12px 4px 0;color:#6b7280;">{k}</td>'
            f'<td style="padding:4px 0;color:#111827;"><code>{v}</code></td></tr>'
            for k, v in rows
        )
        html = f'<table style="border-collapse:collapse;font-size:14px;">{rows_html}</table>'
        text = "\n".join(f"{k}: {v}" for k, v in rows)
        return ComponentResult(
            name=self.name, title=self.title, html=html, text=text, order=self.order
        )

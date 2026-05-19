from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ComponentResult:
    name: str
    title: str
    html: str
    text: str = ""
    order: int = 100
    generated_at: datetime = field(default_factory=datetime.utcnow)
    meta: dict[str, Any] = field(default_factory=dict)


class BaseComponent(ABC):
    """A unit that produces one section of the daily email."""

    name: str = "unnamed"
    title: str = "Untitled"
    order: int = 100

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    @abstractmethod
    def render(self) -> ComponentResult:
        """Return the rendered section. Must be implemented by subclasses."""

    def safe_render(self) -> ComponentResult | None:
        try:
            return self.render()
        except Exception as exc:  # noqa: BLE001 — components must never crash the run
            return ComponentResult(
                name=self.name,
                title=self.title,
                html=f"<p><em>[{self.name}] failed: {exc}</em></p>",
                text=f"[{self.name}] failed: {exc}",
                order=self.order,
                meta={"error": str(exc)},
            )

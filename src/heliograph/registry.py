from __future__ import annotations

import importlib
from typing import Any

from heliograph.components.base import BaseComponent


class ComponentRegistry:
    """Loads components from config and instantiates them."""

    def __init__(self) -> None:
        self._components: list[BaseComponent] = []

    def register(self, component: BaseComponent) -> None:
        self._components.append(component)

    def load_from_config(self, components_config: list[dict[str, Any]]) -> None:
        for entry in components_config:
            if not entry.get("enabled", True):
                continue
            module_path = entry["module"]
            class_name = entry["class"]
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            self.register(cls(entry.get("config", {})))

    def render_all(self):
        results = []
        for comp in self._components:
            result = comp.safe_render()
            if result is not None:
                results.append(result)
        results.sort(key=lambda r: r.order)
        return results

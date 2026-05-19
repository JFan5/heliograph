from heliograph.components.daily_quote import DailyQuoteComponent
from heliograph.components.system_status import SystemStatusComponent
from heliograph.renderer import EmailRenderer


def test_daily_quote_is_deterministic_per_day():
    a = DailyQuoteComponent().render()
    b = DailyQuoteComponent().render()
    assert a.html == b.html
    assert a.name == "daily_quote"


def test_system_status_renders():
    result = SystemStatusComponent().render()
    assert "Host" in result.text


def test_renderer_combines_sections():
    sections = [
        DailyQuoteComponent().render(),
        SystemStatusComponent().render(),
    ]
    html, text = EmailRenderer().render(sections, title="Test")
    assert "<html" in html.lower()
    assert "Quote of the Day" in html
    assert "Test" in text


def test_safe_render_swallows_errors():
    from heliograph.components.base import BaseComponent

    class Boom(BaseComponent):
        name = "boom"
        title = "Boom"

        def render(self):
            raise RuntimeError("kaboom")

    result = Boom().safe_render()
    assert result is not None
    assert "kaboom" in result.text

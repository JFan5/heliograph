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


def test_skills_payload_parser():
    """The skills.sh page embeds a Next.js Flight payload — make sure we can pull it out."""
    import json
    from heliograph.components.skill_trending import parse_skills_html

    # Build the embedded payload the way Next.js Flight actually does:
    # an array of dicts dumped to JSON, then the whole HTML string has every
    # `"` escaped to `\"`. We simulate that with .replace('"', '\\"').
    skills_obj = [
        {"source": "vercel-labs/skills", "skillId": "find-skills",
         "name": "find-skills", "installs": 19256, "isOfficial": True},
        {"source": "degausai/wonda", "skillId": "wonda-cli",
         "name": "wonda-cli", "installs": 9000},
    ]
    embedded = json.dumps(skills_obj).replace('"', '\\"')
    fake_html = f'noise before \\"initialSkills\\":{embedded},\\"foo\\":1 noise after'

    skills = parse_skills_html(fake_html)
    assert len(skills) == 2
    assert skills[0]["name"] == "find-skills"
    assert skills[0]["installs"] == 19256
    assert skills[1]["source"] == "degausai/wonda"


def test_skills_payload_parser_missing():
    from heliograph.components.skill_trending import parse_skills_html
    assert parse_skills_html("nothing useful here") == []


def test_make_sender_unknown_provider(monkeypatch):
    from heliograph.sender import make_sender
    monkeypatch.setenv("EMAIL_PROVIDER", "carrier-pigeon")
    import pytest
    with pytest.raises(ValueError):
        make_sender()


def test_translate_arxiv_batch_parses_claude_output(monkeypatch):
    """Mock the claude CLI call and verify we parse a JSON response correctly."""
    from heliograph import summarizer

    fake_response = (
        "```json\n"
        '[{"title_zh":"中文标题1","summary_zh":"摘要1"},'
        '{"title_zh":"中文标题2","summary_zh":"摘要2"}]\n'
        "```"
    )
    monkeypatch.setattr(summarizer, "run_claude", lambda prompt, timeout=120: fake_response)

    out = summarizer.translate_arxiv_batch([
        {"title": "Foo", "summary": "Bar"},
        {"title": "Baz", "summary": "Qux"},
    ])
    assert out[0]["title_zh"] == "中文标题1"
    assert out[1]["summary_zh"] == "摘要2"


def test_translate_arxiv_batch_falls_back_on_garbage(monkeypatch):
    from heliograph import summarizer
    monkeypatch.setattr(summarizer, "run_claude", lambda prompt, timeout=120: "not json at all")
    out = summarizer.translate_arxiv_batch([{"title": "x", "summary": "y"}])
    assert out == [{}]


def test_translate_arxiv_batch_empty_input():
    from heliograph.summarizer import translate_arxiv_batch
    assert translate_arxiv_batch([]) == []

"""Thin wrapper around the `claude -p` CLI for batch summarization.

We invoke Claude once per batch (not once per item) so the cron job stays
fast and cheap. Failures are reported but never raise — callers should fall
back to whatever the original (untranslated) text was.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from typing import Any

DEFAULT_CLAUDE_BIN = "/home/ubuntu/.local/bin/claude"
DEFAULT_TIMEOUT = 120  # seconds

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class SummarizerError(RuntimeError):
    pass


def _resolve_claude_bin() -> str | None:
    env = os.environ.get("CLAUDE_BIN")
    if env and os.path.exists(env):
        return env
    if os.path.exists(DEFAULT_CLAUDE_BIN):
        return DEFAULT_CLAUDE_BIN
    return shutil.which("claude")


def _strip_fences(text: str) -> str:
    return _FENCE_RE.sub("", text).strip()


def run_claude(prompt: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Run `claude -p`, pipe prompt on stdin, return stdout. Raises on failure."""
    binary = _resolve_claude_bin()
    if not binary:
        raise SummarizerError("`claude` CLI not found; set CLAUDE_BIN or install it")
    proc = subprocess.run(
        [binary, "-p"],
        input=prompt,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise SummarizerError(
            f"claude -p exited {proc.returncode}: {proc.stderr.strip()[:400]}"
        )
    return proc.stdout


def translate_arxiv_batch(papers: list[dict[str, str]], timeout: int = DEFAULT_TIMEOUT) -> list[dict[str, str]]:
    """Translate & summarize a list of arXiv papers to Chinese in one Claude call.

    Each input dict must have keys: title, summary. Returns a list of dicts
    with keys: title_zh, summary_zh — same length and order as input.

    If Claude fails or the response is unparsable, returns a list of empty
    dicts so callers can transparently fall back to the original English.
    """
    if not papers:
        return []

    blocks = []
    for i, p in enumerate(papers, 1):
        title = (p.get("title") or "").strip().replace("\n", " ")
        abstract = (p.get("summary") or "").strip().replace("\n", " ")
        blocks.append(f"### Paper {i}\nTitle: {title}\nAbstract: {abstract}")

    prompt = (
        "你是一名学术论文摘要翻译助手。下面有若干篇 arXiv 论文。\n"
        "对每一篇，请输出：\n"
        '  - "title_zh": 中文翻译的标题（保留 LLM、RAG、CoT 等业内通用英文缩写）\n'
        '  - "summary_zh": 用 1-2 句中文（不超过 80 字）概括这篇论文做了什么、用了什么方法\n\n'
        "严格只输出一个 JSON 数组，顺序与下方论文顺序一致，不要任何额外文字、不要 markdown 代码块。\n"
        '例如：[{"title_zh":"...","summary_zh":"..."}, ...]\n\n'
        + "\n\n".join(blocks)
    )

    try:
        raw = run_claude(prompt, timeout=timeout)
    except (SummarizerError, subprocess.TimeoutExpired):
        return [{} for _ in papers]

    cleaned = _strip_fences(raw)
    # Find the first '[' so trailing/leading chatter never breaks parsing.
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1 or end < start:
        return [{} for _ in papers]
    try:
        parsed: Any = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return [{} for _ in papers]
    if not isinstance(parsed, list):
        return [{} for _ in papers]

    out: list[dict[str, str]] = []
    for i, _ in enumerate(papers):
        item = parsed[i] if i < len(parsed) and isinstance(parsed[i], dict) else {}
        out.append({
            "title_zh": str(item.get("title_zh", "")).strip(),
            "summary_zh": str(item.get("summary_zh", "")).strip(),
        })
    return out

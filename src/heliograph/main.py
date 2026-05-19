from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

import yaml
from dotenv import load_dotenv

from heliograph.registry import ComponentRegistry
from heliograph.renderer import EmailRenderer
from heliograph.sender import make_sender

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config.yaml"


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_email(config: dict) -> tuple[str, str, str]:
    registry = ComponentRegistry()
    registry.load_from_config(config.get("components", []))
    sections = registry.render_all()

    title_tmpl = config.get("email", {}).get("subject", "Heliograph · {date}")
    subject = title_tmpl.format(date=date.today().isoformat())

    renderer = EmailRenderer()
    html, text = renderer.render(sections, title=subject)
    return subject, html, text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="heliograph")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dry-run", action="store_true", help="Print email to stdout instead of sending")
    parser.add_argument("--out", type=Path, help="Write rendered HTML to file (debug)")
    args = parser.parse_args(argv)

    load_dotenv()
    config = load_config(args.config)
    subject, html, text = build_email(config)

    if args.out:
        args.out.write_text(html, encoding="utf-8")
        print(f"Wrote HTML preview to {args.out}")

    if args.dry_run:
        print("=" * 60)
        print(f"Subject: {subject}")
        print("=" * 60)
        print(text)
        return 0

    recipients = config.get("email", {}).get("to") or [os.environ["EMAIL_TO"]]
    sender = make_sender()
    sender.send(recipients, subject, html, text)
    provider = os.environ.get("EMAIL_PROVIDER", "mailgun")
    print(f"Sent '{subject}' to {recipients} via {provider}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

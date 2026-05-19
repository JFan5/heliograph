# Heliograph

> A daily signal from your own machine.

**Heliograph** is a small, modular dispatcher that assembles a daily email out of
pluggable *components*. Each component is a Python class that produces one
section — a quote, weather forecast, stock movements, news digest, server status,
whatever you wire up — and Heliograph stitches them into one nicely-formatted
HTML email and sends it.

The name comes from the 19th-century [heliograph](https://en.wikipedia.org/wiki/Heliograph):
a mirror device that flashed sunlight to send messages across miles. Same idea,
slightly different transport.

## Features

- 🧩 **Modular components** — each section is an isolated class; one failing
  component never breaks the whole email.
- 📨 **Plain SMTP** — works with Gmail, Outlook, Fastmail, or any SMTP server.
- 🎨 **Themed HTML template** — a clean, mobile-friendly default; swap in your own.
- 🛠 **Config-driven** — turn components on/off in `config.yaml` without touching code.
- 🧪 **Dry-run mode** — preview the rendered email before you actually send it.

## Quickstart

```bash
# 1. Create a venv and install
python -m venv .venv && source .venv/bin/activate
pip install -e .

# 2. Configure secrets
cp .env.example .env
# ...edit .env with your SMTP creds and recipient

# 3. Preview without sending
heliograph --dry-run

# 4. Render to an HTML file to eyeball it
heliograph --dry-run --out preview.html

# 5. Send for real
heliograph
```

## Project layout

```
heliograph/
├── config.yaml                       # which components are enabled
├── pyproject.toml
├── requirements.txt
├── .env.example
└── src/heliograph/
    ├── main.py                       # CLI entrypoint
    ├── registry.py                   # loads components from config
    ├── renderer.py                   # Jinja2 -> HTML
    ├── sender.py                     # SMTP transport
    ├── components/
    │   ├── base.py                   # BaseComponent + ComponentResult
    │   ├── daily_quote.py            # example component
    │   └── system_status.py          # example component
    └── templates/
        └── email.html
```

## Writing a new component

Components are subclasses of `BaseComponent`. Implement `render()` and return a
`ComponentResult`:

```python
from heliograph.components.base import BaseComponent, ComponentResult

class WeatherComponent(BaseComponent):
    name = "weather"
    title = "Today's Weather"
    order = 20  # lower = higher in the email

    def render(self) -> ComponentResult:
        # ...fetch your data...
        html = "<p>☀️ 22°C, clear</p>"
        text = "Sunny, 22C, clear"
        return ComponentResult(
            name=self.name, title=self.title, html=html, text=text, order=self.order
        )
```

Then enable it in `config.yaml`:

```yaml
components:
  - name: weather
    module: heliograph.components.weather
    class: WeatherComponent
    enabled: true
    config:
      city: "San Francisco"
```

If `render()` raises, Heliograph catches the exception and inlines a small error
notice in that component's slot — the rest of the email still ships.

## Scheduling

Heliograph itself does not run a daemon. Wire it up with whatever scheduler
your machine already has. `scripts/run.sh` is the cron-friendly entrypoint —
it sources `.env`, runs the dispatcher, and prints a timestamp banner.

### Cron (with timezone gating)

Ubuntu's `cron` doesn't honor per-user `CRON_TZ`, so `run.sh` self-gates: by
default it only sends when the current **US/Eastern** hour is `07`. Tell cron
to fire it at the two UTC times that span both EDT and EST:

```cron
# crontab -e — daily 7 AM US/Eastern, DST-safe
0 11,12 * * * /home/ubuntu/heliograph/scripts/run.sh >> /home/ubuntu/heliograph/logs/heliograph.log 2>&1
```

For other timezones, edit the `ET_HOUR != "07"` check at the top of
`scripts/run.sh`, or set `HELIOGRAPH_SKIP_TIME_CHECK=1` and pick a different
UTC hour in cron directly.

### Manual / test runs

```bash
./scripts/run.sh --force --dry-run    # render to stdout, don't send
./scripts/run.sh --force              # actually send right now
```

## License

MIT

#!/usr/bin/env python3
"""Create an editable HTML/CSS scaffold for a designed brochure PDF."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


THEMES = {
    "refined": {
        "bg": "#F7F2EA",
        "ink": "#161616",
        "muted": "#6F6A62",
        "accent": "#9B6A3F",
        "accent2": "#1F4E5F",
        "paper": "#FFFDF8",
    },
    "tech": {
        "bg": "#F3F7F8",
        "ink": "#101820",
        "muted": "#5B6670",
        "accent": "#007A7A",
        "accent2": "#D4552D",
        "paper": "#FFFFFF",
    },
    "warm": {
        "bg": "#FAF3EF",
        "ink": "#211B18",
        "muted": "#78685F",
        "accent": "#B94E35",
        "accent2": "#2F6F5E",
        "paper": "#FFFDFC",
    },
    "editorial": {
        "bg": "#F5F5F0",
        "ink": "#111111",
        "muted": "#676767",
        "accent": "#C33A2B",
        "accent2": "#1D5B84",
        "paper": "#FFFFFF",
    },
}


def write_file(path: Path, text: str, force: bool) -> None:
    if path.exists() and not force:
        raise SystemExit(f"{path} already exists. Re-run with --force to overwrite it.")
    path.write_text(text, encoding="utf-8")


def build_html(title: str, subtitle: str) -> str:
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <main class="brochure">
    <section class="page cover">
      <div class="mark">BROCHURE</div>
      <div class="cover-copy">
        <p class="eyebrow">Brand / Product / Service</p>
        <h1>{safe_title}</h1>
        <p class="dek">{safe_subtitle}</p>
      </div>
      <div class="cover-visual">
        <span>Replace with hero image</span>
      </div>
      <footer>01</footer>
    </section>

    <section class="page opener">
      <div>
        <p class="eyebrow">Positioning</p>
        <h2>Turn the central promise into one memorable sentence.</h2>
      </div>
      <p class="lead">Use this page to explain who the brochure is for, what problem it solves, and why the offer matters now. Keep it specific and calm.</p>
      <footer>02</footer>
    </section>

    <section class="page feature-page">
      <p class="eyebrow">Highlights</p>
      <h2>Three reasons this offer stands out.</h2>
      <div class="feature-grid">
        <article><span>01</span><h3>Outcome</h3><p>Describe the customer result in plain language.</p></article>
        <article><span>02</span><h3>Method</h3><p>Describe the capability, process, or technology.</p></article>
        <article><span>03</span><h3>Proof</h3><p>Add evidence, metric, certification, case, or partner signal.</p></article>
      </div>
      <footer>03</footer>
    </section>

    <section class="page split">
      <div class="image-slot">Product / service visual</div>
      <div class="split-copy">
        <p class="eyebrow">Detail</p>
        <h2>Use a concrete page for product, service, or package details.</h2>
        <ul>
          <li>Replace bullets with practical specs or deliverables.</li>
          <li>Keep every line useful for a buyer or decision maker.</li>
          <li>Add captions to images so visuals carry meaning.</li>
        </ul>
      </div>
      <footer>04</footer>
    </section>

    <section class="page proof">
      <p class="eyebrow">Proof</p>
      <blockquote>"A short customer quote, metric, or proof statement belongs here."</blockquote>
      <div class="metric-row">
        <div><strong>98%</strong><span>Metric label</span></div>
        <div><strong>30d</strong><span>Timeline</span></div>
        <div><strong>24/7</strong><span>Service scope</span></div>
      </div>
      <footer>05</footer>
    </section>

    <section class="page closing">
      <div>
        <p class="eyebrow">Contact</p>
        <h2>End with one clear next step.</h2>
      </div>
      <div class="contact-panel">
        <p>Company name</p>
        <p>website.example.com</p>
        <p>email@example.com</p>
        <p>+00 0000 0000</p>
      </div>
      <footer>06</footer>
    </section>
  </main>
</body>
</html>
"""


def build_css(theme: dict[str, str], page_format: str) -> str:
    if page_format == "letter":
        page_size = "letter"
        width = "216mm"
        height = "279mm"
    else:
        page_size = "A4"
        width = "210mm"
        height = "297mm"

    return f""":root {{
  --bg: {theme["bg"]};
  --paper: {theme["paper"]};
  --ink: {theme["ink"]};
  --muted: {theme["muted"]};
  --accent: {theme["accent"]};
  --accent-2: {theme["accent2"]};
  --margin: 18mm;
  --radius: 6px;
}}

@page {{
  size: {page_size};
  margin: 0;
}}

* {{
  box-sizing: border-box;
}}

body {{
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: "Microsoft YaHei", "Noto Sans CJK SC", "Source Han Sans SC", Arial, sans-serif;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}

.brochure {{
  width: {width};
  margin: 0 auto;
}}

.page {{
  position: relative;
  width: {width};
  height: {height};
  overflow: hidden;
  padding: var(--margin);
  background: var(--paper);
  page-break-after: always;
}}

.page footer {{
  position: absolute;
  right: var(--margin);
  bottom: 11mm;
  color: var(--muted);
  font-size: 9px;
  letter-spacing: 0.08em;
}}

.eyebrow,
.mark {{
  color: var(--accent);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}}

h1,
h2,
h3,
p {{
  margin: 0;
}}

h1 {{
  max-width: 128mm;
  font-size: 46px;
  line-height: 0.98;
  letter-spacing: 0;
}}

h2 {{
  max-width: 142mm;
  font-size: 31px;
  line-height: 1.06;
  letter-spacing: 0;
}}

h3 {{
  font-size: 17px;
  line-height: 1.2;
}}

p,
li {{
  color: var(--muted);
  font-size: 12px;
  line-height: 1.7;
}}

.cover {{
  display: grid;
  grid-template-rows: auto 1fr auto;
  background:
    linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.12)),
    var(--bg);
}}

.cover-copy {{
  align-self: end;
  z-index: 2;
}}

.dek {{
  max-width: 92mm;
  margin-top: 10mm;
  color: var(--ink);
  font-size: 15px;
}}

.cover-visual {{
  position: absolute;
  right: -18mm;
  bottom: 32mm;
  width: 112mm;
  height: 142mm;
  display: grid;
  place-items: center;
  border: 1px solid rgba(0,0,0,0.08);
  background: linear-gradient(145deg, var(--accent-2), var(--accent));
  color: rgba(255,255,255,0.78);
  font-size: 12px;
}}

.opener {{
  display: grid;
  align-content: center;
  gap: 22mm;
}}

.lead {{
  max-width: 135mm;
  color: var(--ink);
  font-size: 17px;
  line-height: 1.65;
}}

.feature-page {{
  display: grid;
  align-content: center;
  gap: 14mm;
}}

.feature-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 7mm;
}}

.feature-grid article {{
  min-height: 64mm;
  padding: 9mm;
  border-top: 2px solid var(--accent);
  background: color-mix(in srgb, var(--bg) 55%, white);
}}

.feature-grid span {{
  color: var(--accent);
  font-size: 11px;
  font-weight: 700;
}}

.feature-grid h3 {{
  margin-top: 14mm;
  margin-bottom: 5mm;
}}

.split {{
  display: grid;
  grid-template-columns: 1fr 0.88fr;
  gap: 12mm;
  align-items: center;
}}

.image-slot {{
  height: 196mm;
  display: grid;
  place-items: center;
  background: linear-gradient(140deg, var(--accent-2), var(--bg));
  color: rgba(255,255,255,0.82);
  font-size: 12px;
}}

.split-copy ul {{
  margin: 10mm 0 0;
  padding-left: 4mm;
}}

.proof {{
  display: grid;
  align-content: center;
  gap: 20mm;
  background: var(--ink);
  color: white;
}}

.proof .eyebrow,
.proof footer {{
  color: color-mix(in srgb, var(--accent) 72%, white);
}}

blockquote {{
  width: 150mm;
  margin: 0;
  color: white;
  font-size: 34px;
  line-height: 1.12;
  letter-spacing: 0;
}}

.metric-row {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8mm;
}}

.metric-row div {{
  border-top: 1px solid rgba(255,255,255,0.28);
  padding-top: 6mm;
}}

.metric-row strong {{
  display: block;
  color: white;
  font-size: 28px;
}}

.metric-row span {{
  color: rgba(255,255,255,0.68);
  font-size: 10px;
}}

.closing {{
  display: grid;
  grid-template-columns: 1fr 0.72fr;
  align-items: end;
  gap: 14mm;
}}

.contact-panel {{
  padding: 10mm;
  background: var(--bg);
  border-left: 3px solid var(--accent);
}}

.contact-panel p + p {{
  margin-top: 4mm;
}}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--title", default="Beautiful Brochure")
    parser.add_argument("--subtitle", default="A concise promise for the audience goes here.")
    parser.add_argument("--theme", choices=sorted(THEMES), default="refined")
    parser.add_argument("--format", choices=["a4", "letter"], default="a4")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "assets").mkdir(exist_ok=True)
    (out / "renders").mkdir(exist_ok=True)

    brief = {
        "title": args.title,
        "subtitle": args.subtitle,
        "theme": args.theme,
        "format": args.format,
        "pages": 6,
        "notes": [
            "Replace scaffold copy with real brochure content.",
            "Keep final images local under assets/ before PDF export.",
            "Render the final PDF to PNG pages and inspect before delivery.",
        ],
    }

    write_file(out / "brief.json", json.dumps(brief, ensure_ascii=False, indent=2), args.force)
    write_file(out / "index.html", build_html(args.title, args.subtitle), args.force)
    write_file(out / "styles.css", build_css(THEMES[args.theme], args.format), args.force)
    print(f"Created brochure scaffold: {out}")


if __name__ == "__main__":
    main()

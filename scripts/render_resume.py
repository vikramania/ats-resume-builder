#!/usr/bin/env python3
"""Render resume.json (or a standalone .html) to a pixel-accurate PDF, then
save PNG previews of every page for visual verification.

Usage:
    python3 scripts/render_resume.py resume.json output.pdf
    python3 scripts/render_resume.py resume.html output.pdf

Requires a local Chrome/Chromium install; set CHROME_PATH to override the
default lookup.
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "templates"

CHROME_CANDIDATES = [
    os.environ.get("CHROME_PATH"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser",
    shutil.which("chrome"),
    shutil.which("chromium"),
]


def find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        if c and Path(c).exists():
            return c
    raise FileNotFoundError(
        "No Chrome/Chromium found. Set CHROME_PATH env var to the binary path."
    )


def bold_filter(text: str) -> str:
    """Escape HTML, then turn **bold** markers into <strong> tags."""
    escaped = html.escape(text or "")
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)


def render_html_from_json(data_path: Path) -> str:
    data = json.loads(data_path.read_text())
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)
    env.filters["bold"] = bold_filter
    template = env.get_template("resume_template.html")
    return template.render(data=data)


def render_to_pdf(html_path: Path, pdf_path: Path):
    chrome = find_chrome()
    subprocess.run(
        [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--allow-file-access-from-files",
            "--virtual-time-budget=8000",
            f"--print-to-pdf={pdf_path}",
            "--no-pdf-header-footer",
            html_path.as_uri(),
        ],
        check=True,
        capture_output=True,
    )


def save_png_previews(pdf_path: Path):
    try:
        from pdf2image import convert_from_path
    except ImportError:
        print("note: pdf2image not installed, skipping PNG previews", file=sys.stderr)
        return []
    pages = convert_from_path(str(pdf_path), dpi=150)
    out_paths = []
    for i, page in enumerate(pages, 1):
        out = pdf_path.with_name(f"{pdf_path.stem}-page{i}.png")
        page.save(out)
        out_paths.append(out)
    return out_paths


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path, help="resume.json or a standalone .html file")
    ap.add_argument("output", type=Path, help="Output PDF path")
    ap.add_argument("--keep-html", action="store_true", help="Don't delete the intermediate HTML file")
    args = ap.parse_args()

    if not args.source.exists():
        print(f"error: {args.source} not found", file=sys.stderr)
        sys.exit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)

    if args.source.suffix == ".json":
        html_out = render_html_from_json(args.source)
        html_path = args.output.with_suffix(".html")
        html_path.write_text(html_out)
        generated_html = True
    elif args.source.suffix in (".html", ".htm"):
        html_path = args.source
        generated_html = False
    else:
        print("error: source must be .json or .html", file=sys.stderr)
        sys.exit(1)

    render_to_pdf(html_path, args.output)
    print(f"wrote {args.output}")

    previews = save_png_previews(args.output)
    for p in previews:
        print(f"preview: {p}")

    if generated_html and not args.keep_html:
        html_path.unlink()


if __name__ == "__main__":
    main()

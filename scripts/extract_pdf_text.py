#!/usr/bin/env python3
"""Extract text from a resume or LinkedIn-exported PDF, preserving column/row order.

LinkedIn's "Save to PDF" export uses a multi-column layout that naive text
extraction (and sometimes a quick visual read) can scramble — this uses
pdfplumber's word-position data to rebuild reading order top-to-bottom,
left-to-right within each page, which handles that layout correctly.

Usage:
    python3 scripts/extract_pdf_text.py path/to/file.pdf
    python3 scripts/extract_pdf_text.py path/to/file.pdf --out extracted.txt
"""
import argparse
import sys
from pathlib import Path

import pdfplumber


def extract(pdf_path: Path) -> str:
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
            if not words:
                continue
            # Bucket words into lines by y-position (rounded), then sort each
            # line left-to-right — this is what keeps two-column LinkedIn
            # layouts from interleaving mid-sentence.
            lines = {}
            for w in words:
                y = round(w["top"] / 3) * 3  # 3pt tolerance bucket
                lines.setdefault(y, []).append(w)
            page_lines = []
            for y in sorted(lines):
                row = sorted(lines[y], key=lambda w: w["x0"])
                page_lines.append(" ".join(w["text"] for w in row))
            pages_text.append(f"--- page {i} ---\n" + "\n".join(page_lines))
    return "\n\n".join(pages_text)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", type=Path, help="Path to the resume or LinkedIn-export PDF")
    ap.add_argument("--out", type=Path, default=None, help="Write to this file instead of stdout")
    args = ap.parse_args()

    if not args.pdf.exists():
        print(f"error: {args.pdf} not found", file=sys.stderr)
        sys.exit(1)

    text = extract(args.pdf)
    if args.out:
        args.out.write_text(text)
        print(f"wrote {len(text)} chars to {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()

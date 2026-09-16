# ATS Resume Builder

A Claude Code skill + working pipeline for reviewing and building ATS-friendly resumes: intake from an existing resume or a LinkedIn-exported PDF, a Markdown feedback report, and (on request) a pixel-accurate PDF in the established Times New Roman / structured-section format.

## What's here

- `.claude/skills/ats-resume-builder/SKILL.md` — the skill itself. Drop this repo's `.claude/skills/ats-resume-builder` folder into any project's `.claude/skills/` (or point Claude Code at this repo) to make the skill available.
- `scripts/extract_pdf_text.py` — pulls text out of a resume or LinkedIn "Save to PDF" export in correct reading order, even for multi-column layouts.
- `scripts/render_resume.py` — fills `templates/resume_template.html` from a `resume.json` file (or renders a standalone HTML file directly), prints to PDF via headless Chrome, and saves a PNG per page for visual QA.
- `templates/resume_template.html` — the Jinja2 template implementing the format spec. Schema documented in the HTML comment at the top of the file.
- `templates/feedback_template.md` — the rubric used for the review/feedback workflow.
- `examples/resume.json` — a filled example you can render immediately to see the pipeline work.

## Quick start

```bash
pip install -r requirements.txt
python3 scripts/render_resume.py examples/resume.json /tmp/example-resume.pdf
```

This writes `/tmp/example-resume.pdf` plus `/tmp/example-resume-page1.png` (etc.) for a quick visual check.

To extract text from a LinkedIn export or an existing resume PDF:

```bash
python3 scripts/extract_pdf_text.py ~/Downloads/Profile.pdf
```

## How it's meant to be used

Two entry points, both driven by the skill (see `SKILL.md` for the full workflow):

1. **"Review my resume"** — Claude reads your resume (and LinkedIn export, and a target job description if you have one), scores it against `templates/feedback_template.md`'s rubric, and writes a Markdown feedback report with concrete quoted findings and fixes. Nothing else happens unless you ask.
2. **"Build/update my resume"** — Claude drafts content into a Markdown file first (iterated with you until it's final), converts it into `resume.json`, and only then renders the PDF via `render_resume.py`, verifying the output visually before sending it.

Metrics the candidate hasn't supplied are never invented — they go in as `[X]` placeholders with a note on exactly what's missing.

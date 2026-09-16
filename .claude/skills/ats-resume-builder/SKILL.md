---
name: ats-resume-builder
description: "Use when drafting, reformatting, reviewing, or scoring a resume against the ATS-friendly template format (Times New Roman, structured sections, PDF-only output). Handles intake from an existing resume file, a LinkedIn-exported PDF, or certificates; produces a Markdown feedback report first, then (on request) a finished PDF."
---

# ATS-Friendly Resume Builder

Captures the resume format, content conventions, feedback rubric, and build pipeline established for Adithya's and Vaishnavi's resumes, so future resume work — a new candidate, a content update, a review pass, or regenerating a PDF — skips re-deriving the format from scratch.

This skill has two entry points depending on what the user asks for:

- **"Review/score my resume"** &rarr; run the **Feedback workflow** and stop at the Markdown feedback report.
- **"Build/update my resume"** &rarr; run the **Draft workflow**, which folds in feedback findings as you go, and only reaches PDF once the user confirms content is final.

Both workflows share the same intake step and the same Skills Section / formatting rules below.

## Intake (shared by both workflows)

1. **Gather content first.** Pull from the candidate's existing resume (if any), their LinkedIn profile, and any certificates.
   - For LinkedIn: never scrape the live LinkedIn site with a browser tool. Ask the user for the candidate's **exported LinkedIn profile PDF** (LinkedIn's own "Save to PDF" export from their profile page — Profile &rarr; "Resources" / "More" &rarr; Save to PDF) and read that PDF directly for work history, skills, and details. Live browser scraping of LinkedIn has repeatedly been slow/unreliable and is explicitly not the workflow here.
   - If the PDF is a multi-column or dense LinkedIn export and the Read tool's extraction looks garbled or out of order, fall back to `scripts/extract_pdf_text.py <file.pdf>` (uses `pdfplumber`, which handles column layout better) and read its output instead.
   - For certification dates, read the actual certificate PDF to extract the exact issue date — never guess or approximate.
2. Note every number/metric the candidate's source material does NOT already state explicitly. These become `[X]` placeholders later — never invent a number.

## Feedback workflow

Use when the user wants a review/critique/ATS-score of an existing resume, before (or instead of) touching the format.

1. Read the candidate's current resume (PDF, DOCX text, or Markdown — whatever they hand you) plus any LinkedIn export/JD they mention.
2. Score it against `templates/feedback_template.md`'s rubric sections: ATS parseability, Skills Section hygiene (see rules below), quantification gaps, formatting/structure, content gaps against the target format spec, and (if a target job description was provided) keyword alignment.
3. Fill in `templates/feedback_template.md` with concrete findings — quote the actual offending line, don't describe it abstractly. Every finding needs a suggested fix, not just a criticism.
4. Write the completed report to the candidate's folder as `<candidate>-resume-feedback.md` (or update it in place on a re-review) and tell the user directly what you'd change.
5. **Do not touch the PDF or move to the Draft workflow unless the user asks you to act on the feedback.** The feedback report is a complete deliverable on its own.

## Draft workflow

1. **Draft in Markdown first, PDF last.** Always produce a `.md` draft as the intermediate, reviewable format before touching PDF/HTML. Put the page/format spec (below) as an HTML comment block at the top of that markdown file, so the spec travels with the content and survives file handoffs. This markdown draft is itself a real deliverable — write it to disk (and into the candidate's resume folder, if one is connected), not just discussed inline.
2. **Iterate on the markdown via user review** (inline review comments or direct chat instructions) until content is finalized. Edit the SAME draft file in place — do not create v2/v3/etc. files unless the user explicitly asks for a new version. Expect rounds of feedback like: tightening skills to only real tools/libraries/frameworks (see Skills Section rules), converting prose into dated bullet points for certifications/achievements, adding an italic Industry line under each client/project, quantifying impact bullets with `[X]` placeholders for numbers the candidate must supply.
3. **Only after the user confirms content is final**, render to PDF via `scripts/render_resume.py` (HTML+CSS+headless-Chromium pipeline, see below).
4. **Verify the rendered PDF visually** before sending: `scripts/render_resume.py` already does the PNG conversion step for you — read the PNGs it writes with the Read tool and check for page overflow, orphaned section headers, and missing bullet markers (see Known Pitfalls) before calling the job done.

## Page / Format Specification (put this as an HTML comment at the top of the .md draft)

- Page size: A4 | Margins: ~0.6–0.8in
- Font family: Times New Roman (serif) throughout
- Name (header): ~19–20pt, Bold, Centered
- Contact line: ~9.7–10pt, Centered, icon-prefixed (📧 📱 🔗 📍 or ✉ ☎), "|" separated
- Section headings: ALL CAPS, bold, left-aligned, underlined with a horizontal rule below
- Body text: 10–10.5pt, single line spacing, justified paragraphs / left-aligned bullets
- Job entry header: bold company + role on the left, bold date range on the right, same line (flex/tab-stop layout)
- Bullets: "•" for achievements/experience; sub-bullets under a client/project are plain
- Client/project block order: underlined client name (own line) → italic "Industry: ..." line → italic "Tech: ..." line → bullet points
- Bold used inline for key metrics/results
- Education row: bold institution + date range right-aligned, degree/CGPA plain below
- Certifications: bullet points, cert name bold, date right-aligned where known, undated certs listed plain without a date
- Achievements: bullet points, award name bold with year inline, description after a colon
- Skills: grouped by category, never one flat list — each category on its own line as `**Category Name:** item, item, item`

`templates/resume_template.html` already implements this spec as a Jinja2 template driven by a `resume.json` data file (see its header comment for the schema) — prefer filling that data file over hand-writing HTML, unless the candidate's structure genuinely doesn't fit the schema.

## Skills Section rules (recurring point of feedback — apply from the start)

- Every item listed must be an actual tool, library, framework, or package (e.g., Snowflake, Apache Airflow, DBT, Power BI). Never list capability or practice phrases as if they were skills (e.g., "Workflow Automation & Orchestration", "Pipeline Optimization", "Data Quality Assurance", "Cloud Data Migration" are NOT acceptable line items — cut them or fold the real tool behind them into its proper category).
- Group into meaningful categories the candidate's domain actually uses — e.g., Programming Languages; Big Data & Distributed Processing; Transformation & Orchestration; Cloud & Data Platforms; Source Systems & API Integrations; Dev Tools. Category names/order can be renamed or reordered per candidate.
- If the candidate uses AI coding tools (Claude Code, Cursor, GitHub Copilot, etc.), add a small dedicated category for it — this signals "AI-ready" to recruiters and has been explicitly requested before.
- Drop redundant or overly-basic entries the candidate doesn't want emphasized (e.g., a qualifier like "(Basic)" next to a tool, or a database they no longer want listed) — always confirm removals against the candidate's own instructions, don't infer it.
- Fix vague sub-items into their real components (e.g., "OneLake, Lakehouse" as standalone items should fold into a parent platform line like "Microsoft Fabric (OneLake, Lakehouse architecture)" since they're sub-concepts, not separate tools).

## Build Pipeline: Markdown → PDF

Use HTML + CSS + headless Chromium for pixel-accurate control — do not use docx/python-docx, the user has explicitly rejected Word-based output for this workflow.

1. Convert the finalized markdown content into `resume.json` (schema documented at the top of `templates/resume_template.html`) or a standalone HTML file directly if the structure doesn't fit the schema.
2. Render to PDF: `python3 scripts/render_resume.py <resume.json|resume.html> <output.pdf>` — this fills the Jinja2 template (if given JSON), calls headless Chrome with the flags the pitfalls below require, and writes the PDF.
3. `scripts/render_resume.py` also writes `<output>-pageN.png` previews next to the PDF — read them with the Read tool to verify before delivering.
4. Deliver only the PDF via SendUserFile (never send the intermediate HTML as a deliverable). If a local folder is connected, save the PDF into the candidate's resume folder per the standard file-delivery flow.

### CSS notes / known pitfalls (already handled in `templates/resume_template.html`, keep in mind if you hand-edit HTML)

- **Orphaned section headers**: apply `page-break-after: avoid` to section headings and job/client header lines, `page-break-inside: avoid` on tightly-coupled blocks (e.g., wrap Certifications+Achievements in a `.keep-together` div) to stop a header from stranding alone at a page break.
- **Bullets disappearing**: `display:flex` directly on an `<li>` suppresses Chromium's `::marker` bullet rendering. Fix: keep the `<li>` as a normal list item and nest a `<div class="crow" style="display:flex; justify-content:space-between">` inside it for any left/right-aligned content (e.g., cert name + date).
- Keep margins/font-size/line-height tight enough to fit one page for a typical 3–6 year experience resume; adjust `line-height` (~1.2) and section margins (not font size) first if content slightly overflows.

## File & delivery conventions

- Default to editing the existing draft file in place rather than creating new files, unless the user asks for a new version explicitly.
- Final format is always PDF. Never deliver `.docx`.
- When a local folder is connected, the finished PDF and the markdown draft both belong in that candidate's resume folder, not left only in the chat.
- Numbers/metrics the candidate hasn't provided go in as bold `[X]` placeholders in the markdown draft, with a note explaining exactly what needs filling in (what the number represents, with a worked example) — never invent metrics.

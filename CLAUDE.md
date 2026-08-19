# CLAUDE.md — Bergmann-CV

Single-source CV system for Michael F Bergmann. One canonical data file generates every CV format.

## Architecture

```
cv.yaml  ──►  build.py  ──►  output/*.md  ──►  convert.sh  ──►  output/*.docx + *.pdf
prose/sshrc-prose.md ─┘ (appended to the SSHRC doc)      └─ run by CI, or by hand
```

Four documents: **Complete** (public CV), **OCGS** (follows the official OCGS template sections a–i; funding renders as tables from the structured fields on funding entries; publications categorized via `ocgs_category` with a life-time count summary), **SSHRC-Contributions** (six-year window + prose), and **FullRecord** (the "full life file": everything, including `archive_*` sections — the complete historical design/production record that stays out of the other three).

Entry sections render as two-column tables (bold date | item). The borders are removed by `assets/pdf-style.tex` (PDF, via pandoc `-H`) and `assets/reference.docx` (docx, via `--reference-doc`; its Table style has no borders and a flush-left first column). Column widths come from the dash ratio in the pipe-table separator row that `build.py` emits (~24/76).

## Rules

1. **Edit `cv.yaml` only** for CV content. Never edit files in `output/` — they are overwritten on every build.
2. **One entry per event.** New talk, credit, grant, or committee → one line in the correct section of `cv.yaml`, most sections sorted reverse chronological (build.py preserves file order; keep newest first).
3. **Dates**: `YYYY`, `YYYY-MM`, or `YYYY-MM-DD`; `end: present` for ongoing roles.
4. **Flags**: `refereed: true` (anonymous peer review of the full work), `other_refereed: true` (reviewed conference presentations/posters), `sshrc: true` (output of SSHRC funding — renders as `*` in the SSHRC doc), `sshrc_exclude: true` (forthcoming entry kept out of the SSHRC doc, e.g. drafts not yet submitted). No flag → non-refereed.
4a. **Internal notes go in YAML comments** (`# TODO: ...` on their own line), never inside `text:` strings — anything in a string is rendered in every CV. Public-facing status (e.g. "in press") goes in `status:`; editor reminders go in comments.
5. **SSHRC prose** (significance statements, training narrative, relevant experience) lives in `prose/sshrc-prose.md` as a **generic base**: HTML-comment placeholders mark where each application's specific tie-ins go (comments don't render). The list sections regenerate automatically with a rolling six-year filter; the prose does not — tailor it before each submission.
5a. **Archival credits** (pre-2019 design/lighting/direction/film/systems work, early employment) go in the `archive_*` sections and appear only in the FullRecord document. New historical finds go there, not in the main sections.
6. After editing, run `python3 build.py` locally (needs `pyyaml`) or just push — CI rebuilds and commits `output/`.
7. **Fonts and pandoc flags live in `convert.sh`**, which CI and local builds both call, so a locally built PDF matches the committed one. Change a font there, not in the workflow.

## Style

Canadian English (colour, centre); Oxford comma; semicolons over em-dashes. Citation strings follow the patterns already in `cv.yaml` — full bibliographic details, co-authors in original order, roles specified for co-authored work.

## Known TODOs (search `TODO` in cv.yaml)

- Page count and status confirmation for the transcript Verlag chapter (*Robots and Other Artificial Agents on Stage*)

## Facts that trip people up

- Eldon Elder Fellowship: 2012–2014 (held throughout the MFA)
- Faculty Tenure Committee: joined December 2024
- BFA: coursework December 2010, graduated May 2011 — degree year is 2011
- *Nuptials*: official release date is 2026-02-13 (Freestyle Digital Media); design work 2018; award 2022
- Michael is a PhD student (not yet ABD) — not "candidate"
- Co-UPD role ended July 2023
- LTEF "Creative Laboratory Project" grant: 2018 (funding period 2017/1–2018/1 per CCV); the old "2016" note was unfounded — no source says 2016
- Eldon Elder Fellowship amount: $40,000 USD; the CCV's "50,000" is the CAD equivalent, not a conflict
- Augmented Symphony author order: Bouchard, Cristiá, Robert, Bergmann (Bergmann last)
- UKAI Projects board: April 2025 (Michael confirmed; CV 2025.docx's "2024" is wrong)
- Rough Draft "Performance Art: New Magic" (2017) is solo-authored; the CCV's co-author listing is wrong
- Gold Medal committee: 2020–2023; PhD expected 2027; Watchout wording stays as-is (all confirmed July 2026)
- Sabbaticals: Winter 2025 and Winter 2026 — teaching gaps in those terms are expected, not omissions
- The New York City course ran as a Spring/Summer overload in both 2025 and 2026 (same course; the 2025 offering may have used a different course code than FCD 230)
- "Beyond Tools: Reimaging Technology…" (PQ Symposium 2024): "Reimaging" is what appeared on the presentation — do not "correct" to "Reimagining"
- The Design + Technology Lab Associate Director role is deliberately not listed (Michael's choice, July 2026)

## For SSHRC submissions

The SSHRC document is built in Times New Roman 12pt, so a locally built PDF is submission-ready as generated — the old "open the .docx in Word and reset the font" step is no longer needed. CI has no Times New Roman (it is not redistributable), so the committed PDF falls back to Liberation Serif, a metric clone: identical metrics, same line breaks and page count, slightly different letterforms. Build locally with `./convert.sh Bergmann-SSHRC-Contributions` for the real thing.

Margins (0.75") and page size (US Letter) are already compliant. The contributions attachment has a **5-page limit and currently sits at exactly 5** — check the page count after any addition, because the next entry is what pushes it over.

The other three documents use Atkinson Hyperlegible, which is a deliberate legibility choice and not something to "fix" back to a serif.

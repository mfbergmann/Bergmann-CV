---
name: bergmann-cv
description: Maintain and generate Michael F Bergmann's CV from the single-source Bergmann-CV repo (cv.yaml → build.py → four documents). Use this whenever a task touches his CV or academic record in any way — adding a talk, publication, grant, award, course, committee, residency, supervision, or design credit; correcting a date or citation; rebuilding or exporting the Complete, OCGS, SSHRC-Contributions, or FullRecord documents; preparing a SSHRC or OCGS submission; or cutting a short, tailored CV for a job application, residency, fellowship, grant, award nomination, bio, or speaker packet. Trigger it even when he doesn't name the repo — "add this to my CV", "I gave a talk at X", "I need a two-page CV for this residency", "update my publications", "make me an artist CV", and "what does my CV say about Y" all belong here. Also use it before answering questions about his record, so the answer comes from cv.yaml rather than memory.
---

# Bergmann-CV

One YAML file holds the record. Everything else is generated. The value of this
system is that a fact gets entered once, correctly, and then appears in every
document that should carry it — which only holds if edits go into `cv.yaml` and
nowhere else.

```
cv.yaml ──► build.py ──► output/*.md ──► GitHub Action ──► output/*.docx + *.pdf
prose/sshrc-prose.md ─┘ (appended to the SSHRC doc only)
```

`CLAUDE.md` in the repo root is the companion to this skill: it carries the
house rules and, importantly, a **"Facts that trip people up"** list of
already-settled questions (award amounts, degree years, which role is
deliberately omitted). Read it before "correcting" anything that looks wrong —
several of those apparent errors are the verified answer.

## The four documents

| Document | Contains | Built for |
| --- | --- | --- |
| `Bergmann-CV-Complete` | The public CV: current sections, no archive | General use, the repo README's download link |
| `Bergmann-CV-OCGS` | Official OCGS template, sections a–i; funding as tables; publications binned by `ocgs_category` with life-time counts | Graduate program appraisals |
| `Bergmann-SSHRC-Contributions` | Rolling six-year window, refereed/other/non-refereed split, plus prose | SSHRC applications (5-page limit) |
| `Bergmann-CV-FullRecord` | Everything, including `archive_*` and `pending_submissions` | The "full life file"; the source to curate from |

Anything application-specific is a **fifth kind of document** — built ad hoc,
never added to `build.py`. See [Tailored CVs](#tailored-cvs-for-applications).

## Adding or changing an entry

1. Find the right section in `cv.yaml` (`--list` below prints them all).
2. Write **one entry per event**. A talk that became a paper is two entries, in
   two sections; the same show remounted in a new city is two entries.
3. Insert it in the right place: `build.py` preserves file order, so most
   sections are hand-maintained newest-first. Put a 2026 entry at the top, not
   the bottom.
4. Set the flags (below). They decide which documents pick the entry up.
5. Rebuild and check the diff (see [Building](#building)).

**Dates** are `YYYY`, `YYYY-MM`, or `YYYY-MM-DD`; `end: present` for anything
ongoing. Rendering truncates to month precision, so the day is only ever worth
recording when the citation text quotes it anyway.

**Notes go in YAML comments**, on their own line above the entry — never inside
a `text:` string, because strings render verbatim into every document. Public
status ("in press", "submitted") belongs in `status:`; "confirm this with the
editor" belongs in a comment.

### Flags

| Flag | Meaning | Effect |
| --- | --- | --- |
| `refereed: true` | Anonymous peer review of the *full work* | SSHRC "Refereed contributions" |
| `other_refereed: true` | Reviewed conference presentation or poster | SSHRC "Other refereed contributions" |
| *(no flag)* | Everything else | SSHRC "Non-refereed contributions" |
| `sshrc: true` | Output of previous SSHRC funding | Renders `*` beside the entry in the SSHRC doc |
| `sshrc_exclude: true` | Keep out of the SSHRC doc | Only honoured on `forthcoming` entries |
| `status:` | Public-facing state of a forthcoming work | Rendered in brackets |
| `ocgs_category:` | `chapter`, `journal`, `refereed_proceedings`, or `other` | Bins the entry in the OCGS publication tables |

Two things about flags are easy to get wrong. `refereed` and `other_refereed`
are not interchangeable: a refereed conference *paper* in published proceedings
is `refereed: true` on the `publications` entry, while the act of *presenting*
it is a separate `other_refereed: true` entry under `presentations`. And an
un-flagged publication is not neutral — it lands in the SSHRC non-refereed list,
so leave the flag off only when that is the true answer.

`ocgs_category` covers four of the eight OCGS bins. Books authored, books
edited, and major invited contributions have no key because there is nothing to
put in them yet; adding the first one means editing `PUB_CATS` in `build.py`,
not inventing a category string.

### Funding entries

Funding carries structured fields alongside the citation because the OCGS
document renders them as a table: `source`, `program`, `ftype` (`C` granting
councils, `G` government, `F` foundations, `O` other), `amount`, `pi`,
`purpose`. The other three documents use `text:` as the citation, so both must
be filled in and must agree with each other.

### A note on `formats:`

The header comment in `cv.yaml` documents a `formats:` key for restricting an
entry to certain outputs. **`build.py` does not implement it** — no entry
currently uses it, and setting it will silently do nothing. Which documents an
entry reaches is decided by which section it lives in and by the flags above.
Either implement it or leave it alone; don't rely on it.

## Building

```bash
python build.py          # needs pyyaml; writes the four markdown files
git diff --stat output/  # confirm only the intended entries moved
```

Markdown is the source of truth for the layout; `.docx` and `.pdf` are produced
by pandoc. Locally that needs `pandoc` plus `texlive-xetex` for PDF, which is
often not installed — building markdown and letting CI do the conversion is the
normal path.

CI (`.github/workflows/build.yml`) rebuilds and commits `output/` **only on
pushes to `main`**, and only when `cv.yaml`, `build.py`, `prose/**`, `assets/**`,
or the workflow itself changed. Two consequences worth planning around:

- On a feature branch, nothing rebuilds. Either run `python build.py` and commit
  the markdown yourself so the diff is reviewable, or expect the `.docx`/`.pdf`
  to regenerate when the branch merges. Say which one you did.
- `output/` is machine-written and committed by `cv-bot`. Never hand-edit a file
  there; the next build overwrites it and the edit is lost silently.

The six-year SSHRC window is computed from *today* at build time, so that
document changes on its own as entries age out. A diff showing entries dropping
off the bottom of the SSHRC lists is usually the calendar, not a mistake.

## Tailored CVs for applications

Residencies, jobs, fellowships, and award nominations rarely want any of the
four canonical documents. They want a short, curated selection, sometimes with
prose that lives nowhere else. Build these with the bundled script rather than
by adding options to `build.py` — the canonical documents stay stable, and a
one-off spec file is easier to reuse next time than a hand-edited markdown file.

```bash
python .claude/skills/bergmann-cv/scripts/custom_cv.py --list      # sections, counts, date ranges
python .claude/skills/bergmann-cv/scripts/custom_cv.py spec.yaml   # -> custom/<name>.md
python .claude/skills/bergmann-cv/scripts/custom_cv.py spec.yaml --docx --pdf
```

A spec picks sections, filters them, and orders them for the reader:

```yaml
title: "Artist CV"
subtitle: "Prepared for the Banff Centre digital arts residency, October 2026"
sections:
  - heading: "Selected Creative Work"
    from: [creative, archive_installation]   # merged and sorted newest-first
    since: 2014
    limit: 8
  - heading: "AI and Performance Talks"
    from: invited_talks
    match: '\bAI\b|robot|artificial'         # case-insensitive regex over text
  - heading: "Statement"
    text: |
      Prose that belongs to this application only.
```

Full spec reference, more worked examples, and the curation judgement that
matters more than the mechanics: **`references/custom-cv.md`**.

Three habits keep this clean:

- **Write output to `custom/`, never `output/`.** CI runs `git add output/`, so
  anything left there gets committed as though it were canonical.
- **Filter, don't retype.** If a tailored CV needs an entry `cv.yaml` doesn't
  have, the entry is missing from the record — add it to `cv.yaml` first, then
  select it. Retyping it into the spec means the next document won't have it.
- **Curate down, not up.** Start from what the record holds (the FullRecord
  document exists for exactly this) and cut. Never write a line into a tailored
  CV that isn't supported by `cv.yaml`.

## SSHRC submissions

The generated lists refresh themselves; **the prose does not**.
`prose/sshrc-prose.md` is a generic base with HTML-comment placeholders marking
where each application's specific tie-ins go (HTML comments don't render).
Before a submission: replace those placeholders with sentences aimed at *this*
application, confirm the "present" claims are still true, and check what the
six-year window currently includes.

Formatting for actual uploads: CI PDFs use Liberation Serif, a metric clone of
Times New Roman, which is close but not what SSHRC asks for. Open the generated
`.docx` in Word, set Times New Roman 12pt, and export the PDF from there.
Margins (0.75") and US Letter page size are already compliant. The contributions
attachment has a 5-page limit — check the page count before sending.

## The archive, and other places facts live

- `archive_*` sections hold the pre-2019 design, lighting, direction, film, and
  systems record plus early employment. They render **only** in FullRecord. New
  historical finds go there, not into the main sections — that separation is
  deliberate, so don't "fix" it by promoting entries.
- `pending_submissions` is for work submitted but not yet public; FullRecord
  only. Move an entry out of it when the answer arrives.
- `ORCID-checklist.md` tracks what still needs syncing to ORCID
  (0000-0002-5698-8121). It is hand-maintained: after adding a publication or
  presentation to `cv.yaml`, add the matching checklist line.

## Style

Canadian English (colour, centre); Oxford comma; semicolons rather than
em-dashes. Citation strings follow the patterns already in the file — full
bibliographic details, co-authors in original order, roles named for co-authored
work. The fastest way to get a new entry right is to copy the shape of its
nearest neighbour in the same section.

## Reference files

- `references/data-model.md` — every `cv.yaml` section, its shape, and which
  documents render it. Read this when a task needs to know where something goes
  or why an entry isn't appearing.
- `references/custom-cv.md` — the tailored-CV spec format in full, with worked
  examples for the common application types.

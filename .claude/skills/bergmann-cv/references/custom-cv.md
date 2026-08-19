# Tailored CVs for applications

`scripts/custom_cv.py` builds a one-off document from `cv.yaml` using a short
YAML spec. The spec is the artifact worth keeping: next year's version of the
same application is a two-line edit rather than a fresh curation pass.

```bash
python .claude/skills/bergmann-cv/scripts/custom_cv.py --list          # inventory
python .claude/skills/bergmann-cv/scripts/custom_cv.py banff.yaml      # -> custom/banff.md
python .claude/skills/bergmann-cv/scripts/custom_cv.py banff.yaml --docx --pdf
python .claude/skills/bergmann-cv/scripts/custom_cv.py banff.yaml -o /tmp/draft.md
```

Markdown always gets written. `--docx` and `--pdf` shell out to pandoc using the
repo's own `assets/`, so a tailored CV looks like the canonical ones; if pandoc
isn't installed, the script prints the exact commands to run elsewhere and
leaves the markdown in place.

**Finding the repo.** The script needs `cv.yaml`, and it may be running from
inside the checkout (Claude Code) or from a skills directory somewhere else
entirely (the desktop app). It looks in order at `--repo`, `$BERGMANN_CV_REPO`,
the current directory and its parents, its own directory and its parents, then
the usual homes — `~/projects/Bergmann-CV` first, then `~/`, `~/Documents`,
`~/Developer`, `~/src`, `~/code`, `~/repos`, matching either capitalisation and
falling back to any similarly-named sibling. If none of that lands, it says so
rather than guessing:

```bash
python3 custom_cv.py spec.yaml --repo ~/Documents/Bergmann-CV
export BERGMANN_CV_REPO=~/Documents/Bergmann-CV   # or set it once
```

## Spec format

### Document level

| Key | Default | Notes |
| --- | --- | --- |
| `title` | `Curriculum Vitae` | Rendered as `# <title> — Michael F Bergmann`. |
| `subtitle` | none | Italic line under the title. Good place to name the application and date. |
| `contact` | `true` | The title/ORCID/email/website block from `personal`. Set `false` when the application form already collects it. |
| `hqp` | `false` | Mark supervised HQP with an asterisk in every citation, per tri-agency convention. A section can override it. |
| `font` | `default` | Which font set `--pdf` uses: `default` is Atkinson Hyperlegible, `sshrc` is Times New Roman. Set it to `sshrc` only when a funder demands that face. |
| `sections` | — | Ordered list; the order here is the order the reader sees. |

### Section level

A section either selects entries from `cv.yaml`, supplies literal `items`, or
holds a block of `text`.

| Key | Notes |
| --- | --- |
| `heading` | Section heading. Omit on a `text` block for an unheaded preamble. |
| `from` | One section name, or a list of them. A list is merged and sorted newest-first. `all` sweeps every section at once, which is how `flags: [mentorship]` gathers evidence that is scattered across sections by design. |
| `since` / `until` | Year or `YYYY-MM`. `since` also keeps entries with `end: present`, matching the SSHRC window's logic. |
| `flags` | List of flag names; an entry must have all of them true. e.g. `[refereed]`, `[other_refereed]`, `[sshrc]`, `[mentorship]`. |
| `match` | Case-insensitive regex over `text`. Keeps matches. Single-quote it in YAML so backslashes survive, and use `\b` boundaries on short acronyms. |
| `exclude` | Case-insensitive regex over `text`. Drops matches. |
| `limit` | Keep the first N after filtering and sorting. |
| `hqp` | Override the document-level HQP marking for this section only. |
| `sort` | `date-desc`, `date-asc`, or `file`. Defaults to `file` for a single source (preserving the hand-maintained order) and `date-desc` for merged sources. |
| `dated` | `false` suppresses the date column — useful for a bare list of titles. |
| `bullets` | `true` renders a bullet list instead of a table. Required for `teaching`, which has no dates. |
| `items` | Literal entries (`{date, text}`), bypassing `cv.yaml`. See the warning below. |
| `text` | A prose block. Rendered as-is under the heading. |

A section that selects zero entries prints a warning and is dropped from the
document, which is how a too-narrow filter announces itself.

### On `items`

Use it for genuine one-offs: a line about the specific project being proposed, a
reference, a note the record has no section for. If the entry is a real event —
a talk, a credit, an award — it belongs in `cv.yaml` first. An entry typed
straight into a spec exists only in that spec, and the next document won't know
about it.

## Worked examples

### Artist CV for a residency or exhibition

Practice first, academic apparatus trimmed to what an arts jury reads. The
archive matters here: pre-2019 design credits are often the strongest evidence
of practice, and they appear in no document but FullRecord.

```yaml
title: "Artist CV"
subtitle: "Banff Centre digital arts residency, October 2026"
sections:
  - heading: "Selected Creative Work"
    from: [creative, archive_installation, archive_projection_design]
    limit: 12
  - heading: "Residencies"
    from: [invited_positions, archive_residencies]
  - heading: "Exhibitions and Awards"
    from: awards
  - heading: "Selected Talks"
    from: invited_talks
    since: 2021
    limit: 6
  - heading: "Education"
    from: education
    until: 2014          # drop the in-progress PhD if the jury reads it as unfinished
```

### Two-page academic CV for a job or fellowship

Reverse the emphasis: appointments, funding, publications, supervision.

```yaml
title: "Curriculum Vitae"
subtitle: "Application for the Chair in Performance and Technology, March 2027"
sections:
  - heading: "Appointments"
    from: employment
  - heading: "Education"
    from: education
  - heading: "Peer-Reviewed Publications"
    from: publications
    flags: [refereed]
  - heading: "Other Publications"
    from: publications
    exclude: "Rough Draft"
  - heading: "Research Funding"
    from: [funding_external, funding_internal]
    since: 2018
  - heading: "Graduate Supervision"
    from: supervision
  - heading: "Selected Service"
    from: service
    since: 2022
    limit: 10
  - heading: "Courses Taught"
    from: teaching
    bullets: true
```

`from: supervision` pulls the entries; the summary sentence is not included, so
add it as a `text` block above if the count matters to the reader.

### Topic-focused packet

When an application is about one thread — AI, robotics, projection — regex
across several sections gathers the thread in one pass, and the merged sort puts
it in a single timeline.

```yaml
title: "Selected Work in AI and Performance"
contact: false
sections:
  - heading: "Research and Creation"
    from: [creative, publications, presentations, invited_talks]
    match: '\bAI\b|artificial intelligence|robot|machine learning|algorithm'
    since: 2019
  - heading: "Context"
    text: |
      Two or three sentences connecting this thread to the proposed work.
```

Note the word boundaries and the single quotes. Matching is case-insensitive and
unanchored, so a bare `match: "AI"` on this record pulls in three unrelated
entries by matching the "Ai" in collaborator **Ai**mée Dawn Robinson's name.
`\bAI\b` is the fix. Single-quote the pattern in YAML so backslashes survive —
double quotes need them doubled (`"\\bAI\\b"`).

Always read what a regex selected before shipping it; the entry count alone
won't tell you a name slipped in.

### Speaker or press bio packet

```yaml
title: "Speaker Biography and Credits"
subtitle: "Prepared October 2026"
sections:
  - heading: ~
    text: |
      A short third-person bio, written for this audience.
  - heading: "Recent Talks"
    from: invited_talks
    since: 2023
  - heading: "Press and Interviews"
    from: interviews
    limit: 6
```

## Curating well

The mechanics are the easy part. What makes a tailored CV work:

- **Read the call first.** Length limits, required sections, and what the panel
  is actually assessing determine the spec. A jury that asks for "selected
  works, maximum 10" wants ten, not everything since 2019.
- **Lead with what this reader values.** The section order is the argument. An
  arts jury reads creative work first; a hiring committee reads appointments and
  funding first; a grant panel reads the funded thread first.
- **`limit` is a curation tool, not a truncation tool.** `limit: 8` on a
  date-sorted list gives the eight most recent, which is rarely the eight
  strongest. When the selection matters, filter deliberately — by `match`, by
  `since`, or with several narrower sections — and check the result.
- **Mine the archive.** `archive_*` sections hold two decades of design,
  direction, lighting, film, and systems work that no canonical document shows.
  For anything practice-facing, that's where the depth is.
- **Say what you cut.** When handing back a tailored CV, note which sections
  were included and what was left out, so the omissions are a choice rather than
  a surprise.

## Where the output goes

Default output is `custom/<spec-name>.md` in the repo root. Keep it out of
`output/`: CI runs `git add output/`, so a stray file there gets committed as
though it were one of the four canonical documents.

Whether to commit `custom/` at all is a judgement call. The spec files are worth
keeping — they're small and they document how a past application was framed. The
generated markdown and PDFs are regenerable, so committing them is optional; if
they aren't committed, note in the handoff where the built file landed, since
this container is ephemeral.

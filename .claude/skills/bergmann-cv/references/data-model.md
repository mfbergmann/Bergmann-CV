# cv.yaml data model

Where each section goes, what shape it has, and which documents render it. Read
this when you need to know where a new fact belongs, or why an entry isn't
showing up where you expected.

Documents are abbreviated: **C** = Complete, **O** = OCGS, **S** =
SSHRC-Contributions, **F** = FullRecord.

## Entry shape

Almost every section is a list of one-line flow mappings:

```yaml
  - { date: 2025-09-12, other_refereed: true, text: "Bergmann, M. \"…\" …" }
```

| Key | Required | Notes |
| --- | --- | --- |
| `date` | effectively yes | `YYYY`, `YYYY-MM`, or `YYYY-MM-DD`. Rendered at month precision. An entry without one renders with a blank date cell. |
| `end` | no | Same formats, or `present`. `end` equal to `date` renders as a single date. |
| `text` | yes | The rendered citation. Rendered verbatim into every document — no internal notes here. |
| `refereed` | no | Anonymous peer review of the full work. |
| `other_refereed` | no | Reviewed conference presentation or poster. |
| `sshrc` | no | Output of previous SSHRC support; renders `*` in S. |
| `sshrc_exclude` | no | Honoured **only** on `forthcoming`. |
| `status` | forthcoming only | e.g. `in press`, `in draft`. Rendered in brackets. |
| `ocgs_category` | publications, forthcoming | `chapter`, `journal`, `refereed_proceedings`, `other`. |
| funding fields | funding only | `source`, `program`, `ftype`, `amount`, `pi`, `purpose`. |

Two sections break the pattern:

- **`personal`** is a mapping (`name`, `title`, `orcid`, `email`, `website`,
  `github`) and feeds every document's header.
- **`teaching`** is a list of plain strings, rendered as bullets. Course code,
  title, terms in parentheses, and any "(created course)" / "(redesigned
  course)" note. There are no dates to sort on, so the list order is the order
  readers see.
- **`supervision`** is a mapping of `summary` (a counts sentence, maintained by
  hand — update it when adding a student) and `entries` (normal entry list).

## Section-by-section

| Section | Documents | Notes |
| --- | --- | --- |
| `employment` | C O F | F merges in `archive_employment`, sorted by year. |
| `education` | C O F | Reverse chronological. |
| `qualifications` | C F | Teaching training and certifications. |
| `awards` | C O F | OCGS section d) "Honours". |
| `invited_positions` | C F | Residencies and invited positions; F merges `archive_residencies`. |
| `memberships` | C F | Professional associations and collectives. |
| `service` | C O F | OCGS section e). Largest section; committees, juries, review work, boards. |
| `funding_external` | C O F | O renders the structured table. |
| `funding_internal` | C O F | Same. |
| `funding_scholarships` | C F | Not in the OCGS funding tables. |
| `publications` | C O S F | Binned by `ocgs_category` in O; split by `refereed` in S. |
| `forthcoming` | C O S F | O lists separately per OCGS instructions; S omits `sshrc_exclude` entries. |
| `presentations` | C O S F | O merges these with posters as "Abstracts and/or papers read". |
| `posters` | C O S F | Same merge. |
| `invited_talks` | C S F | Always non-refereed in S. Not in O. |
| `creative` | C O S F | O calls it "Creative and Professional Work". |
| `supervision` | C O F | O section f). |
| `teaching` | C F | O section g) is hard-coded prose explaining there is no graduate program. |
| `interviews` | C F | Media coverage and interviews. |
| `pending_submissions` | F | Submitted, not yet public. |
| `archive_employment` | F | Merged into F's Employment. |
| `archive_residencies` | F | Merged into F's Residencies. |
| `archive_projection_design` | F | Own heading under the Archive. |
| `archive_assistant_design` | F | Own heading. |
| `archive_direction` | F | Own heading. |
| `archive_lighting` | F | Own heading. |
| `archive_installation` | F | Own heading. |
| `archive_film` | F | Own heading. |
| `archive_systems` | F | Own heading. Programming and system credits, largest archive section. |

## How each document selects

### Complete
Straight pass over the current sections in a fixed order. No filtering. Anything
in a non-archive section appears here, which is the reason the archive exists.

### OCGS
Follows the official template's sections a–i. Two mechanisms to know about:

- **Funding tables.** `funding_table()` reads the structured fields, defaulting
  `ftype` to `O` and `amount` to an em dash. A funding entry missing those
  fields still renders, just with blanks — so fill them in.
- **Publication bins.** `PUB_CATS` maps eight OCGS labels to `ocgs_category`
  values. Three labels (books authored, books edited, major invited
  contributions) map to `None` and always report a count of zero. The life-time
  summary counts every category, including the zeros; "Abstracts and/or papers
  read" counts presentations plus posters.

### SSHRC-Contributions
The only document that filters by date. `in_window()` keeps an entry if its
start year is within six years of today **or** its `end` is `present`, which is
how ongoing roles stay listed regardless of when they began.

- Refereed contributions: in-window `publications` with `refereed: true`
- Other refereed: in-window `presentations` + `posters` with `other_refereed: true`
- Non-refereed: in-window `publications` *without* `refereed`, plus in-window `invited_talks`
- Forthcoming: all `forthcoming` except `sshrc_exclude: true` (not date-filtered)
- Creative outputs: in-window `creative`
- `prose/sshrc-prose.md` is appended verbatim if it exists

An entry with `sshrc: true` gets a `*` prefix in the first three lists.

### FullRecord
Everything: all current sections, `pending_submissions`, and the seven
`archive_*` sections under an "Archive: Complete Design and Production Record"
heading. This is the document to read when curating a tailored CV — it is the
only place the whole record appears at once.

## Rendering mechanics

Entry sections render as two-column pipe tables, `**date** | text`. The dash
ratio in the separator row (24/76) is what sets column widths; the borders come
off via `assets/pdf-style.tex` for PDF (pandoc `-H`) and `assets/reference.docx`
for Word (`--reference-doc`, whose Table style has no borders and a flush-left
first column). If a table ever renders with visible borders or a stray indent,
the fix is in those two asset files, not in `build.py`.

An empty section renders as `*(none in window)*` rather than disappearing — seen
mostly in the SSHRC document when a window has no entries of some kind.

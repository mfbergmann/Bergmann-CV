# Bergmann-CV

Single-source CV system. **Edit `cv.yaml` only** — every document is generated from it.

## How it works

```
cv.yaml  ──►  build.py  ──►  output/*.md  ──►  GitHub Action  ──►  output/*.docx + *.pdf
prose/sshrc-prose.md ─┘
```

- `cv.yaml` — the canonical record: every position, publication, talk, credit, grant, and committee, tagged with dates and flags (`refereed`, `sshrc`, etc.).
- `build.py` — generates three markdown documents:
  - **Bergmann-CV-Complete** — everything, reverse chronological
  - **Bergmann-CV-OCGS** — OCGS section ordering
  - **Bergmann-SSHRC-Contributions** — auto-filtered to the rolling six-year window, SSHRC section structure, `*` markers on SSHRC-funded outputs
- `prose/sshrc-prose.md` — the narrative SSHRC sections (significance statements, training, relevant experience), appended to the contributions doc. Edit per application.
- `.github/workflows/build.yml` — on every push touching `cv.yaml`, `build.py`, or `prose/`, regenerates markdown, converts to `.docx` and `.pdf`, and commits them to `output/`.

## Updating

1. Something happens (talk, credit, grant) → add one line to the right section of `cv.yaml`.
2. Commit and push. PDFs rebuild automatically.
3. Link from the website to the stable raw URLs, e.g.:
   `https://raw.githubusercontent.com/mfbergmann/Bergmann-CV/main/output/Bergmann-CV-Complete.pdf`

## Local build

```
pip install pyyaml && python build.py          # markdown only
pandoc output/Bergmann-CV-Complete.md -o out.pdf --pdf-engine=xelatex   # optional
```

## Caveats

- **SSHRC submissions**: the CI PDF uses Liberation Serif (metric-identical to Times New Roman, which isn't freely licensed). For an actual SSHRC upload, open the generated `.docx` in Word, set Times New Roman, and export the PDF — margins and size are already compliant.
- Search `cv.yaml` for `TODO` — unresolved dates and details are marked inline.

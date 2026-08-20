#!/usr/bin/env bash
# Convert the generated markdown in output/ to .docx and .pdf.
#
# Fonts live here and nowhere else. CI and local builds both call this script,
# so a PDF built on a laptop matches the one the GitHub Action commits.
#
#   ./convert.sh                 # all four documents
#   ./convert.sh Bergmann-CV-OCGS
#
# Needs pandoc, and xelatex for PDF. Without xelatex it writes .docx and says so.

set -euo pipefail
cd "$(dirname "$0")"

# First font in each list that is actually installed wins. The body font is
# Atkinson Hyperlegible, drawn for legibility; the SSHRC document overrides it
# because SSHRC asks for Times New Roman, and CI falls back to Liberation Serif
# there — a metric clone, so line breaks and page count match the real thing.
BODY_FONTS=("Atkinson Hyperlegible" "Atkinson Hyperlegible Next" "DejaVu Serif")
SSHRC_FONTS=("Times New Roman" "Liberation Serif" "DejaVu Serif")

# Read the family list once. Note the deliberate absence of a pipe into
# `grep -q` here: under `pipefail`, grep exiting early on a match SIGPIPEs the
# upstream process and the successful match is reported as a failure.
FAMILIES=$(fc-list : family 2>/dev/null | tr ',' '\n' | sed 's/^ *//; s/ *$//' | sort -u || true)

pick_font() {
  local f
  for f in "$@"; do
    if printf '%s\n' "$FAMILIES" | grep -xF "$f" >/dev/null 2>&1; then
      printf '%s' "$f"; return 0
    fi
  done
  return 1
}

font_for() {
  case "$1" in
    Bergmann-SSHRC-Contributions) pick_font "${SSHRC_FONTS[@]}" ;;
    *)                            pick_font "${BODY_FONTS[@]}" ;;
  esac
}

command -v pandoc >/dev/null || { echo "pandoc is not installed; nothing to do." >&2; exit 1; }
HAVE_PDF=1
command -v xelatex >/dev/null || { echo "note: xelatex not found, writing .docx only" >&2; HAVE_PDF=0; }
command -v fc-list >/dev/null || echo "note: fc-list not found, font detection will fall through" >&2

# With no arguments, convert everything that is publishable. The artist CV comes
# from a committed spec via custom_cv.py rather than from build.py, so it may
# legitimately be absent on a checkout where only build.py has run — the default
# sweep skips what is missing, while an explicitly named document must exist.
DOCS=("$@")
EXPLICIT=1
if [ ${#DOCS[@]} -eq 0 ]; then
  EXPLICIT=0
  DOCS=(Bergmann-CV-Complete Bergmann-CV-OCGS Bergmann-SSHRC-Contributions Bergmann-CV-FullRecord
        Bergmann-CV-Artist)
fi

for f in "${DOCS[@]}"; do
  if [ ! -f "output/$f.md" ]; then
    [ "$EXPLICIT" = 1 ] && { echo "output/$f.md does not exist; run build.py first." >&2; exit 1; }
    echo "note: output/$f.md not present, skipping" >&2
    continue
  fi

  pandoc "output/$f.md" -o "output/$f.docx" --reference-doc=assets/reference.docx
  echo "Wrote output/$f.docx"

  [ "$HAVE_PDF" = 1 ] || continue
  if ! font=$(font_for "$f"); then
    echo "warning: no usable font found for $f, skipping its PDF" >&2
    continue
  fi
  # Say so loudly when the first choice was missing: a silent fallback is how a
  # CV quietly ships in the wrong typeface.
  case "$f" in
    Bergmann-SSHRC-Contributions) first="${SSHRC_FONTS[0]}" ;;
    *)                            first="${BODY_FONTS[0]}" ;;
  esac
  [ "$font" = "$first" ] || echo "warning: $first is not installed; $f falls back to $font" >&2

  pandoc "output/$f.md" -o "output/$f.pdf" --pdf-engine=xelatex \
    -H assets/pdf-style.tex \
    -V mainfont="$font" -V fontsize=12pt \
    -V geometry:margin=0.75in -V papersize=letter
  echo "Wrote output/$f.pdf ($font)"
done

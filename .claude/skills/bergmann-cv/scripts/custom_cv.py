#!/usr/bin/env python3
"""Build a one-off, application-specific CV from cv.yaml.

The four canonical documents come from build.py and are not configurable.
This script exists for the other case: a residency, job, grant, or award
application that wants a short, curated CV — a subset of the record, in an
order that suits the reader, sometimes with prose the canonical documents
have no place for.

It reads a small YAML spec describing the document, pulls entries out of
cv.yaml, and writes markdown using the same two-column table layout as
build.py, so pandoc renders it with the repo's existing styling.

Usage:
    python3 custom_cv.py --list                     # what sections exist, with date ranges
    python3 custom_cv.py spec.yaml                  # -> custom/<slug>.md
    python3 custom_cv.py spec.yaml --docx --pdf     # also convert, if pandoc is installed
    python3 custom_cv.py spec.yaml -o path/to.md    # explicit output path
    python3 custom_cv.py spec.yaml --repo ~/Bergmann-CV   # when the repo isn't nearby

See references/custom-cv.md for the spec format and worked examples.
"""
import argparse
import datetime
import os
import pathlib
import re
import shutil
import subprocess
import sys

try:
    import yaml
except ModuleNotFoundError:
    # find_repo() is defined below and needs yaml itself, so repeat the cheap
    # part of it here: enough to name a real path in the error rather than a
    # placeholder the reader has to translate.
    def _guess_repo():
        seen = [pathlib.Path.cwd(), pathlib.Path(__file__).resolve().parent]
        for start in seen:
            for d in [start, *start.parents]:
                if (d / "cv.yaml").exists() and (d / "build.py").exists():
                    return d
        home = pathlib.Path.home()
        for parent in (home / "projects", home / "Projects", home, home / "Documents",
                       home / "Developer", home / "src", home / "code", home / "repos"):
            for name in ("Bergmann-CV", "bergmann-cv"):
                if (parent / name / "cv.yaml").exists():
                    return parent / name
        return None

    repo = _guess_repo()
    where = str(repo) if repo else "/path/to/Bergmann-CV"
    venv = f"{where}/.venv/bin/python"
    hint = (f"  {venv} " + " ".join(sys.argv)) if pathlib.Path(venv).exists() else (
        f"  cd {where} && python3 -m venv .venv && .venv/bin/pip install pyyaml\n"
        f"  then re-run with {where}/.venv/bin/python")
    sys.exit(
        "This needs pyyaml, and the interpreter running it does not have it:\n"
        f"  {sys.executable}\n\n"
        "The repo keeps one in a virtual environment:\n" + hint
    )

TODAY = datetime.date.today()
REPO = None      # set by load_repo()
CV = None


# ---------------------------------------------------------------- repo layout

def find_repo(explicit=None) -> pathlib.Path:
    """Locate the Bergmann-CV checkout.

    The script may sit inside the repo (Claude Code, .claude/skills/…) or well
    outside it (a skill installed into the desktop app's own directory), so try
    the explicit answer first, then the obvious neighbourhoods, then the usual
    places a checkout lives.
    """
    def walk_up(p):
        for d in [p, *p.parents]:
            if (d / "cv.yaml").exists() and (d / "build.py").exists():
                return d
        return None

    if explicit:
        p = pathlib.Path(explicit).expanduser().resolve()
        if (p / "cv.yaml").exists():
            return p
        sys.exit(f"No cv.yaml in {p}")

    env = os.environ.get("BERGMANN_CV_REPO")
    if env:
        return find_repo(env)

    for start in (pathlib.Path.cwd(), pathlib.Path(__file__).resolve().parent):
        found = walk_up(start)
        if found:
            return found

    # Common places a checkout lives. Look for the repo by name first, then for
    # any similarly-named sibling, since the clone directory's capitalisation
    # varies and some volumes are case-sensitive.
    home = pathlib.Path.home()
    parents = [home / "projects", home / "Projects", home, home / "Documents",
               home / "Developer", home / "src", home / "code", home / "repos"]
    for parent in parents:
        for name in ("Bergmann-CV", "bergmann-cv"):
            if (parent / name / "cv.yaml").exists():
                return parent / name
    for parent in parents:
        if not parent.is_dir():
            continue
        for child in sorted(parent.iterdir()):
            if "bergmann" in child.name.lower() and (child / "cv.yaml").exists():
                return child

    sys.exit("Could not find the Bergmann-CV repo. Run this from inside a checkout, "
             "pass --repo /path/to/Bergmann-CV, or set BERGMANN_CV_REPO.")


def load_repo(explicit=None):
    global REPO, CV
    REPO = find_repo(explicit)
    CV = yaml.safe_load((REPO / "cv.yaml").read_text())

# Rendering below is deliberately a copy of build.py's helpers rather than an
# import: importing build.py would run it and rewrite output/, producing diff
# noise. Keep these in sync if build.py's table layout ever changes.
DATE_RE = re.compile(r"^\d{4}(-\d{2})?(-\d{2})?$")


def year(e):
    return str(e.get("date", ""))[:4]


def fmt(d, precision="month"):
    d = str(d)
    if not DATE_RE.match(d):
        return d                                   # leave placeholders intact
    return d[:4] if precision == "year" else d[:7]


def dstr(e, precision="month"):
    """The date cell. At year precision an entry inside one year collapses to
    that year, which is what an arts CV wants: the specific run of dates already
    lives in the citation, and repeating it in the left column is noise."""
    d = fmt(e.get("date", ""), precision)
    end = e.get("end")
    if end:
        end = "present" if str(end) == "present" else fmt(end, precision)
        return d if end == d else f"{d} – {end}"
    return d


def hqp_text(e):
    """Citation with supervised HQP marked by an asterisk after the name.

    This is the tri-agency CV's convention, not the house style, so it applies
    only where a spec asks for it. Mirrors hqp_text() in build.py.
    """
    text = e["text"]
    for name in e.get("hqp", []):
        if name in text:
            text = text.replace(name, f"{name}*", 1)
    return text


def rows(entries, dated=True, hqp=False, precision="month"):
    """Two-column pipe table: date | item. Dash ratio sets column widths (~24/76)."""
    lines = ["|  |  |", "|:" + "-" * 24 + "|:" + "-" * 76 + "|"]
    for e in entries:
        d = f"**{dstr(e, precision)}**" if dated and e.get("date") else ""
        lines.append(f"| {d} | {hqp_text(e) if hqp else e['text']} |")
    return "\n".join(lines)


# ---------------------------------------------------------------- selection

# Sections that are not part of the record proper, so `from: all` skips them.
NOT_A_SECTION = {"personal"}


def source_entries(names):
    """Collect entries from one or more cv.yaml keys, normalising the odd shapes."""
    if list(names) == ["all"]:
        names = [k for k in CV if k not in NOT_A_SECTION]
    out = []
    for name in names:
        if name not in CV:
            sys.exit(f"Unknown cv.yaml section: {name!r}. Run --list to see what exists.")
        block = CV[name]
        if name == "supervision":                       # dict: summary + entries
            out += block["entries"]
        elif isinstance(block, dict):                   # personal, etc.
            sys.exit(f"Section {name!r} is not a list of entries; use `text:` instead.")
        elif block and isinstance(block[0], str):       # teaching: plain strings
            out += [{"text": s} for s in block]
        else:
            out += block
    return out


def yr(v):
    """Accept 2019 or '2019-06'; compare as a zero-padded string."""
    return str(v)[:4]


def select(spec):
    entries = source_entries(spec["from"] if isinstance(spec["from"], list) else [spec["from"]])

    if "since" in spec:
        cutoff = yr(spec["since"])
        entries = [e for e in entries
                   if year(e) >= cutoff or str(e.get("end")) == "present"]
    if "until" in spec:
        entries = [e for e in entries if year(e) <= yr(spec["until"])]
    for flag in spec.get("flags", []):
        entries = [e for e in entries if e.get(flag)]
    if "match" in spec:
        pat = re.compile(spec["match"], re.I)
        entries = [e for e in entries if pat.search(e["text"])]
    if "exclude" in spec:
        pat = re.compile(spec["exclude"], re.I)
        entries = [e for e in entries if not pat.search(e["text"])]

    # A single source keeps cv.yaml's hand-maintained order (build.py does the
    # same); merged sources need an explicit sort to interleave sensibly.
    multi = spec["from"] == "all" or (
        isinstance(spec["from"], list) and len(spec["from"]) > 1)
    sort = spec.get("sort", "date-desc" if multi else "file")
    if sort == "date-desc":
        entries = sorted(entries, key=lambda e: str(e.get("date", "")), reverse=True)
    elif sort == "date-asc":
        entries = sorted(entries, key=lambda e: str(e.get("date", "")))
    elif sort != "file":
        sys.exit(f"Unknown sort: {sort!r} (use date-desc, date-asc, or file)")

    if "limit" in spec:
        entries = entries[: spec["limit"]]
    return entries


# ---------------------------------------------------------------- rendering

def render(spec):
    P = CV["personal"]
    doc = [f"# {spec.get('title', 'Curriculum Vitae')} — {P['name']}\n"]
    if spec.get("subtitle"):
        doc.append(f"*{spec['subtitle']}*\n")
    if spec.get("contact", True):
        # Which address the document carries. Named as a key in cv.yaml's
        # `personal` rather than written out here, so the address itself stays
        # in one place: `contact_email: email_personal` for work that goes to
        # juries and funders instead of to the university.
        key = spec.get("contact_email", "email")
        if key not in P:
            sys.exit(f"contact_email: {key!r} is not a key in cv.yaml's personal block "
                     f"(available: {', '.join(k for k in P if 'email' in k)})")
        doc.append(f"{P['title']}  \nORCID: {P['orcid']} · {P[key]} · {P['website']}\n")
    doc.append(f"<!-- Generated {TODAY.isoformat()} from cv.yaml by custom_cv.py — "
               f"edit cv.yaml or the spec, never this file. -->\n")

    for sec in spec.get("sections", []):
        heading = sec.get("heading")
        if "text" in sec:                                # free prose block
            doc.append(f"\n## {heading}\n\n{sec['text'].rstrip()}\n" if heading
                       else f"\n{sec['text'].rstrip()}\n")
            continue

        entries = sec["items"] if "items" in sec else select(sec)
        if not entries:
            print(f"  warning: section {heading!r} selected 0 entries — check the filters",
                  file=sys.stderr)
            continue

        doc.append(f"\n## {heading}\n")
        if sec.get("bullets"):
            doc.append("\n" + "\n".join(f"- {e['text']}" for e in entries) + "\n")
        else:
            doc.append("\n" + rows(entries, dated=sec.get("dated", True),
                                    hqp=sec.get("hqp", spec.get("hqp", False)),
                                    precision=sec.get("dates", spec.get("dates", "month"))) + "\n")

    return "\n".join(doc)


# Keep these lists in step with convert.sh, which does the same job for the four
# canonical documents. Atkinson Hyperlegible is the house font; a spec sets
# `font: sshrc` when the document has to satisfy SSHRC's Times New Roman rule.
FONT_SETS = {
    "default": ["Atkinson Hyperlegible", "Atkinson Hyperlegible Next", "DejaVu Serif"],
    "sshrc": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
}


def installed_families():
    """Font families fontconfig can see. Empty set if fc-list isn't available."""
    if not shutil.which("fc-list"):
        return set()
    out = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True)
    return {name.strip() for line in out.stdout.splitlines() for name in line.split(",")}


def pick_font(font_set):
    candidates = FONT_SETS.get(font_set or "default", FONT_SETS["default"])
    have = installed_families()
    if not have:
        return candidates[0]      # no fontconfig; let xelatex have a go at the first choice
    for f in candidates:
        if f in have:
            return f
    return None


def convert(md_path, want_docx, want_pdf, font_set=None):
    if not (want_docx or want_pdf):
        return
    font = pick_font(font_set)
    if not shutil.which("pandoc"):
        print("\npandoc is not installed here, so only markdown was written.\n"
              "Install it with `brew install pandoc`, or convert where it is available:\n"
              f"  pandoc {md_path.name} -o {md_path.stem}.docx "
              f"--reference-doc={REPO/'assets/reference.docx'}\n"
              f"  pandoc {md_path.name} -o {md_path.stem}.pdf --pdf-engine=xelatex "
              f"-H {REPO/'assets/pdf-style.tex'} -V mainfont='{font or FONT_SETS['default'][0]}' "
              "-V fontsize=12pt -V geometry:margin=0.75in -V papersize=letter",
              file=sys.stderr)
        return

    if want_docx:
        subprocess.run(["pandoc", md_path.name, "-o", f"{md_path.stem}.docx",
                        f"--reference-doc={REPO / 'assets/reference.docx'}"],
                       cwd=md_path.parent, check=True)
        print(f"Wrote {md_path.with_suffix('.docx')}")
    if want_pdf:
        if not shutil.which("xelatex"):
            print("xelatex is not installed, so no PDF was written. "
                  "`brew install --cask basictex` provides it.", file=sys.stderr)
            return
        if not font:
            print(f"None of {FONT_SETS.get(font_set or 'default')} is installed, "
                  "so no PDF was written.", file=sys.stderr)
            return
        subprocess.run(["pandoc", md_path.name, "-o", f"{md_path.stem}.pdf",
                        "--pdf-engine=xelatex", "-H", str(REPO / "assets/pdf-style.tex"),
                        "-V", f"mainfont={font}", "-V", "fontsize=12pt",
                        "-V", "geometry:margin=0.75in", "-V", "papersize=letter"],
                       cwd=md_path.parent, check=True)
        print(f"Wrote {md_path.with_suffix('.pdf')} ({font})")


def list_sections():
    """Inventory of what is available to draw from, so a spec can be written blind."""
    print(f"{'section':<28} {'n':>4}  date range")
    print("-" * 58)
    for name, block in CV.items():
        if name == "personal":
            continue
        entries = block["entries"] if name == "supervision" else block
        if entries and isinstance(entries[0], str):
            print(f"{name:<28} {len(entries):>4}  (plain strings — use bullets: true)")
            continue
        years = sorted(year(e) for e in entries if e.get("date"))
        span = f"{years[0]}–{years[-1]}" if years else "undated"
        print(f"{name:<28} {len(entries):>4}  {span}")


def main():
    ap = argparse.ArgumentParser(description="Build an application-specific CV from cv.yaml.")
    ap.add_argument("spec", nargs="?", help="YAML spec file describing the document")
    ap.add_argument("-o", "--out", help="output markdown path (default: custom/<spec-name>.md)")
    ap.add_argument("--docx", action="store_true", help="also convert to .docx via pandoc")
    ap.add_argument("--pdf", action="store_true", help="also convert to .pdf via pandoc+xelatex")
    ap.add_argument("--list", action="store_true", help="list cv.yaml sections and exit")
    ap.add_argument("--repo", help="path to the Bergmann-CV checkout (default: auto-detect)")
    args = ap.parse_args()

    load_repo(args.repo)

    if args.list:
        list_sections()
        return
    if not args.spec:
        ap.error("give a spec file, or --list to see what cv.yaml holds")

    spec_path = pathlib.Path(args.spec)
    spec = yaml.safe_load(spec_path.read_text())
    out = pathlib.Path(args.out) if args.out else REPO / "custom" / f"{spec_path.stem}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(spec))
    print(f"Wrote {out}")
    convert(out, args.docx, args.pdf, spec.get("font"))


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:      # e.g. `--list | head`
        sys.stderr.close()

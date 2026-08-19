#!/usr/bin/env python3
"""Build all CV formats from cv.yaml. Outputs markdown to output/;
the GitHub Action (or local pandoc) converts markdown to docx/pdf.
Entry sections render as two-column tables (date | item); pandoc turns
these into borderless tables via assets/pdf-style.tex and assets/reference.docx."""
import yaml, datetime, pathlib, re

CV = yaml.safe_load(open(pathlib.Path(__file__).parent / "cv.yaml"))
OUT = pathlib.Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)
TODAY = datetime.date.today()
SIX_YEARS_AGO = TODAY.replace(year=TODAY.year - 6)

DATE_RE = re.compile(r"^\d{4}(-\d{2})?(-\d{2})?$")

def year(e):
    return str(e.get("date", ""))[:4]

def fmt(d):
    d = str(d)
    return d[:7] if DATE_RE.match(d) else d  # display at month precision; leave placeholders intact

def dstr(e):
    d, end = fmt(e.get("date", "")), e.get("end")
    if end:
        end = "present" if str(end) == "present" else fmt(end)
        if end == d:
            return d
        return f"{d} – {end}"
    return d

def in_window(e):
    try:
        return int(year(e)) >= SIX_YEARS_AGO.year or str(e.get("end")) == "present"
    except ValueError:
        return True

def hqp_text(e):
    """The entry's citation with supervised HQP marked, per tri-agency convention.

    The tri-agency CV asks for an asterisk after the name of any highly qualified
    person the applicant supervised. That convention belongs to that document
    alone — the Complete, OCGS, and SSHRC CVs have their own citation styles — so
    `hqp:` is recorded on the entry here and rendered only where it is asked for.
    Nothing in the four canonical documents calls this.
    """
    text = e["text"]
    for name in e.get("hqp", []):
        if name in text:
            text = text.replace(name, f"{name}*", 1)
    return text


def check_hqp(cv):
    """Warn when an hqp: name is not in the citation it annotates — almost always
    a typo or a name that changed on one side only, and silent until submission."""
    problems = []
    for section, v in cv.items():
        entries = v.get("entries", []) if isinstance(v, dict) else v
        if not isinstance(entries, list):
            continue
        for e in entries:
            if not isinstance(e, dict):
                continue
            for name in e.get("hqp", []):
                if name not in e.get("text", ""):
                    problems.append(f"  {section}: {name!r} not found in {e.get('text','')[:60]!r}")
    return problems


def rows(entries, star=False, dated=True):
    """Two-column pipe table: date | item. Dash ratio sets column widths (~24/76)."""
    lines = ["|  |  |", "|:" + "-" * 24 + "|:" + "-" * 76 + "|"]
    for e in entries:
        mark = "\\* " if (star and e.get("sshrc")) else ""
        d = f"**{dstr(e)}**" if dated and e.get("date") else ""
        lines.append(f"| {d} | {mark}{e['text']} |")
    return "\n".join(lines)

def sec(title, entries, star=False, dated=True):
    if not entries:
        return f"\n## {title}\n\n*(none in window)*\n"
    return f"\n## {title}\n\n" + rows(entries, star, dated) + "\n"

def strsec(title, items):
    return f"\n## {title}\n\n" + "\n".join(f"- {i}" for i in items) + "\n"

def view(doc):
    """cv.yaml filtered to the entries that opt into `doc` via `formats:`.

    An entry with no `formats:` key belongs to every document; listing formats
    narrows it (e.g. `formats: [complete]` keeps an entry off the OCGS and
    SSHRC documents). FullRecord is never filtered — it is the full record by
    definition, so it uses CV directly."""
    def keep(e):
        return not isinstance(e, dict) or doc in e.get("formats", [doc])

    def filt(v):
        if isinstance(v, list):
            return [e for e in v if keep(e)]
        if isinstance(v, dict) and "entries" in v:      # supervision
            return {**v, "entries": [e for e in v["entries"] if keep(e)]}
        return v

    return {k: filt(v) for k, v in CV.items()}


V_COMPLETE, V_OCGS, V_SSHRC = view("complete"), view("ocgs"), view("sshrc")

P = CV["personal"]
head = (f"# {P['name']}\n\n{P['title']}  \nORCID: {P['orcid']} · {P['email']} · {P['website']}\n\n"
        f"<!-- Generated {TODAY.isoformat()} from cv.yaml — do not edit outputs directly. -->\n")

# ---------- 1. Complete CV ----------
doc = [head.replace("# ", "# Curriculum Vitae — ")]
doc.append(sec("Employment", V_COMPLETE["employment"]))
doc.append(sec("Education", V_COMPLETE["education"]))
doc.append(sec("Teaching, Training, and Certifications", V_COMPLETE["qualifications"]))
doc.append(sec("Awards and Distinctions", V_COMPLETE["awards"]))
doc.append(sec("Residencies and Invited Positions", V_COMPLETE["invited_positions"]))
doc.append(sec("Publications", V_COMPLETE["publications"]))
doc.append(sec("Forthcoming", [{**e, "text": f"{e['text']} [{e.get('status','')}]"} for e in V_COMPLETE["forthcoming"]]))
doc.append(sec("Conference Presentations", V_COMPLETE["presentations"]))
doc.append(sec("Poster Presentations", V_COMPLETE["posters"]))
doc.append(sec("Invited Talks and Public Lectures", V_COMPLETE["invited_talks"]))
doc.append(sec("Creative Research Output", V_COMPLETE["creative"]))
doc.append(sec("External Research Funding", V_COMPLETE["funding_external"]))
doc.append(sec("Internal Research Funding", V_COMPLETE["funding_internal"]))
doc.append(sec("Scholarships", V_COMPLETE["funding_scholarships"]))
doc.append(f"\n## Graduate Supervision\n\n{V_COMPLETE['supervision']['summary']}\n\n" + rows(V_COMPLETE["supervision"]["entries"]) + "\n")
doc.append(strsec("Courses Taught", V_COMPLETE["teaching"]))
doc.append(sec("Service", V_COMPLETE["service"]))
doc.append(sec("Memberships and Collectives", V_COMPLETE["memberships"]))
doc.append(sec("Interviews and Media", V_COMPLETE["interviews"]))
(OUT / "Bergmann-CV-Complete.md").write_text("\n".join(doc))

# ---------- 2. OCGS CV (follows the official OCGS template sections a–i) ----------
def funding_table(entries):
    lines = ["| Year | Source | Program | Type\\* | Amount | PI | Purpose\\*\\* |",
             "|:-----|:---------|:--------------|:---|:--------|:----------|:------|"]
    for e in entries:
        lines.append(f"| {year(e)} | {e.get('source','')} | {e.get('program','')} | {e.get('ftype','O')} | "
                     f"{e.get('amount','—')} | {e.get('pi','')} | {e.get('purpose','')} |")
    lines.append("\n\\*Type: C – Granting Councils; G – Government; F – Foundations; O – Other  \n\\*\\*Purpose: research, travel, publication, etc.")
    return "\n".join(lines)

PUB_CATS = [("Books authored", None), ("Books edited", None), ("Chapters in books", "chapter"),
            ("Papers in refereed journals", "journal"), ("Papers in refereed conference proceedings", "refereed_proceedings"),
            ("Major invited contributions and/or technical reports", None), ("Abstracts and/or papers read", "papers_read"),
            ("Other (data sets, magazine and literary publications)", "other")]
pubs_by_cat = lambda cat: [e for e in V_OCGS["publications"] if e.get("ocgs_category") == cat]
papers_read = sorted(V_OCGS["presentations"] + V_OCGS["posters"], key=lambda e: str(e.get("date", "")), reverse=True)

doc = [head.replace("# ", "# OCGS Curriculum Vitae — ")]
doc.append(f"\n## a) Name\n\nBergmann, Michael F. — {P['title']}\n")
doc.append(sec("b) Degrees", V_OCGS["education"]))
doc.append(sec("c) Employment History", V_OCGS["employment"]))
doc.append(sec("d) Honours", V_OCGS["awards"]))
doc.append(sec("e) Scholarly and Professional Academic Activities", V_OCGS["service"]))
doc.append(f"\n## f) Graduate Supervisions\n\n{V_OCGS['supervision']['summary']}\n\n" + rows(V_OCGS["supervision"]["entries"]) + "\n")
doc.append("\n## g) Graduate Courses\n\nNone — the School of Performance offers no graduate program; graduate work is supervised through the Master of Digital Media program (see f).\n")
doc.append("\n## h) Research Funding\n\n### 1. External Research Funding\n\n" + funding_table(V_OCGS["funding_external"]) +
           "\n\n### 2. Internal Research Funding\n\n" + funding_table(V_OCGS["funding_internal"]) + "\n")
counts = "\n".join(f"- {label}: {len(papers_read) if key == 'papers_read' else (len(pubs_by_cat(key)) if key else 0)}"
                   for label, key in PUB_CATS)
doc.append(f"\n## i) Publications\n\n### Life-time summary\n\n{counts}\n")
for label, key in PUB_CATS:
    if key == "papers_read":
        doc.append(sec(label, papers_read))
    elif key and pubs_by_cat(key):
        doc.append(sec(label, pubs_by_cat(key)))
forth = [{**e, "text": f"{e['text']} [{e.get('status','')}]"} for e in V_OCGS["forthcoming"]]
doc.append(sec("Submitted and in-press (listed separately per OCGS instructions)", forth))
doc.append(sec("Creative and Professional Work", V_OCGS["creative"]))
(OUT / "Bergmann-CV-OCGS.md").write_text("\n".join(doc))

# ---------- 3. SSHRC Research Contributions (six-year window) ----------
w = lambda key: [e for e in V_SSHRC[key] if in_window(e)]
doc = [f"# Research Contributions and Relevant Experience — {P['name']}\n\n*Six-year window: contributions since {SIX_YEARS_AGO.isoformat()}. \\* = resulted from previous SSHRC support.*\n\n<!-- Generated {TODAY.isoformat()}; prose sections (significance, training narrative, relevant experience) live in prose/sshrc-prose.md and are appended below. -->\n"]
doc.append("\n# 1. Research Contributions Over the Last Six Years\n")
doc.append(sec("Refereed contributions", [e for e in w("publications") if e.get("refereed")], star=True))
doc.append(sec("Other refereed contributions", [e for e in w("presentations") + w("posters") if e.get("other_refereed")], star=True))
nonref = [e for e in w("publications") if not e.get("refereed")] + w("invited_talks")
doc.append(sec("Non-refereed contributions", nonref, star=True))
sshrc_forth = [e for e in V_SSHRC["forthcoming"] if not e.get("sshrc_exclude")]
doc.append(sec("Forthcoming contributions", [{**e, "text": f"{e['text']} Status: {e.get('status','')}"} for e in sshrc_forth]))
doc.append(sec("Creative outputs", w("creative")))
prose = pathlib.Path(__file__).parent / "prose" / "sshrc-prose.md"
if prose.exists():
    doc.append("\n" + prose.read_text())
(OUT / "Bergmann-SSHRC-Contributions.md").write_text("\n".join(doc))

# ---------- 4. Full Record ("full life file": everything, including the archive) ----------
doc = [head.replace("# ", "# Full Record — ")]
doc.append("\n*The complete record. Archive sections at the end hold historical credits excluded from the rendered CVs; filter from here when building any application-specific version.*\n")
merged = lambda *ls: sorted(sum(ls, []), key=year, reverse=True)
doc.append(sec("Employment", merged(CV["employment"], CV["archive_employment"])))
doc.append(sec("Education", CV["education"]))
doc.append(sec("Teaching, Training, and Certifications", CV["qualifications"]))
doc.append(sec("Awards and Distinctions", CV["awards"]))
doc.append(sec("Residencies and Invited Positions", merged(CV["invited_positions"], CV["archive_residencies"])))
doc.append(sec("Publications", CV["publications"]))
doc.append(sec("Forthcoming", [{**e, "text": f"{e['text']} [{e.get('status','')}]"} for e in CV["forthcoming"]]))
doc.append(sec("Pending Submissions (not yet public)", CV["pending_submissions"]))
doc.append(sec("Conference Presentations", CV["presentations"]))
doc.append(sec("Poster Presentations", CV["posters"]))
doc.append(sec("Invited Talks and Public Lectures", CV["invited_talks"]))
doc.append(sec("Creative Research Output", CV["creative"]))
doc.append(sec("External Research Funding", CV["funding_external"]))
doc.append(sec("Internal Research Funding", CV["funding_internal"]))
doc.append(sec("Scholarships", CV["funding_scholarships"]))
doc.append(f"\n## Graduate Supervision\n\n{CV['supervision']['summary']}\n\n" + rows(CV["supervision"]["entries"]) + "\n")
doc.append(strsec("Courses Taught", CV["teaching"]))
doc.append(sec("Service", CV["service"]))
doc.append(sec("Memberships and Collectives", CV["memberships"]))
doc.append(sec("Interviews and Media", CV["interviews"]))
doc.append("\n# Archive: Complete Design and Production Record\n")
doc.append(sec("Projection Design", CV["archive_projection_design"]))
doc.append(sec("Assistant Projection Design", CV["archive_assistant_design"]))
doc.append(sec("Direction", CV["archive_direction"]))
doc.append(sec("Lighting Design", CV["archive_lighting"]))
doc.append(sec("Installation and Video Art", CV["archive_installation"]))
doc.append(sec("Film", CV["archive_film"]))
doc.append(sec("Projection and Live Event Systems", CV["archive_systems"]))
(OUT / "Bergmann-CV-FullRecord.md").write_text("\n".join(doc))

for problem in check_hqp(CV):
    print(f"warning: hqp name not in citation\n{problem}")

print(f"Built 4 documents in output/ (six-year window: since {SIX_YEARS_AGO.isoformat()})")

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

P = CV["personal"]
head = (f"# {P['name']}\n\n{P['title']}  \nORCID: {P['orcid']} · {P['email']} · {P['website']}\n\n"
        f"<!-- Generated {TODAY.isoformat()} from cv.yaml — do not edit outputs directly. -->\n")

# ---------- 1. Complete CV ----------
doc = [head.replace("# ", "# Curriculum Vitae — ")]
doc.append(sec("Employment", CV["employment"]))
doc.append(sec("Education", CV["education"]))
doc.append(sec("Teaching, Training, and Certifications", CV["qualifications"]))
doc.append(sec("Awards and Distinctions", CV["awards"]))
doc.append(sec("Residencies and Invited Positions", CV["invited_positions"]))
doc.append(sec("Publications", CV["publications"]))
doc.append(sec("Forthcoming", [{**e, "text": f"{e['text']} [{e.get('status','')}]"} for e in CV["forthcoming"]]))
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
pubs_by_cat = lambda cat: [e for e in CV["publications"] if e.get("ocgs_category") == cat]
papers_read = sorted(CV["presentations"] + CV["posters"], key=lambda e: str(e.get("date", "")), reverse=True)

doc = [head.replace("# ", "# OCGS Curriculum Vitae — ")]
doc.append(f"\n## a) Name\n\nBergmann, Michael F. — {P['title']}\n")
doc.append(sec("b) Degrees", CV["education"]))
doc.append(sec("c) Employment History", CV["employment"]))
doc.append(sec("d) Honours", CV["awards"]))
doc.append(sec("e) Scholarly and Professional Academic Activities", CV["service"]))
doc.append(f"\n## f) Graduate Supervisions\n\n{CV['supervision']['summary']}\n\n" + rows(CV["supervision"]["entries"]) + "\n")
doc.append("\n## g) Graduate Courses\n\nNone — the School of Performance offers no graduate program; graduate work is supervised through the Master of Digital Media program (see f).\n")
doc.append("\n## h) Research Funding\n\n### 1. External Research Funding\n\n" + funding_table(CV["funding_external"]) +
           "\n\n### 2. Internal Research Funding\n\n" + funding_table(CV["funding_internal"]) + "\n")
counts = "\n".join(f"- {label}: {len(papers_read) if key == 'papers_read' else (len(pubs_by_cat(key)) if key else 0)}"
                   for label, key in PUB_CATS)
doc.append(f"\n## i) Publications\n\n### Life-time summary\n\n{counts}\n")
for label, key in PUB_CATS:
    if key == "papers_read":
        doc.append(sec(label, papers_read))
    elif key and pubs_by_cat(key):
        doc.append(sec(label, pubs_by_cat(key)))
forth = [{**e, "text": f"{e['text']} [{e.get('status','')}]"} for e in CV["forthcoming"]]
doc.append(sec("Submitted and in-press (listed separately per OCGS instructions)", forth))
doc.append(sec("Creative and Professional Work", CV["creative"]))
(OUT / "Bergmann-CV-OCGS.md").write_text("\n".join(doc))

# ---------- 3. SSHRC Research Contributions (six-year window) ----------
w = lambda key: [e for e in CV[key] if in_window(e)]
doc = [f"# Research Contributions and Relevant Experience — {P['name']}\n\n*Six-year window: contributions since {SIX_YEARS_AGO.isoformat()}. \\* = resulted from previous SSHRC support.*\n\n<!-- Generated {TODAY.isoformat()}; prose sections (significance, training narrative, relevant experience) live in prose/sshrc-prose.md and are appended below. -->\n"]
doc.append("\n# 1. Research Contributions Over the Last Six Years\n")
doc.append(sec("Refereed contributions", [e for e in w("publications") if e.get("refereed")], star=True))
doc.append(sec("Other refereed contributions", [e for e in w("presentations") + w("posters") if e.get("other_refereed")], star=True))
nonref = [e for e in w("publications") if not e.get("refereed")] + w("invited_talks")
doc.append(sec("Non-refereed contributions", nonref, star=True))
sshrc_forth = [e for e in CV["forthcoming"] if not e.get("sshrc_exclude")]
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

print(f"Built 4 documents in output/ (six-year window: since {SIX_YEARS_AGO.isoformat()})")

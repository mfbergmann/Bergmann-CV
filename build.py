#!/usr/bin/env python3
"""Build all CV formats from cv.yaml. Outputs markdown to output/;
the GitHub Action (or local pandoc) converts markdown to docx/pdf."""
import yaml, datetime, pathlib

CV = yaml.safe_load(open(pathlib.Path(__file__).parent / "cv.yaml"))
OUT = pathlib.Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)
TODAY = datetime.date.today()
SIX_YEARS_AGO = TODAY.replace(year=TODAY.year - 6)

def year(e):
    return str(e.get("date", ""))[:4]

def dstr(e):
    d, end = str(e.get("date", "")), e.get("end")
    d = d[:7] if len(d) > 7 else d
    if end:
        end = "present" if str(end) == "present" else str(end)[:7]
        return f"{d} – {end}"
    return d

def in_window(e):
    try:
        return int(year(e)) >= SIX_YEARS_AGO.year or str(e.get("end")) == "present"
    except ValueError:
        return True

def sec(title, entries, star=False, dated=True):
    lines = [f"\n## {title}\n"]
    for e in entries:
        mark = "\\* " if (star and e.get("sshrc")) else ""
        pre = f"**{dstr(e)}** — " if dated and e.get("date") else ""
        lines.append(f"- {mark}{pre}{e['text']}")
    return "\n".join(lines) + "\n"

def strsec(title, items):
    return f"\n## {title}\n\n" + "\n".join(f"- {i}" for i in items) + "\n"

P = CV["personal"]
head = (f"# {P['name']}\n\n{P['title']}  \nORCID: {P['orcid']} · {P['email']} · {P['website']}\n\n"
        f"*Generated {TODAY.isoformat()} from cv.yaml — do not edit outputs directly.*\n")

# ---------- 1. Complete CV ----------
doc = [head.replace("# ", "# Curriculum Vitae — ")]
doc.append(sec("Employment", CV["employment"]))
doc.append(sec("Education", CV["education"]))
doc.append(sec("Teaching Training and Certifications", CV["qualifications"]))
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
doc.append(f"\n## Graduate Supervision\n\n{CV['supervision']['summary']}\n")
doc += [f"- {e['text']}" for e in CV["supervision"]["entries"]]
doc.append(strsec("Courses Taught", CV["teaching"]))
doc.append(sec("Service", CV["service"]))
doc.append(sec("Memberships and Collectives", CV["memberships"]))
doc.append(sec("Interviews and Media", CV["interviews"]))
(OUT / "Bergmann-CV-Complete.md").write_text("\n".join(doc))

# ---------- 2. OCGS-ordered CV ----------
doc = [head.replace("# ", "# OCGS Curriculum Vitae — ")]
doc.append(sec("A. Education", CV["education"]))
doc.append(sec("B. Employment History", CV["employment"]))
doc.append(f"\n## C. Graduate Supervision\n\n{CV['supervision']['summary']}\n")
doc += [f"- {e['text']}" for e in CV["supervision"]["entries"]]
doc.append(sec("D. External Research Funding", CV["funding_external"]))
doc.append(sec("E. Internal Research Funding", CV["funding_internal"]))
doc.append(sec("F. Publications", CV["publications"]))
doc.append(sec("G. Conference Presentations", CV["presentations"] + CV["posters"]))
doc.append(sec("H. Creative and Professional Work", CV["creative"]))
doc.append(sec("I. Service and Professional Activities", CV["service"] + CV["memberships"]))
(OUT / "Bergmann-CV-OCGS.md").write_text("\n".join(doc))

# ---------- 3. SSHRC Research Contributions (six-year window) ----------
w = lambda key: [e for e in CV[key] if in_window(e)]
doc = [f"# Research Contributions and Relevant Experience — {P['name']}\n\n*Six-year window: contributions since {SIX_YEARS_AGO.isoformat()}. \\* = resulted from previous SSHRC support. Generated {TODAY.isoformat()}; prose sections (significance, training narrative, relevant experience) live in prose/sshrc-prose.md and are appended below.*\n"]
doc.append("\n# 1. Research Contributions Over the Last Six Years\n")
doc.append(sec("Refereed contributions", [e for e in w("publications") if e.get("refereed")], star=True))
doc.append(sec("Other refereed contributions", [e for e in w("presentations") + w("posters") if e.get("other_refereed")], star=True))
nonref = [e for e in w("publications") if not e.get("refereed")] + w("invited_talks")
doc.append(sec("Non-refereed contributions", nonref, star=True))
doc.append(sec("Forthcoming contributions", [{**e, "text": f"{e['text']} Status: {e.get('status','')}"} for e in CV["forthcoming"]]))
doc.append(sec("Creative outputs", w("creative")))
prose = pathlib.Path(__file__).parent / "prose" / "sshrc-prose.md"
if prose.exists():
    doc.append("\n" + prose.read_text())
(OUT / "Bergmann-SSHRC-Contributions.md").write_text("\n".join(doc))

print(f"Built 3 documents in output/ (six-year window: since {SIX_YEARS_AGO.isoformat()})")

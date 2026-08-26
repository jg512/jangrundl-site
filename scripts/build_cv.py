#!/usr/bin/env python3
"""Build the downloadable CV PDF.

Single column, US-resume shape on A4. Every number in here is sourced -- see
SOURCES at the bottom. Nothing is inferred or rounded up; if a figure could not
be verified it is left out rather than estimated.

    pip install fpdf2 && python3 scripts/build_cv.py
"""

from pathlib import Path
from fpdf import FPDF

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "cv" / "Jan_Grundl_CV.pdf"
FONTS = Path("/usr/share/fonts/truetype/lato")

INK = (26, 26, 23)
SOFT = (74, 72, 66)
MUTED = (110, 107, 99)
ACCENT = (45, 90, 61)
RULE = (206, 202, 194)

NAME = "Jan Victornino Grundl"
TAGLINE = "M.Sc. Computer Science student · AI, software engineering, IoT"
CONTACT = [
    ("janvictorninogrundl@gmail.com", "mailto:janvictorninogrundl@gmail.com"),
    ("jangrundl.de", "https://www.jangrundl.de"),
    ("github.com/jg512", "https://github.com/jg512"),
    ("linkedin.com/in/jan-victornino-grundl-722645357",
     "https://www.linkedin.com/in/jan-victornino-grundl-722645357/"),
    ("Rostock, Germany", None),
]

SUMMARY = (
    "Computer science master's student in Rostock, working as a research assistant on LLM agents "
    "and on IoT sensor systems for animal health, and as a software developer modernising the software "
    "of a 920-berth marina. Comfortable from microcontroller firmware up to Django backends, and "
    "most interested in systems that have to keep working outside a demo."
)

EXPERIENCE = [
    dict(
        org="Yachthafenresidenz Hohe Düne", url="https://www.hohe-duene.de/",
        role="Software Developer, Digitalisation & Full-Stack Development",
        when="Jul 2026 - Present", where="Rostock, Germany",
        bullets=[
            "Architected and developed a new ERP and marina management system to replace the legacy "
            "platform, modernising operations for a 920-berth marina, the largest in "
            "Mecklenburg-Vorpommern and the first in Germany to hold a five-star classification.",
            "Modernising the digital infrastructure across hotel and harbour software, databases and web; "
            "reporting directly to the owner.",
            "Audited the legacy Java systems for code quality and security issues and drafted the "
            "migration path to a Django and PostgreSQL data model.",
        ],
    ),
    dict(
        org="Fraunhofer IGD / University of Rostock", url="https://www.igd.fraunhofer.de/",
        role="Research Assistant · KI-TIERWOHL, work package AP 6",
        when="Feb 2026 - Present", where="Rostock, Germany",
        bullets=[
            "Work package AP 6 (technologies for welfare recognition) of KI-TIERWOHL, a €5 million "
            "excellence-research consortium of eight work packages, "
            "funded from the ERDF programme of Mecklenburg-Vorpommern; seven consortium partners and four associated partners.",
            "Built the calf smart jacket: detects respiratory problems in calves from audio and "
            "accelerometer data, using contactless welfare indicators.",
            "Ran measurement campaigns at consortium partner FBN Dummerstorf; built the data pipelines, "
            "annotation and ML workflows in PyTorch, OpenCV and CVAT.",
        ],
    ),
    dict(
        org="University of Rostock, Chair of Software Engineering",
        url="https://www.informatik.uni-rostock.de/lehrstuehle/am-institut-fuer-informatik-forts/software-engineering/",
        role="Research Assistant", when="Dec 2025 - Present", where="Rostock, Germany",
        bullets=[
            "Designed a semi-autonomous LLM agent using ReAct prompting, tool use and MCP that generates "
            "and checks UML class diagrams from source repositories (AI4SE).",
            "Built the evaluation dataset and implemented the system in Python on the Hugging Face stack.",
        ],
    ),
    dict(
        org="Ossinity GmbH", url="https://de.linkedin.com/company/ossinity",
        role="AI Developer", when="Nov 2025 - Jun 2026", where="Rostock, Germany",
        bullets=[
            "Annotated MRI scans in 3D Slicer for AI-assisted cancer detection, and ran evaluation and "
            "testing in Python.",
        ],
    ),
    dict(
        org="University of Rostock, Chair of Integrated Systems", url=None,
        role="Teaching Assistant", when="May 2025 - Nov 2025", where="Rostock, Germany",
        bullets=[
            "Planned, recorded and edited modular teaching videos on computer architecture for reusable "
            "course formats.",
        ],
    ),
    dict(
        org="University of Rostock, Juniorstudium", url="https://www.uni-rostock.de/studium/studienorientierung/juniorstudium/",
        role="Tutor", when="Sep 2023 - Nov 2025", where="Rostock, Germany",
        bullets=[
            "Taught 30+ prospective computer science students per semester in AI basics, mathematics, "
            "logic and programming: tutorials, exercise sessions and hands-on labs.",
            "Wrote the course materials.",
        ],
    ),
]

PROJECTS = [
    dict(
        org="Summer of Solutions · The Future Living and Fraunhofer IGP", url="https://www.thefutureliving.com/summer-of-solutions-en/",
        role="Practice-transfer project with Nordwasser GmbH", when="Apr 2026 - Jul 2026",
        bullets=[
            "Responsible for technical concept, architecture and data protection in a team of five "
            "master's students; one of 13 practice partners and 60+ students in the 2026 cohort.",
            "Designed a vendor-independent telematics concept for 138 vehicles over OBD dongles, keeping "
            "the data in-house; delivered a 40+ page specification with a cost-benefit calculation, "
            "CO₂ estimate and rollout plan.",
        ],
    ),
    dict(
        org="AI Hackathon, Cheftreff Hamburg", url=None,
        role="Case by Finanz Informatik · Top 3 of 300+ participants", when="Apr 2026",
        bullets=[
            "\"Aline\", an AI assistant wired into Jira, GitHub and Teams that helps the business side with "
            "requirements during development.",
        ],
    ),
    dict(
        org="Healthcare Hackathon Berlin", url=None,
        role="Case with caire", when="Jul 2026",
        bullets=[
            "Estimated vital parameters from video (remote PPG), with LLM-based evaluation and alerting "
            "tied into the patient history.",
        ],
    ),
]

OPEN_SOURCE = [
    dict(
        org="rfidpoll", url="https://github.com/FBN-Dummerstorf/rfidpoll",
        role="Published by FBN Dummerstorf, out of the KI-TIERWOHL project", when="2026",
        bullets=[
            "Reads FEIG OBID RFID readers over TCP and writes every detected tag to CSV; built for gapless "
            "capture, deduplicating across restarts. Runs as a systemd service with a YAML config and a "
            "mock reader for hardware-free testing.",
            "In use in a year-long animal behaviour study in the barn.",
        ],
    ),
    dict(
        org="ArbiterMed-MCP", url="https://github.com/jg512/ArbiterMed-MCP",
        role="MCP server for evidence-based medical research", when="2026",
        bullets=[
            "Extracts hazard ratios and p-values from studies as structured data and rates how directly a "
            "study answers the question asked (PICO directness). No dependencies.",
        ],
    ),
]

EDUCATION = [
    ("University of Rostock", "M.Sc. Computer Science, focus on AI, software engineering and IoT",
     "Oct 2025 - Present", "Current average 1.7 (German scale); expected Apr 2027"),
    ("University of Rostock", "B.Sc. Computer Science",
     "Oct 2020 - Oct 2025", "Final grade 2.4, thesis 1.3; extended while working to support family"),
    ("Schulcampus Evershagen, Rostock", "Abitur", "until Jun 2020", None),
]

SKILLS = [
    ("Languages", "Python, Java, C/C++, SQL, TypeScript"),
    ("ML & AI", "PyTorch, OpenCV, Hugging Face, LLM agents, MCP, ReAct prompting, CVAT"),
    ("Backend & Data", "Django, PostgreSQL, SQLite, MongoDB"),
    ("Embedded & Tools", "ESP32, Arduino, Raspberry Pi, Linux, Docker, Git"),
    ("Spoken", "German (native), English (C1), Spanish (basic)"),
]

VOLUNTEERING = (
    "NALA AI: open-source developer on AI-assisted water monitoring, shown at re:publica 2026. "
    "BYTE Challenge: free online STEM courses for disadvantaged school students, under the Gesellschaft "
    "für Informatik. Student council (StuRa), University of Rostock. Member, Gesellschaft für Informatik e.V."
)

M = 15          # page margin, mm
LINE = 4.1      # body leading


class CV(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("Lato", "", 7.5)
        self.set_text_color(*MUTED)
        self.cell(0, 4, f"Jan Victornino Grundl  ·  page {self.page_no()} of {{nb}}", align="C")


def rule(pdf, gap_before=1.4, gap_after=1.8):
    pdf.ln(gap_before)
    pdf.set_draw_color(*RULE)
    pdf.set_line_width(0.25)
    y = pdf.get_y()
    pdf.line(M, y, pdf.w - M, y)
    pdf.ln(gap_after)


def section(pdf, title):
    if pdf.get_y() > pdf.h - 45:
        pdf.add_page()
    pdf.ln(2.2)
    pdf.set_font("Lato", "B", 9.5)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 4.6, "  ".join(title.upper()), new_x="LMARGIN", new_y="NEXT")
    rule(pdf, gap_before=0.8, gap_after=2.0)


def entry(pdf, org, role, when, where=None, url=None, bullets=(), keep=26):
    """One experience/project block. `keep` mm of room needed before it starts."""
    if pdf.get_y() > pdf.h - keep:
        pdf.add_page()
    w = pdf.w - 2 * M

    pdf.set_font("Lato", "B", 10)
    pdf.set_text_color(*INK)
    pdf.cell(w * 0.66, 4.6, org, link=url or "")
    pdf.set_font("Lato", "", 8.8)
    pdf.set_text_color(*MUTED)
    pdf.cell(w * 0.34, 4.6, when, align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Lato", "I", 9.2)
    pdf.set_text_color(*SOFT)
    pdf.cell(w * 0.66, 4.4, role)
    if where:
        pdf.set_font("Lato", "I", 8.6)
        pdf.set_text_color(*MUTED)
        pdf.cell(w * 0.34, 4.4, where, align="R")
    pdf.ln(5.0)

    pdf.set_font("Lato", "", 9.2)
    pdf.set_text_color(*SOFT)
    for b in bullets:
        x0 = pdf.get_x()
        pdf.set_text_color(*ACCENT)
        pdf.cell(3.6, LINE, chr(0x2022))
        pdf.set_text_color(*SOFT)
        pdf.set_x(x0 + 3.6)
        pdf.multi_cell(w - 3.6, LINE, b, align="L", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.5)
    pdf.ln(1.6)


def build():
    pdf = CV(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(M, 13, M)
    for style, f in (("", "Lato-Regular.ttf"), ("B", "Lato-Bold.ttf"),
                     ("I", "Lato-Italic.ttf"), ("BI", "Lato-BoldItalic.ttf")):
        pdf.add_font("Lato", style, str(FONTS / f))
    pdf.set_title(f"{NAME} - CV")
    pdf.set_author(NAME)
    pdf.add_page()
    w = pdf.w - 2 * M

    # ---- header ----
    top = pdf.get_y()
    pdf.set_font("Lato", "B", 21)
    pdf.set_text_color(*INK)
    pdf.set_xy(M, top)
    pdf.cell(w * 0.55, 9, NAME, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Lato", "", 9.6)
    pdf.set_text_color(*MUTED)
    pdf.set_x(M)
    pdf.cell(w * 0.55, 5, TAGLINE, new_x="LMARGIN", new_y="NEXT")
    left_end = pdf.get_y()

    y = top + 1.2
    for label, href in CONTACT:
        pdf.set_xy(M + w * 0.55, y)
        pdf.set_font("Lato", "", 8.4)
        pdf.set_text_color(*(ACCENT if href else MUTED))
        pdf.cell(w * 0.45, 4.3, label, align="R", link=href or "")
        y += 4.3
    pdf.set_y(max(left_end, y))

    rule(pdf, gap_before=1.6, gap_after=2.4)
    pdf.set_font("Lato", "", 9.3)
    pdf.set_text_color(*SOFT)
    pdf.multi_cell(w, LINE, SUMMARY, align="L", new_x="LMARGIN", new_y="NEXT")

    section(pdf, "Experience")
    for e in EXPERIENCE:
        entry(pdf, **e)

    section(pdf, "Projects & Competitions")
    for e in PROJECTS:
        entry(pdf, **e)

    section(pdf, "Open Source")
    for e in OPEN_SOURCE:
        entry(pdf, **e)

    section(pdf, "Education")
    for org, deg, when, note in EDUCATION:
        if pdf.get_y() > pdf.h - 26:
            pdf.add_page()
        pdf.set_font("Lato", "B", 10)
        pdf.set_text_color(*INK)
        pdf.cell(w * 0.66, 4.6, org)
        pdf.set_font("Lato", "", 8.8)
        pdf.set_text_color(*MUTED)
        pdf.cell(w * 0.34, 4.6, when, align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Lato", "I", 9.2)
        pdf.set_text_color(*SOFT)
        pdf.multi_cell(w, 4.4, deg, new_x="LMARGIN", new_y="NEXT")
        if note:
            pdf.set_font("Lato", "", 8.8)
            pdf.set_text_color(*MUTED)
            pdf.multi_cell(w, 4.0, note, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1.8)

    section(pdf, "Technical Skills")
    for label, val in SKILLS:
        if pdf.get_y() > pdf.h - 22:
            pdf.add_page()
        pdf.set_font("Lato", "B", 9)
        pdf.set_text_color(*INK)
        pdf.cell(30, LINE + 0.4, label)
        pdf.set_font("Lato", "", 9.2)
        pdf.set_text_color(*SOFT)
        pdf.multi_cell(w - 30, LINE + 0.4, val, new_x="LMARGIN", new_y="NEXT")

    section(pdf, "Volunteering")
    pdf.set_font("Lato", "", 9.2)
    pdf.set_text_color(*SOFT)
    pdf.multi_cell(w, LINE, VOLUNTEERING, align="L", new_x="LMARGIN", new_y="NEXT")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT))
    print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size/1024:.0f} KB, {pdf.page_no()} pages)")


# SOURCES for every figure above, checked 2026-08-25:
#   EUR 5 million / ERDF / 8 work packages / AP 6 ...... ki-tierwohl.de, ki-tierwohl.de/efre,
#                                                        regierung-mv.de (EXF-25-1031..1038)
#   920 berths, first 5-star marina in Germany ......... hohe-duene.de/yachthafen,
#                                                        yachthafen-hohe-duene.de
#   largest marina in Mecklenburg-Vorpommern ........... Jan's LinkedIn profile, 2026-08-26
#   138 vehicles, 40+ page specification, team of 5 .... Jan's own CV (cv_jan_grundl.pdf)
#   13 practice partners, 60+ students ................. thefutureliving.com
#   Top 3 of 300+ participants ......................... Jan's own CV
#   30+ pupils per semester ............................ Jan, this session
#   grades 1.7 / 2.4 / 1.3 ............................. Jan, this session + his CV
# Deliberately NOT claimed: "one of Germany's biggest private marinas" (no source says this);
# any Juniorstudium head-count (the university publishes none).

if __name__ == "__main__":
    build()

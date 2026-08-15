"""
pdf_generator.py
================
Generates professional PDF resumes and cover letters using reportlab.
Pure Python — no LaTeX/pdflatex needed. Works on Streamlit Cloud.
"""

import os
import io
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, KeepTogether
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from config import OUTPUT_DIR

# ── Colours ──────────────────────────────────────────────────────────────────
NAVY   = HexColor("#000000")   # Black headings like LaTeX
DARK   = HexColor("#1a1a1a")
GREY   = HexColor("#444444")
LGREY  = HexColor("#f0f0f0")
RULE   = HexColor("#000000")   # Black rule like LaTeX


# ── Style factory ─────────────────────────────────────────────────────────────

def _styles():
    # Name: \LARGE\bfseries — ~24pt bold centred
    name = ParagraphStyle("Name",
        fontSize=22, leading=26, textColor=DARK,
        fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=2)

    # Headline: smaller centred italic under name
    headline = ParagraphStyle("Headline",
        fontSize=9.5, leading=13, textColor=DARK,
        fontName="Helvetica-Oblique", alignment=TA_CENTER, spaceAfter=2)

    # Contact: centred small, pipe-separated
    contact = ParagraphStyle("Contact",
        fontSize=9, leading=12, textColor=DARK,
        fontName="Helvetica", alignment=TA_CENTER, spaceAfter=4)

    # Section: bold uppercase, rule follows via _rule()
    section = ParagraphStyle("Section",
        fontSize=10, leading=13, textColor=DARK,
        fontName="Helvetica-Bold", spaceBefore=9, spaceAfter=0)

    # Job title row — bold left
    job_title = ParagraphStyle("JobTitle",
        fontSize=10, leading=13, textColor=DARK,
        fontName="Helvetica-Bold", spaceBefore=5, spaceAfter=0)

    # Job title right (date)
    job_date = ParagraphStyle("JobDate",
        fontSize=10, leading=13, textColor=DARK,
        fontName="Helvetica-Oblique", alignment=TA_RIGHT, spaceBefore=5, spaceAfter=0)

    # Company / sub line — italic
    job_sub = ParagraphStyle("JobSub",
        fontSize=9.5, leading=12, textColor=DARK,
        fontName="Helvetica-Oblique", spaceAfter=1)

    # Small italic context description under company
    job_context = ParagraphStyle("JobContext",
        fontSize=8.5, leading=11, textColor=GREY,
        fontName="Helvetica-Oblique", spaceAfter=3)

    # Bullet point — 9pt, indented
    bullet = ParagraphStyle("Bullet",
        fontSize=9, leading=13, textColor=DARK,
        fontName="Helvetica", leftIndent=14, firstLineIndent=-9,
        spaceAfter=1.5)

    # Summary / body — justified
    summary = ParagraphStyle("Summary",
        fontSize=10, leading=14.5, textColor=DARK,
        fontName="Helvetica", spaceAfter=4, alignment=TA_JUSTIFY)

    # Skills table — category cell (bold)
    skill_cat = ParagraphStyle("SkillCat",
        fontSize=9, leading=13, textColor=DARK,
        fontName="Helvetica-Bold", spaceAfter=0)

    # Skills table — value cell
    skill_val = ParagraphStyle("SkillVal",
        fontSize=9, leading=13, textColor=DARK,
        fontName="Helvetica", spaceAfter=0)

    # Education title
    edu_title = ParagraphStyle("EduTitle",
        fontSize=10, leading=13, textColor=DARK,
        fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=0)

    # Education sub
    edu_sub = ParagraphStyle("EduSub",
        fontSize=9.5, leading=12, textColor=DARK,
        fontName="Helvetica", spaceAfter=2)

    # Cert plain line
    cert = ParagraphStyle("Cert",
        fontSize=9, leading=13, textColor=DARK,
        fontName="Helvetica", spaceAfter=1)

    # Achievement bullet (bold award name inline)
    ach = ParagraphStyle("Ach",
        fontSize=9, leading=13, textColor=DARK,
        fontName="Helvetica", leftIndent=14, firstLineIndent=-9,
        spaceAfter=1.5)

    # Cover letter styles
    cl_body = ParagraphStyle("CLBody",
        fontSize=11, leading=16, textColor=DARK,
        fontName="Helvetica", spaceAfter=10, alignment=TA_JUSTIFY)

    cl_name = ParagraphStyle("CLName",
        fontSize=16, leading=20, textColor=DARK,
        fontName="Helvetica-Bold", spaceAfter=4)

    cl_contact = ParagraphStyle("CLContact",
        fontSize=10, leading=13, textColor=GREY,
        fontName="Helvetica", spaceAfter=16)

    return dict(
        name=name, headline=headline, contact=contact, section=section,
        job_title=job_title, job_date=job_date, job_sub=job_sub,
        job_context=job_context, bullet=bullet,
        summary=summary, skill_cat=skill_cat, skill_val=skill_val,
        edu_title=edu_title, edu_sub=edu_sub, cert=cert, ach=ach,
        cl_body=cl_body, cl_name=cl_name, cl_contact=cl_contact,
    )


def _rule():
    return HRFlowable(width="100%", thickness=0.6, color=RULE,
                      spaceAfter=3, spaceBefore=1)


def _safe(val: Any) -> str:
    """Convert value to string, escape XML special chars for reportlab."""
    s = str(val) if val else ""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return s


# ── Resume PDF ────────────────────────────────────────────────────────────────

def generate_resume_pdf(resume_data: dict, output_path: str) -> str:
    """Generate a professional resume PDF matching the LaTeX reference format."""
    import json as _json
    if isinstance(resume_data, str):
        try:
            resume_data = _json.loads(resume_data)
        except Exception:
            resume_data = {}
    if not isinstance(resume_data, dict):
        resume_data = {}

    # ── Inline normalise: guarantee all list-of-dict fields are dicts ───────
    def _norm_list(lst, str_key: str) -> list:
        out = []
        for x in (lst if isinstance(lst, list) else []):
            if isinstance(x, dict):
                out.append(x)
            elif isinstance(x, str) and x.strip():
                out.append({str_key: x.strip()})
        return out

    resume_data["experience"]     = _norm_list(resume_data.get("experience",     []), "title")
    resume_data["education"]      = _norm_list(resume_data.get("education",      []), "degree")
    resume_data["projects"]       = _norm_list(resume_data.get("projects",       []), "name")
    resume_data["certifications"] = _norm_list(resume_data.get("certifications", []), "name")

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    # A4 paper to match LaTeX a4paper
    from reportlab.lib.pagesizes import A4
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=0.72*inch, rightMargin=0.72*inch,
        topMargin=0.62*inch,  bottomMargin=0.62*inch,
    )

    st    = _styles()
    elems = []
    d     = resume_data
    # page width minus margins for table colWidths
    pw = A4[0] - 1.44*inch

    # ── \LARGE\bfseries NAME ────────────────────────────────────────────────
    elems.append(Paragraph(_safe(d.get("full_name", "")), st["name"]))

    # ── Headline (Senior Software Engineer --- ...) ──────────────────────────
    if d.get("headline"):
        elems.append(Paragraph(_safe(d["headline"]), st["headline"]))

    # ── Contact: location --- email | phone | linkedin | github ─────────────
    loc   = _safe(d.get("location", ""))
    email = _safe(d.get("email", ""))
    phone = _safe(d.get("phone", ""))
    li    = d.get("linkedin", "")
    gh    = d.get("github", "")

    line1_parts = []
    if loc:   line1_parts.append(loc)
    if phone: line1_parts.append(phone)
    if email: line1_parts.append(f'<link href="mailto:{email}">{email}</link>')
    line2_parts = []
    if gh:    line2_parts.append(f'<link href="{_safe(gh)}">{_safe(gh)}</link>')
    if li:    line2_parts.append(f'<link href="{_safe(li)}">{_safe(li)}</link>')

    contact_sep = " $|$ "
    if line1_parts:
        elems.append(Paragraph(" --- ".join(line1_parts[:1]) + (" $|$ " + " $|$ ".join(line1_parts[1:]) if len(line1_parts) > 1 else ""), st["contact"]))
    if line2_parts:
        elems.append(Paragraph(" $|$ ".join(line2_parts), st["contact"]))
    elems.append(Spacer(1, 3))

    # ── PROFESSIONAL SUMMARY ────────────────────────────────────────────────
    if d.get("summary"):
        elems.append(Paragraph("PROFESSIONAL SUMMARY", st["section"]))
        elems.append(_rule())
        elems.append(Paragraph(_safe(d["summary"]), st["summary"]))

    # ── TECHNICAL SKILLS  (2-col table: bold category | skill list) ─────────
    skill_cats = d.get("skill_categories", [])
    skills_flat = d.get("skills", {})

    # Build rows — prefer skill_categories, fall back to flat skills dict
    skill_rows = []
    if skill_cats:
        for cat in skill_cats:
            cat_name  = _safe(cat.get("category", ""))
            cat_vals  = ", ".join(_safe(s) for s in cat.get("skills", []) if s)
            if cat_name and cat_vals:
                skill_rows.append((cat_name, cat_vals))
    else:
        label_map = [
            ("technical_skills",   "Technical Skills"),
            ("tools_technologies", "Tools & Technologies"),
            ("soft_skills",        "Soft Skills"),
        ]
        for key, label in label_map:
            vals = skills_flat.get(key, [])
            if vals:
                skill_rows.append((label, ", ".join(vals)))

    if skill_rows:
        elems.append(Paragraph("TECHNICAL SKILLS", st["section"]))
        elems.append(_rule())
        CAT_W = 1.55*inch   # ~4.10cm
        VAL_W = pw - CAT_W
        tdata = [
            [Paragraph(f"<b>{r[0]}</b>", st["skill_cat"]),
             Paragraph(r[1], st["skill_val"])]
            for r in skill_rows
        ]
        sk_tbl = Table(tdata, colWidths=[CAT_W, VAL_W], hAlign="LEFT")
        sk_tbl.setStyle(TableStyle([
            ("VALIGN",       (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING",  (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 4),
            ("TOPPADDING",   (0,0), (-1,-1), 2),
            ("BOTTOMPADDING",(0,0), (-1,-1), 2),
        ]))
        elems.append(sk_tbl)

    # ── PROFESSIONAL EXPERIENCE ─────────────────────────────────────────────
    experience = d.get("experience", [])
    if experience:
        elems.append(Paragraph("PROFESSIONAL EXPERIENCE", st["section"]))
        elems.append(_rule())
        for job in experience:
            title    = _safe(job.get("title", ""))
            company  = _safe(job.get("company", ""))
            location = _safe(job.get("location", ""))
            start    = _safe(job.get("start_date", ""))
            end      = _safe(job.get("end_date", ""))
            context  = _safe(job.get("context", ""))   # optional short description

            # Row: "Bold Title" left  \hfill  italic date right
            t_para = Paragraph(f"<b>{title}</b>", st["job_title"])
            d_para = Paragraph(f"<i>{start} -- {end}</i>", st["job_date"])
            hdr_t  = Table([[t_para, d_para]], colWidths=[pw*0.62, pw*0.38])
            hdr_t.setStyle(TableStyle([
                ("VALIGN",       (0,0),(-1,-1),"TOP"),
                ("LEFTPADDING",  (0,0),(-1,-1),0),
                ("RIGHTPADDING", (0,0),(-1,-1),0),
                ("TOPPADDING",   (0,0),(-1,-1),0),
                ("BOTTOMPADDING",(0,0),(-1,-1),0),
            ]))

            # Company --- Location (italic)
            co_str = company
            if location: co_str += f" --- {location}"
            co_para = Paragraph(f"<i>{co_str}</i>", st["job_sub"])

            block = [hdr_t, co_para]
            if context:
                block.append(Paragraph(f"<i>{context}</i>", st["job_context"]))

            elems.append(KeepTogether(block))

            for b in job.get("bullets", []):
                elems.append(Paragraph(f"\u2022  {_safe(b)}", st["bullet"]))
            elems.append(Spacer(1, 5))

    # ── OPEN SOURCE / ADDITIONAL EXPERIENCE ─────────────────────────────────
    oss = d.get("open_source", [])
    if oss:
        elems.append(Paragraph("OPEN SOURCE CONTRIBUTIONS", st["section"]))
        elems.append(_rule())
        for proj in oss:
            name = _safe(proj.get("name",""))
            url  = _safe(proj.get("url",""))
            date_str = _safe(proj.get("date",""))
            name_para = Paragraph(f"<b>{name}</b>" + (f' -- <link href="{url}">{url}</link>' if url else ""), st["job_title"])
            if date_str:
                d_para2 = Paragraph(f"<i>{date_str}</i>", st["job_date"])
                ht2 = Table([[name_para, d_para2]], colWidths=[pw*0.70, pw*0.30])
                ht2.setStyle(TableStyle([
                    ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),0),
                    ("RIGHTPADDING",(0,0),(-1,-1),0),("TOPPADDING",(0,0),(-1,-1),0),
                    ("BOTTOMPADDING",(0,0),(-1,-1),0),
                ]))
                elems.append(ht2)
            else:
                elems.append(name_para)
            for b in proj.get("bullets", []):
                elems.append(Paragraph(f"\u2022  {_safe(b)}", st["bullet"]))
            elems.append(Spacer(1, 4))

    # ── SELECTED PROJECTS ───────────────────────────────────────────────────
    projects = [p for p in d.get("projects", []) if p.get("name")]
    if projects:
        elems.append(Paragraph("SELECTED PROJECTS", st["section"]))
        elems.append(_rule())
        for p in projects:
            pname  = _safe(p.get("name",""))
            pyear  = _safe(p.get("year","") or "")
            pdesc  = _safe(p.get("description",""))
            tech   = ", ".join(_safe(s) for s in (p.get("technologies") or []) if s)
            pbulls = p.get("bullets", [])

            name_p = Paragraph(f"<b>{pname}</b>", st["job_title"])
            if pyear:
                yr_p  = Paragraph(f"<i>{pyear}</i>", st["job_date"])
                ht3   = Table([[name_p, yr_p]], colWidths=[pw*0.72, pw*0.28])
                ht3.setStyle(TableStyle([
                    ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),0),
                    ("RIGHTPADDING",(0,0),(-1,-1),0),("TOPPADDING",(0,0),(-1,-1),0),
                    ("BOTTOMPADDING",(0,0),(-1,-1),0),
                ]))
                elems.append(ht3)
            else:
                elems.append(name_p)

            if pdesc and not pbulls:
                # single description line (no sub-bullets)
                elems.append(Paragraph(pdesc, st["job_sub"]))
            for b in pbulls:
                elems.append(Paragraph(f"\u2022  {_safe(b)}", st["bullet"]))
            # italic stack line at bottom like LaTeX \textit{Stack: ...}
            if tech:
                elems.append(Paragraph(f"<i>Stack: {tech}</i>", st["job_context"]))
            elems.append(Spacer(1, 4))

    # ── ACHIEVEMENTS & CERTIFICATIONS ───────────────────────────────────────
    achievements = d.get("achievements", d.get("awards", []))
    raw_certs    = d.get("certifications", [])
    certs        = [c for c in raw_certs if (isinstance(c, dict) and c.get("name")) or isinstance(c, str)]

    if achievements or certs:
        elems.append(Paragraph("ACHIEVEMENTS &amp; CERTIFICATIONS", st["section"]))
        elems.append(_rule())

    if achievements:
        for a in achievements:
            text = _safe(a.get("text", a) if isinstance(a, dict) else a)
            title_part = _safe(a.get("title", "")) if isinstance(a, dict) else ""
            if title_part and text:
                elems.append(Paragraph(f"\u2022  <b>{title_part}:</b> {text}", st["ach"]))
            elif text:
                elems.append(Paragraph(f"\u2022  {text}", st["ach"]))

    if certs:
        elems.append(Spacer(1, 4))
        # Render as 2-col table: name left, status/year right  (like LaTeX tabular)
        cert_rows = []
        for c in certs:
            if isinstance(c, str):
                # try to parse "Name --- Issuer (Status)"
                cert_rows.append((c, ""))
            else:
                cname   = _safe(c.get("name",""))
                issuer  = _safe(c.get("issuer",""))
                cyear   = _safe(c.get("year",""))
                status  = _safe(c.get("status",""))
                left    = cname + (f" --- {issuer}" if issuer else "")
                right   = status or (f"({cyear})" if cyear else "")
                cert_rows.append((left, right))
        if cert_rows:
            cdata = [
                [Paragraph(_safe(r[0]), st["cert"]),
                 Paragraph(_safe(r[1]), ParagraphStyle("CR", parent=st["cert"], alignment=TA_RIGHT))]
                for r in cert_rows
            ]
            c_tbl = Table(cdata, colWidths=[pw*0.72, pw*0.28], hAlign="LEFT")
            c_tbl.setStyle(TableStyle([
                ("VALIGN",       (0,0),(-1,-1),"TOP"),
                ("LEFTPADDING",  (0,0),(-1,-1),0),
                ("RIGHTPADDING", (0,0),(-1,-1),0),
                ("TOPPADDING",   (0,0),(-1,-1),1),
                ("BOTTOMPADDING",(0,0),(-1,-1),1),
            ]))
            elems.append(c_tbl)

    # ── EDUCATION ──────────────────────────────────────────────────────────
    education = d.get("education", [])
    if education:
        elems.append(Paragraph("EDUCATION", st["section"]))
        elems.append(_rule())
        for edu in education:
            degree = _safe(edu.get("degree", ""))
            field  = _safe(edu.get("field", ""))
            inst   = _safe(edu.get("institution", ""))
            year   = _safe(edu.get("graduation_year", ""))
            gpa    = edu.get("gpa", "") or ""

            # "Bold Degree --- Field" left, italic year right
            deg_str  = f"{degree} ({field})" if field else degree
            deg_p    = Paragraph(f"<b>{deg_str}</b>", st["edu_title"])
            yr_p     = Paragraph(f"<i>{year}</i>",
                ParagraphStyle("YR2", parent=st["edu_title"], alignment=TA_RIGHT,
                               fontName="Helvetica-Oblique"))
            et = Table([[deg_p, yr_p]], colWidths=[pw*0.72, pw*0.28])
            et.setStyle(TableStyle([
                ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),0),
                ("RIGHTPADDING",(0,0),(-1,-1),0),("TOPPADDING",(0,0),(-1,-1),0),
                ("BOTTOMPADDING",(0,0),(-1,-1),0),
            ]))
            elems.append(et)
            inst_str = inst
            if gpa and gpa not in ("optional", ""):
                inst_str += f", GPA: {_safe(str(gpa))}"
            elems.append(Paragraph(_safe(inst_str), st["edu_sub"]))

    doc.build(elems)
    return output_path


# ── Cover Letter PDF ──────────────────────────────────────────────────────────

def generate_cover_letter_pdf(
    cl_data: dict,
    user_info: dict,
    output_path: str,
) -> str:
    """Generate a professional cover letter PDF. Returns path to PDF file."""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=1.0*inch, rightMargin=1.0*inch,
        topMargin=0.9*inch,  bottomMargin=0.9*inch,
    )

    st    = _styles()
    elems = []

    # ── Header ─────────────────────────────────────────────────────────────
    name = _safe(user_info.get("full_name", ""))
    elems.append(Paragraph(name, st["cl_name"]))

    contact_parts = []
    if user_info.get("email"):   contact_parts.append(_safe(user_info["email"]))
    if user_info.get("phone"):   contact_parts.append(_safe(user_info["phone"]))
    if user_info.get("location"):contact_parts.append(_safe(user_info["location"]))
    if user_info.get("linkedin"):
        contact_parts.append(f'<link href="{_safe(user_info["linkedin"])}">LinkedIn</link>')
    elems.append(Paragraph(" · ".join(contact_parts), st["cl_contact"]))
    elems.append(_rule())
    elems.append(Spacer(1, 14))

    # ── Body ───────────────────────────────────────────────────────────────
    full_text = cl_data.get("full_text", "")
    # Split on literal \n\n or real newlines
    full_text = full_text.replace("\\n\\n", "\n\n").replace("\\n", "\n")
    paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]

    for para in paragraphs:
        elems.append(Paragraph(_safe(para), st["cl_body"]))

    doc.build(elems)
    return output_path

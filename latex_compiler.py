"""
latex_compiler.py
=================
Builds LaTeX source directly in Python (no Jinja2 templates) → .tex / .pdf

Strategy:
  1. Pure Python string building — zero conflict with LaTeX backslashes / %
  2. Try local pdflatex / xelatex (if MiKTeX or TeX Live installed)
  3. Fallback: write .tex file → user compiles on Overleaf
"""

import os
import re
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Any

from config import OUTPUT_DIR, LATEX_COMPILER_PATH


# ─── LaTeX helpers ────────────────────────────────────────────────────────────

def _e(value: Any) -> str:
    """Escape special LaTeX characters in a plain string value."""
    if not isinstance(value, str):
        value = str(value) if value else ""
    if not value:
        return ""
    chars = [
        ("\\", r"\textbackslash{}"),
        ("&",  r"\&"),
        ("%",  r"\%"),
        ("$",  r"\$"),
        ("#",  r"\#"),
        ("_",  r"\_"),
        ("{",  r"\{"),
        ("}",  r"\}"),
        ("~",  r"\textasciitilde{}"),
        ("^",  r"\textasciicircum{}"),
        ("<",  r"\textless{}"),
        (">",  r"\textgreater{}"),
    ]
    for ch, rep in chars:
        value = value.replace(ch, rep)
    return value


def _safe_url(url: str) -> str:
    """URLs only need % escaped for LaTeX href."""
    return url.replace("%", r"\%") if url else ""


# ─── Resume LaTeX builder ─────────────────────────────────────────────────────

def build_resume_latex(d: dict) -> str:
    """Build a complete ATS-optimised LaTeX resume from a resume data dict."""
    import json as _json
    # Guard: if caller passed a JSON string instead of a dict, parse it
    if isinstance(d, str):
        try:
            d = _json.loads(d)
        except Exception:
            d = {}
    if not isinstance(d, dict):
        d = {}

    # ── Inline normalise: guarantee every list-of-dict field contains only dicts ──
    def _norm_list(lst, str_key: str) -> list:
        out = []
        for x in (lst if isinstance(lst, list) else []):
            if isinstance(x, dict):
                out.append(x)
            elif isinstance(x, str) and x.strip():
                out.append({str_key: x.strip()})
            # silently drop None / int / etc.
        return out

    d["experience"]     = _norm_list(d.get("experience",     []), "title")
    d["education"]      = _norm_list(d.get("education",      []), "degree")
    d["projects"]       = _norm_list(d.get("projects",       []), "name")
    d["certifications"] = _norm_list(d.get("certifications", []), "name")

    def _to_dict(item, name_key="name") -> dict:
        """Ensure a list item is always a dict. Plain strings become {name_key: item}."""
        if isinstance(item, dict):
            return item
        if isinstance(item, str):
            return {name_key: item.strip()}
        return {}

    def skills_line(label: str, items: list) -> str:
        if not items:
            return ""
        joined = ", ".join(_e(s) for s in items if s and isinstance(s, str))
        return f"\\textbf{{{label}:}} {joined}\\\\\n"

    # ── Header links ──────────────────────────────────────────
    links = []
    if d.get("email"):
        links.append(f"\\href{{mailto:{_safe_url(d['email'])}}}{{{_e(d['email'])}}}")
    if d.get("phone"):
        links.append(_e(d["phone"]))
    if d.get("linkedin"):
        links.append(f"\\href{{{_safe_url(d['linkedin'])}}}{{{_e('LinkedIn')}}}")
    if d.get("github"):
        links.append(f"\\href{{{_safe_url(d['github'])}}}{{{_e('GitHub')}}}")
    header_links = " $\\cdot$ ".join(links)

    # ── Skills ────────────────────────────────────────────────
    raw_skills = d.get("skills", {})
    skills = raw_skills if isinstance(raw_skills, dict) else {}
    skills_block = ""

    # Prefer skill_categories (new format) → fall back to flat skills dict
    skill_cats = d.get("skill_categories", [])
    if skill_cats:
        for cat in skill_cats:
            if not isinstance(cat, dict):
                continue
            cat_name  = cat.get("category", "")
            cat_items = cat.get("skills", [])
            if cat_name and cat_items:
                skills_block += skills_line(_e(cat_name), cat_items)
    else:
        skills_block += skills_line("Technical Skills",       skills.get("technical_skills", []))
        skills_block += skills_line("Tools \\& Technologies", skills.get("tools_technologies", []))
        skills_block += skills_line("Soft Skills",            skills.get("soft_skills", []))

    # ── Experience ────────────────────────────────────────────
    exp_block = ""
    for raw_job in d.get("experience", []):
        job    = _to_dict(raw_job, "title")
        title   = _e(job.get("title", ""))
        company = _e(job.get("company", ""))
        location= _e(job.get("location", ""))
        start   = _e(job.get("start_date", ""))
        end     = _e(job.get("end_date", ""))
        context = _e(job.get("context", ""))
        exp_block += (
            f"\\noindent\\textbf{{{title}}} \\hfill \\textit{{{start} -- {end}}}\\\\\n"
            f"\\textit{{{company}"
            + (f" --- {location}" if location else "")
            + f"}}\n"
        )
        if context:
            exp_block += f"{{\\small\\textit{{{context}}}}}\n"
        exp_block += "\\vspace{2pt}\n\\begin{itemize}\n"
        for bullet in job.get("bullets", []):
            exp_block += f"  \\item {_e(str(bullet))}\n"
        exp_block += "\\end{itemize}\n\\vspace{4pt}\n\n"

    # ── Education ─────────────────────────────────────────────
    edu_block = ""
    for raw_edu in d.get("education", []):
        edu    = _to_dict(raw_edu, "degree")
        degree = _e(edu.get("degree", ""))
        field  = _e(edu.get("field", ""))
        inst   = _e(edu.get("institution", ""))
        year   = _e(edu.get("graduation_year", ""))
        gpa    = _e(edu.get("gpa", "") or "")
        gpa_str = f" $\\cdot$ GPA: {gpa}" if gpa and gpa not in ("optional", "") else ""
        deg_str = f"{degree} in {field}" if field else degree
        edu_block += (
            f"\\noindent\\textbf{{{deg_str}}} \\hfill \\textbf{{{year}}}\\\\\n"
            f"\\textit{{{inst}}}{gpa_str}\n"
            f"\\vspace{{4pt}}\n\n"
        )
        coursework = [c for c in edu.get("relevant_coursework", []) if c]
        if coursework:
            edu_block += f"\\textbf{{Relevant Coursework:}} {', '.join(_e(str(c)) for c in coursework)}\\\\\n\n"

    # ── Certifications ────────────────────────────────────────
    cert_block = ""
    raw_certs = d.get("certifications", [])
    certs = []
    for c in raw_certs:
        cd = _to_dict(c, "name")
        if cd.get("name"):
            certs.append(cd)
    if certs:
        cert_block = "\\section{Certifications}\n"
        for cert in certs:
            name   = _e(cert.get("name", ""))
            issuer = _e(cert.get("issuer", ""))
            year   = _e(cert.get("year", "") or cert.get("status", ""))
            line   = f"\\noindent\\textbf{{{name}}}"
            if issuer: line += f" $\\cdot$ {issuer}"
            if year:   line += f" \\hfill {year}"
            cert_block += line + "\\\\\n"
        cert_block += "\\vspace{4pt}\n\n"

    # ── Projects ──────────────────────────────────────────────
    proj_block = ""
    raw_projects = [p for p in d.get("projects", []) if p]
    projects = [_to_dict(p, "name") for p in raw_projects]
    projects = [p for p in projects if p.get("name")]
    if projects:
        proj_block = "\\section{Selected Projects}\n"
        for proj in projects:
            name   = _e(proj.get("name", ""))
            year   = _e(proj.get("year", "") or proj.get("impact", ""))
            desc   = _e(proj.get("description", ""))
            tech   = ", ".join(_e(str(t)) for t in proj.get("technologies", []) if t)
            bullets = proj.get("bullets", [])
            proj_block += f"\\noindent\\textbf{{{name}}}"
            if year: proj_block += f" \\hfill \\textit{{{year}}}"
            proj_block += "\\\\\n"
            if desc and not bullets:
                proj_block += f"{desc}\\\\\n"
            for b in bullets:
                proj_block += f"\\textit{{\\small {_e(str(b))}}}\\\\\n"
            if tech:
                proj_block += f"\\textit{{Stack: {tech}}}\\\\\n"
            proj_block += "\\vspace{4pt}\n\n"

    # ── Achievements ──────────────────────────────────────────
    ach_block = ""
    achievements = d.get("achievements", d.get("awards", []))
    if achievements:
        ach_block = "\\section{Achievements \\& Awards}\n\\begin{itemize}\n"
        for a in achievements:
            if isinstance(a, dict):
                title_part = a.get("title", "")
                text_part  = a.get("text", "")
                if title_part and text_part:
                    ach_block += f"  \\item \\textbf{{{_e(title_part)}:}} {_e(text_part)}\n"
                else:
                    ach_block += f"  \\item {_e(title_part or text_part)}\n"
            else:
                ach_block += f"  \\item {_e(str(a))}\n"
        ach_block += "\\end{itemize}\n\\vspace{4pt}\n\n"

    # ── Assemble full document ────────────────────────────────
    headline = _e(d.get("headline", ""))
    tex = r"""\documentclass[10pt,a4paper]{article}
\usepackage[top=0.62in,bottom=0.62in,left=0.72in,right=0.72in]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage{microtype}
\usepackage{hyperref}
\hypersetup{hidelinks}
\usepackage{enumitem}
\setlist[itemize]{leftmargin=1.35em,topsep=1.5pt,itemsep=0.5pt,parsep=0pt,label=\textbullet}
\usepackage{titlesec}
\titleformat{\section}{\normalsize\bfseries\MakeUppercase}{}{0em}{}[\vspace{-5pt}\rule{\linewidth}{0.6pt}\vspace{1pt}]
\titlespacing*{\section}{0pt}{9pt}{3pt}
\usepackage{array}
\usepackage{tabularx}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\pagestyle{empty}
\begin{document}

\begin{center}
  {\LARGE\bfseries """ + _e(d.get("full_name", "")) + r""" }\\[3pt]
  """ + (f"{{\\small {headline}}}\\\\[4pt]\n  " if headline else "") + r"""{\small """ + _e(d.get("location", "")) + (r" \quad $\mid$ \quad " if d.get("location") and (d.get("phone") or d.get("email")) else "") + (f'\\href{{mailto:{_safe_url(d.get("email",""))}}}{{{_e(d.get("email",""))}}}' if d.get("email") else "") + (r" $\mid$ " + _e(d.get("phone","")) if d.get("phone") else "") + r"""\\[2pt]
  """ + (f'\\href{{{_safe_url(d.get("github",""))}}}{{{_e(d.get("github",""))}}}' if d.get("github") else "") + (r" $\mid$ " if d.get("github") and d.get("linkedin") else "") + (f'\\href{{{_safe_url(d.get("linkedin",""))}}}{{{_e(d.get("linkedin",""))}}}' if d.get("linkedin") else "") + r"""}
\end{center}

\vspace{2pt}

\section{Professional Summary}
""" + _e(d.get("summary", "")) + r"""

\section{Technical Skills}
""" + skills_block + r"""

\section{Professional Experience}
""" + exp_block + r"""
\section{Selected Projects}
""" + proj_block + ach_block + cert_block + r"""
\section{Education}
""" + edu_block + r"""
\end{document}
"""
    return tex


# ─── Cover Letter LaTeX builder ───────────────────────────────────────────────

def build_cover_letter_latex(cl: dict, user: dict, company_name: str) -> str:
    """Build a LaTeX cover letter from cover letter data + user info."""

    full_name = _e(user.get("full_name", ""))
    email_raw = user.get("email", "")
    phone     = _e(user.get("phone", ""))
    location  = _e(user.get("location", ""))
    linkedin  = user.get("linkedin", "")

    contact_line = _e(email_raw)
    if phone:
        contact_line += f" $\\cdot$ {phone}"
    if linkedin:
        contact_line += f" $\\cdot$ \\href{{{_safe_url(linkedin)}}}{{{_e('LinkedIn')}}}"

    body = _e(cl.get("full_text", ""))
    # Replace literal \n\n with LaTeX paragraph breaks
    body = body.replace("\\n\\n", "\n\n").replace("\\n", "\\\\\n")

    tex = r"""\documentclass[11pt,letterpaper]{article}
\usepackage[top=1in,bottom=1in,left=1in,right=1in]{geometry}
\usepackage{helvet}
\renewcommand{\familydefault}{\sfdefault}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{hyperref}
\usepackage{parskip}
\usepackage{xcolor}
\definecolor{navy}{RGB}{0,51,102}
\hypersetup{colorlinks=true,urlcolor=navy}
\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{8pt}
\begin{document}

{\Large\bfseries\color{navy} """ + full_name + r"""}\\
""" + contact_line + r"""

\vspace{12pt}

""" + body + r"""

\end{document}
"""
    return tex


# ─── Compiler class ───────────────────────────────────────────────────────────

class LatexCompiler:
    """Builds LaTeX source and optionally compiles to PDF."""

    def __init__(self):
        self.compiler = self._find_compiler()

    def _find_compiler(self) -> str | None:
        if LATEX_COMPILER_PATH and Path(LATEX_COMPILER_PATH).exists():
            return LATEX_COMPILER_PATH
        for binary in ["pdflatex", "xelatex", "lualatex"]:
            path = shutil.which(binary)
            if path:
                return path
        return None

    def render_resume(self, resume_data) -> str:
        import json as _json
        if isinstance(resume_data, str):
            try:
                resume_data = _json.loads(resume_data)
            except Exception:
                resume_data = {}
        return build_resume_latex(resume_data)

    def render_cover_letter(
        self,
        cover_letter_data: dict[str, Any],
        user_info: dict[str, Any],
        company_name: str,
    ) -> str:
        return build_cover_letter_latex(cover_letter_data, user_info, company_name)

    def compile_to_pdf(self, tex_content: str, output_filename: str,
                       resume_data: dict | None = None,
                       cover_letter_data: dict | None = None,
                       user_info: dict | None = None) -> dict[str, Any]:
        """
        Generate PDF using reportlab (always works, no LaTeX needed).
        Also saves the .tex file for those who want LaTeX source.
        """
        from pdf_generator import generate_resume_pdf, generate_cover_letter_pdf

        # Always save .tex file
        tex_path = os.path.join(OUTPUT_DIR, f"{output_filename}.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_content)

        pdf_path = os.path.join(OUTPUT_DIR, f"{output_filename}.pdf")
        result = {
            "success":      False,
            "pdf_path":     None,
            "tex_path":     tex_path,
            "log":          "",
            "has_compiler": True,
        }

        try:
            if resume_data is not None:
                generate_resume_pdf(resume_data, pdf_path)
            elif cover_letter_data is not None and user_info is not None:
                generate_cover_letter_pdf(cover_letter_data, user_info, pdf_path)
            else:
                result["log"] = "No data provided for PDF generation."
                return result

            result["success"]  = True
            result["pdf_path"] = pdf_path
            result["log"]      = "PDF generated successfully."
        except Exception as e:
            result["log"] = f"PDF generation error: {e}"

        return result

    def _escape_dict(self, data: Any) -> Any:
        if isinstance(data, str):
            return _e(data)
        elif isinstance(data, dict):
            return {k: self._escape_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._escape_dict(item) for item in data]
        return data


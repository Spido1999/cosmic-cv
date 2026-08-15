"""
utils/ats_scorer.py
===================
Scores a resume text against a parsed JD.
Returns a score 0-100 with detailed breakdown explaining what's missing.
"""

import re
from typing import Any


def _normalize(text: str) -> str:
    return text.lower().strip()


def _keyword_found(keyword: str, resume_text: str) -> bool:
    """Check if a keyword (or its significant words) appear in the resume."""
    resume_lower = resume_text.lower()
    keyword_lower = keyword.lower().strip()

    # Exact phrase match first
    if keyword_lower in resume_lower:
        return True

    # For multi-word keywords, check if most words appear
    words = [w for w in re.split(r'\W+', keyword_lower) if len(w) > 2]
    if not words:
        return False
    matched = sum(1 for w in words if w in resume_lower)
    return matched / len(words) >= 0.75  # 75% word match threshold


class ATSScorer:
    """
    Scores a resume against a JD parsed dict.

    Score breakdown (100 pts total):
      - Must-have keywords:        35 pts
      - Hard skills coverage:      25 pts
      - Tools & technologies:      15 pts
      - Soft skills:                5 pts
      - Job title match:            5 pts
      - Education match:            5 pts
      - Seniority/experience:       5 pts
      - ATS formatting rules:       5 pts
    """

    WEIGHTS = {
        "must_have_keywords":       35,
        "hard_skills":              25,
        "tools_and_technologies":   15,
        "soft_skills":               5,
        "job_title":                 5,
        "education":                 5,
        "experience":                5,
        "formatting":                5,
    }

    def score(self, resume_text: str, parsed_jd: dict[str, Any]) -> dict[str, Any]:
        breakdown: dict[str, Any] = {}
        total = 0.0
        missing_keywords: list[str] = []
        found_keywords: list[str] = []

        # ── 1. Must-have keywords (35 pts) ────────────────────────────────
        must_have = parsed_jd.get("must_have_keywords", [])
        if must_have:
            hits = [kw for kw in must_have if _keyword_found(kw, resume_text)]
            misses = [kw for kw in must_have if not _keyword_found(kw, resume_text)]
            ratio = len(hits) / len(must_have)
            pts = round(ratio * self.WEIGHTS["must_have_keywords"], 1)
            breakdown["must_have_keywords"] = {
                "score": pts, "max": self.WEIGHTS["must_have_keywords"],
                "found": len(hits), "total": len(must_have), "missing": misses[:10]
            }
            total += pts
            missing_keywords.extend(misses)
            found_keywords.extend(hits)
        else:
            breakdown["must_have_keywords"] = {"score": self.WEIGHTS["must_have_keywords"],
                                                "max": self.WEIGHTS["must_have_keywords"]}
            total += self.WEIGHTS["must_have_keywords"]

        # ── 2. Hard skills (25 pts) ────────────────────────────────────────
        hard_skills = parsed_jd.get("hard_skills", [])
        if hard_skills:
            hits = [s for s in hard_skills if _keyword_found(s, resume_text)]
            misses = [s for s in hard_skills if not _keyword_found(s, resume_text)]
            ratio = len(hits) / len(hard_skills)
            pts = round(ratio * self.WEIGHTS["hard_skills"], 1)
            breakdown["hard_skills"] = {
                "score": pts, "max": self.WEIGHTS["hard_skills"],
                "found": len(hits), "total": len(hard_skills), "missing": misses[:8]
            }
            total += pts
            missing_keywords.extend(misses)
        else:
            breakdown["hard_skills"] = {"score": self.WEIGHTS["hard_skills"],
                                         "max": self.WEIGHTS["hard_skills"]}
            total += self.WEIGHTS["hard_skills"]

        # ── 3. Tools & technologies (15 pts) ──────────────────────────────
        tools = parsed_jd.get("tools_and_technologies", [])
        if tools:
            hits = [t for t in tools if _keyword_found(t, resume_text)]
            misses = [t for t in tools if not _keyword_found(t, resume_text)]
            ratio = len(hits) / len(tools)
            pts = round(ratio * self.WEIGHTS["tools_and_technologies"], 1)
            breakdown["tools_and_technologies"] = {
                "score": pts, "max": self.WEIGHTS["tools_and_technologies"],
                "found": len(hits), "total": len(tools), "missing": misses[:5]
            }
            total += pts
        else:
            breakdown["tools_and_technologies"] = {"score": self.WEIGHTS["tools_and_technologies"],
                                                     "max": self.WEIGHTS["tools_and_technologies"]}
            total += self.WEIGHTS["tools_and_technologies"]

        # ── 4. Soft skills (5 pts) ─────────────────────────────────────────
        soft_skills = parsed_jd.get("soft_skills", [])
        if soft_skills:
            hits = [s for s in soft_skills if _keyword_found(s, resume_text)]
            ratio = len(hits) / len(soft_skills)
            pts = round(ratio * self.WEIGHTS["soft_skills"], 1)
            breakdown["soft_skills"] = {"score": pts, "max": self.WEIGHTS["soft_skills"]}
            total += pts
        else:
            breakdown["soft_skills"] = {"score": self.WEIGHTS["soft_skills"],
                                         "max": self.WEIGHTS["soft_skills"]}
            total += self.WEIGHTS["soft_skills"]

        # ── 5. Job title match (5 pts) ─────────────────────────────────────
        job_title = parsed_jd.get("job_title", "")
        if job_title and _keyword_found(job_title, resume_text):
            pts = self.WEIGHTS["job_title"]
        elif job_title:
            # Partial: check individual words of job title
            title_words = [w for w in job_title.lower().split() if len(w) > 3]
            matched = sum(1 for w in title_words if w in resume_text.lower())
            pts = round((matched / max(len(title_words), 1)) * self.WEIGHTS["job_title"], 1)
        else:
            pts = self.WEIGHTS["job_title"]
        breakdown["job_title"] = {"score": pts, "max": self.WEIGHTS["job_title"]}
        total += pts

        # ── 6. Education (5 pts) ───────────────────────────────────────────
        edu_level = parsed_jd.get("education_level", "None specified").lower()
        edu_keywords = {
            "high school": ["high school", "secondary"],
            "associate": ["associate", "diploma"],
            "bachelor": ["bachelor", "b.s.", "b.a.", "b.eng", "undergraduate", "degree"],
            "master": ["master", "m.s.", "m.a.", "m.eng", "mba", "postgraduate"],
            "phd": ["phd", "doctorate", "ph.d"],
        }
        edu_pts = self.WEIGHTS["education"]
        if edu_level != "none specified":
            for level, variants in edu_keywords.items():
                if level in edu_level:
                    found = any(v in resume_text.lower() for v in variants)
                    edu_pts = self.WEIGHTS["education"] if found else 2
                    break
        breakdown["education"] = {"score": edu_pts, "max": self.WEIGHTS["education"]}
        total += edu_pts

        # ── 7. Experience (5 pts) ──────────────────────────────────────────
        exp_min = parsed_jd.get("experience_years_min", 0)
        has_exp_section = any(w in resume_text.lower()
                              for w in ["experience", "work history", "employment"])
        exp_pts = self.WEIGHTS["experience"] if has_exp_section else 0
        breakdown["experience"] = {"score": exp_pts, "max": self.WEIGHTS["experience"],
                                    "min_years_required": exp_min}
        total += exp_pts

        # ── 8. ATS Formatting rules (5 pts) ───────────────────────────────
        fmt_pts = self.WEIGHTS["formatting"]
        fmt_issues: list[str] = []

        # Check standard sections exist
        standard_sections = ["experience", "education", "skills", "summary"]
        missing_sections = [s for s in standard_sections if s not in resume_text.lower()]
        if missing_sections:
            deduct = len(missing_sections) * 1
            fmt_pts -= deduct
            fmt_issues.append(f"Missing sections: {missing_sections}")

        # Check no special chars that confuse ATS
        if re.search(r'[│┤╡╢╖╕╣║╗╝╜╛┐└┴┬├─┼╞╟╚╔╩╦╠═╬╧╨╤╥╙╘╒╓╫╪┘┌]', resume_text):
            fmt_pts -= 2
            fmt_issues.append("Contains box-drawing characters (ATS unfriendly)")

        fmt_pts = max(0, fmt_pts)
        breakdown["formatting"] = {"score": fmt_pts, "max": self.WEIGHTS["formatting"],
                                    "issues": fmt_issues}
        total += fmt_pts

        # ── Final result ───────────────────────────────────────────────────
        final_score = min(round(total, 1), 100.0)

        # Unique missing keywords (deduped)
        seen: set[str] = set()
        unique_missing: list[str] = []
        for kw in missing_keywords:
            if kw.lower() not in seen:
                seen.add(kw.lower())
                unique_missing.append(kw)

        return {
            "total_score": final_score,
            "grade": self._grade(final_score),
            "breakdown": breakdown,
            "missing_keywords": unique_missing,
            "found_keywords": list(set(found_keywords)),
            "recommendation": self._recommendation(final_score, unique_missing),
        }

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 95:
            return "🏆 Excellent — Will pass virtually all ATS systems"
        elif score >= 85:
            return "✅ Strong — Likely to pass most ATS systems"
        elif score >= 70:
            return "⚠️ Good — May be filtered by strict ATS; add missing keywords"
        elif score >= 50:
            return "❌ Weak — High risk of ATS rejection; significant revision needed"
        else:
            return "🚫 Poor — Will be rejected by ATS; major rewrite required"

    @staticmethod
    def _recommendation(score: float, missing: list[str]) -> str:
        if score >= 95:
            return "Your resume is highly optimised. Focus on interview preparation."
        top_missing = ", ".join(f'"{k}"' for k in missing[:5])
        if missing:
            return f"Add these keywords naturally into your resume: {top_missing}"
        return "Review formatting and section structure to improve further."

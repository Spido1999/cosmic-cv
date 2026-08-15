"""
utils/jd_parser.py
==================
Parses a raw Job Description and extracts:
  - Required hard skills / tech stack
  - Soft skills
  - Mandatory keywords (must appear in resume for ATS)
  - Job title, seniority level, industry
  - Experience requirements
  - Education requirements
  - Action verbs used in JD (mirror them in resume)
"""

import re
import json
import httpx
import openai
from typing import Any
from config import OPENAI_API_KEY, OPENAI_MODEL, DEEPSEEK_BASE_URL


JD_SYSTEM_PROMPT = """You are an expert ATS (Applicant Tracking System) analyst and HR specialist.
Your job is to deeply analyse a Job Description and extract every detail that an ATS system
would scan for when evaluating a resume.

Return ONLY a valid JSON object with this exact schema (no markdown, no explanation):
{
  "job_title": "string",
  "company_name": "string or empty",
  "seniority_level": "Intern|Junior|Mid|Senior|Lead|Manager|Director|VP|C-Level",
  "industry": "string",
  "employment_type": "Full-time|Part-time|Contract|Freelance|Internship",
  "location": "string or Remote",
  "experience_years_min": 0,
  "experience_years_max": 10,
  "hard_skills": ["list of specific technical skills, tools, frameworks, languages"],
  "soft_skills": ["list of soft skills explicitly or implicitly required"],
  "certifications": ["list of certifications mentioned or implied"],
  "education_level": "High School|Associate|Bachelor|Master|PhD|None specified",
  "education_field": ["relevant fields of study"],
  "must_have_keywords": ["top 30 exact keywords/phrases ATS will scan for"],
  "nice_to_have_keywords": ["secondary keywords that boost ranking"],
  "action_verbs": ["action verbs used in the JD responsibilities section"],
  "responsibilities": ["key responsibilities paraphrased concisely"],
  "quantifiable_expectations": ["any metrics, numbers, % goals mentioned"],
  "tools_and_technologies": ["specific software, platforms, databases, cloud services"],
  "domain_knowledge": ["industry-specific knowledge areas required"],
  "resume_section_priorities": ["ordered list: which sections matter most for this role"]
}"""


def _make_client() -> openai.OpenAI:
    """Create OpenAI-compatible client pointing at DeepSeek, SSL-bypass for corporate proxies."""
    return openai.OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        http_client=httpx.Client(verify=False),
    )


# ─── Parser Class ────────────────────────────────────────────────────────────
class JDParser:
    """Extracts structured ATS intelligence from a raw Job Description."""

    def __init__(self):
        self.client = _make_client()
        self.model  = OPENAI_MODEL

    def parse(self, jd_text: str) -> dict[str, Any]:
        """Parse JD and return structured dict."""
        if not jd_text.strip():
            raise ValueError("Job Description cannot be empty.")

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.0,
            extra_body={"reasoning_effort": "low"},
            messages=[
                {"role": "system", "content": JD_SYSTEM_PROMPT},
                {"role": "user",   "content": f"Job Description:\n\n{jd_text}"},
            ],
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}\nRaw: {raw[:500]}")

        return parsed

    def get_ats_keywords(self, parsed_jd: dict) -> list[str]:
        """Return a flat deduplicated list of all ATS-critical keywords."""
        all_keywords: list[str] = []
        for field in ["must_have_keywords", "hard_skills", "tools_and_technologies",
                      "soft_skills", "nice_to_have_keywords"]:
            all_keywords.extend(parsed_jd.get(field, []))
        seen: set[str] = set()
        unique: list[str] = []
        for kw in all_keywords:
            lower = kw.lower().strip()
            if lower not in seen:
                seen.add(lower)
                unique.append(kw.strip())
        return unique

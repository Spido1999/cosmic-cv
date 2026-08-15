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

import os
import re
import json
import httpx
import openai
from typing import Any
from config import DEEPSEEK_BASE_URL, OPENAI_BASE_URL, NVIDIA_BASE_URL


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


def _live_secret(key: str, fallback: str = "") -> str:
    """Read from Streamlit secrets first, then env vars."""
    try:
        import streamlit as st
        val = st.secrets.get(key, None)
        if val:
            return val
    except Exception:
        pass
    return os.getenv(key, fallback)


def _make_client() -> tuple[openai.OpenAI, str]:
    """Return (client, model) using whichever provider key is available."""
    deepseek_key = _live_secret("DEEPSEEK_API_KEY")
    openai_key   = _live_secret("OPENAI_API_KEY")
    nvidia_key   = _live_secret("NVIDIA_API_KEY")
    if deepseek_key:
        model  = _live_secret("DEEPSEEK_MODEL", "deepseek-chat")
        client = openai.OpenAI(
            api_key=deepseek_key,
            base_url=DEEPSEEK_BASE_URL,
            http_client=httpx.Client(verify=False),
        )
    elif nvidia_key:
        model  = "nvidia/nemotron-3-ultra-550b-a55b"
        client = openai.OpenAI(api_key=nvidia_key, base_url=NVIDIA_BASE_URL)
    elif openai_key:
        model  = _live_secret("OPENAI_MODEL", "gpt-4o-mini")
        client = openai.OpenAI(api_key=openai_key, base_url=OPENAI_BASE_URL)
    else:
        raise RuntimeError("No API key found. Add DEEPSEEK_API_KEY, OPENAI_API_KEY, or NVIDIA_API_KEY in Streamlit secrets.")
    return client, model


# ─── Parser Class ────────────────────────────────────────────────────────────
class JDParser:
    """Extracts structured ATS intelligence from a raw Job Description."""

    def __init__(self):
        self.client, self.model = _make_client()

    def parse(self, jd_text: str) -> dict[str, Any]:
        """Parse JD and return structured dict."""
        if not jd_text.strip():
            raise ValueError("Job Description cannot be empty.")

        extra = {"extra_body": {"reasoning_effort": "low"}} if DEEPSEEK_BASE_URL in str(self.client.base_url) else {}
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.0,
            **extra,
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

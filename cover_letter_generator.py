"""
cover_letter_generator.py - ATS Cover Letter Generator using DeepSeek API.
"""

import json
import re
import httpx
import openai
from typing import Any

from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL,
    OPENAI_API_KEY, OPENAI_BASE_URL,
    OPENAI_MODEL,
)


def _make_client(provider: str = "DeepSeek", model: str | None = None) -> tuple["openai.OpenAI", str]:
    """Return (client, resolved_model) for the chosen provider."""
    if provider == "OpenAI":
        client   = openai.OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        resolved = model or "gpt-4o"
    else:
        client   = openai.OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            http_client=httpx.Client(verify=False),
        )
        resolved = model or OPENAI_MODEL
    return client, resolved


COVER_LETTER_SYSTEM = """You are a world-class cover letter strategist who has written 10,000+ cover letters securing interviews at top companies. You know exactly what hiring managers want to read in the first 3 sentences.

Your philosophy: A great cover letter doesn't summarise the resume. It tells a story — WHY this person, WHY this company, WHY right now. It makes the hiring manager feel: "This person gets exactly what we need."

STRUCTURE RULES:
1. OPENING: Name the exact role, express specific excitement about THIS company (not generic). Hook in the first line.
2. ACHIEVEMENT PARAGRAPH 1: Single best achievement using CAR (Challenge → Action → Result). Match the JD's top requirement.
3. ACHIEVEMENT PARAGRAPH 2: Second strength using a different JD requirement. Show depth.
4. COMPANY MOTIVATION: A dedicated paragraph on WHY this company specifically — their mission, product, domain, tech, culture, or recent news. Make it personal and genuine. "What drew me to [Company] specifically is..."
5. CLOSING: Confident call to action. Enthusiastic, not desperate. Under 2 sentences.

WRITING RULES:
- Use EXACT job title in paragraph 1.
- Mirror the JD's language and terminology throughout (same words, same casing).
- Every achievement must have a metric ($, %, x faster, users, time saved).
- NO clichés: no "I am a passionate professional", "team player", "hardworking", "I believe I would be a great fit".
- Tone: confident, specific, enthusiastic — like someone who has done this exact work and is excited to do more of it.
- Total length: under 420 words. Every sentence earns its place.

Return ONLY a JSON object (no markdown fences, no commentary):
{
  "subject_line": "Application for [Exact Job Title] — [Full Name]",
  "salutation": "Dear Hiring Team,",
  "opening_paragraph": "1-2 sentences: exact role + company hook + immediate value statement with a result",
  "body_paragraph_1": "CAR achievement targeting JD's #1 requirement — specific metric, JD keyword embedded",
  "body_paragraph_2": "Second CAR achievement targeting JD's #2 requirement — different skill area",
  "company_motivation_paragraph": "Why THIS company specifically — reference their product/mission/domain/tech — personal and genuine, not generic",
  "closing_paragraph": "Confident CTA + enthusiasm + availability for interview",
  "sign_off": "Sincerely,",
  "full_text": "Complete cover letter as single string with paragraph breaks as double newlines"
}"""


class CoverLetterGenerator:
    def __init__(self, provider: str = "DeepSeek", model: str | None = None):
        self.provider = provider
        self.client, self.model = _make_client(provider, model)

    def _extra(self, effort: str = "medium") -> dict:
        return {"extra_body": {"reasoning_effort": effort}} if self.provider == "DeepSeek" else {}

    def generate(self, user_profile: str, parsed_jd: dict[str, Any],
                 resume_data: dict[str, Any] | None = None,
                 additional_context: str = "") -> dict[str, Any]:
        highlights = self._extract_highlights(resume_data) if resume_data else ""
        company    = parsed_jd.get('company_name', 'the company')
        job_title  = parsed_jd.get('job_title', '')
        seniority  = parsed_jd.get('seniority_level', '')
        industry   = parsed_jd.get('industry', '')
        must_haves = ', '.join(parsed_jd.get('must_have_keywords', [])[:12])
        top_resp   = parsed_jd.get('responsibilities', [])[:4]
        tools      = ', '.join(parsed_jd.get('tools_and_technologies', [])[:6])
        culture    = parsed_jd.get('company_culture', parsed_jd.get('company_values', ''))

        user_msg = f"""CANDIDATE PROFILE:
{user_profile}

TARGET ROLE:
- Company     : {company}
- Job Title   : {job_title}
- Seniority   : {seniority}
- Industry    : {industry}
- Must-Have Keywords: {must_haves}
- Tools/Tech  : {tools}
- Top Responsibilities:
{chr(10).join(f'  {i+1}. {r}' for i, r in enumerate(top_resp))}
- Company Culture/Values: {culture if culture else 'Not specified — infer from industry and JD'}

BEST RESUME HIGHLIGHTS (use these as the basis for CAR achievements):
{highlights}

INSTRUCTIONS:
Write the IDEAL cover letter for this {seniority} {job_title} role at {company}.

- Opening: name the exact role, hook the reader with a specific result or insight, show you know {company}.
- Body 1: Best CAR achievement targeting the #1 responsibility listed above. Include a metric.
- Body 2: Second achievement targeting a different top requirement. Show skill depth.
- Company Motivation: WHY {company} specifically. Reference their {industry} domain, their use of {tools}, their mission or market position. Make it feel personal and researched — not "great company culture".
- Closing: confident, specific CTA. 1-2 sentences max.

Return the JSON object only:"""

        r = self.client.chat.completions.create(
            model=self.model, temperature=0.5,
            **self._extra("medium"),
            messages=[{"role": "system", "content": COVER_LETTER_SYSTEM},
                      {"role": "user",   "content": user_msg}])
        raw = re.sub(r"^```(?:json)?\s*", "", r.choices[0].message.content.strip())
        raw = re.sub(r"\s*```$", "", raw)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                return json.loads(m.group())
            return {"full_text": raw, "subject_line": f"Application for {parsed_jd.get('job_title','Position')}"}

    @staticmethod
    def _extract_highlights(resume_data: dict) -> str:
        highlights: list[str] = []
        for exp in resume_data.get("experience", [])[:2]:
            highlights.extend(exp.get("bullets", [])[:2])
        for proj in resume_data.get("projects", [])[:1]:
            highlights.append(proj.get("description", ""))
        return "\n".join(f"- {h}" for h in highlights if h)

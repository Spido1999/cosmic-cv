"""
resume_generator.py - ATS Resume Generator using DeepSeek API directly.
"""

import json
import re
import httpx
import openai
from typing import Any

from config import (
    DEEPSEEK_BASE_URL,
    OPENAI_BASE_URL,
    NVIDIA_BASE_URL,
    OPENAI_MODEL, ATS_TARGET_SCORE,
)
from utils.ats_scorer import ATSScorer


def _live_secret(key: str, fallback: str = "") -> str:
    """Read from Streamlit secrets first, then env vars."""
    try:
        import streamlit as st
        val = st.secrets.get(key, None)
        if val:
            return val
    except Exception:
        pass
    import os
    return os.getenv(key, fallback)


def _make_client(provider: str = "DeepSeek", model: str | None = None) -> tuple["openai.OpenAI", str]:
    """Return (client, resolved_model) for the chosen provider."""
    if provider == "OpenAI":
        api_key  = _live_secret("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not found in secrets.")
        client   = openai.OpenAI(api_key=api_key, base_url=OPENAI_BASE_URL)
        resolved = model or _live_secret("OPENAI_MODEL", "gpt-4o")
    elif provider == "NVIDIA":
        api_key  = _live_secret("NVIDIA_API_KEY")
        if not api_key:
            raise RuntimeError("NVIDIA_API_KEY not found in secrets. Add it in Streamlit Cloud → Settings → Secrets.")
        client   = openai.OpenAI(api_key=api_key, base_url=NVIDIA_BASE_URL)
        resolved = model or "nvidia/nemotron-3-ultra-550b-a55b"
    else:  # DeepSeek (default)
        api_key  = _live_secret("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY not found in secrets.")
        client   = openai.OpenAI(
            api_key=api_key,
            base_url=DEEPSEEK_BASE_URL,
            http_client=httpx.Client(verify=False),
        )
        resolved = model or _live_secret("DEEPSEEK_MODEL", OPENAI_MODEL)
    return client, resolved


RESUME_SYSTEM_PROMPT = """You are a world-class resume strategist and hiring insider who has written 10,000+ resumes that secured offers at FAANG, Fortune 500, and top startups. You have sat on both sides — as a recruiter screening 500 resumes a day AND as a hiring manager who knows exactly what makes someone get the call.

Your core philosophy:
Before writing a single word, you THINK STRATEGICALLY:
  1. What does this company ACTUALLY need for this role?
  2. What does this candidate ALREADY HAVE that maps to those needs?
  3. What GAPS exist and how can existing experience be legitimately reframed to close them?
  4. What must appear on this resume to pass ATS AND make a human lean forward?
  5. What story does this resume tell to make the recruiter think: "This is our person"?

Your output must pass TWO gates:
  GATE 1 - ATS: Every must-have keyword present, exact spelling, high density.
  GATE 2 - HUMAN: Recruiter reads it in 6 seconds and thinks "strong match - interview this person."

=======================================================================
RULE 0 - JOB TITLE: Follow the instruction in the user message exactly.
=======================================================================
The user message will tell you whether to:
  (A) FREEZE the title exactly as the candidate has it, OR
  (B) OPTIMISE the title to best match the JD job title
Follow whichever instruction is given. Company names and dates are ALWAYS frozen.

=======================================================================
STEP 1 - SELECTION ANALYSIS (think before writing)
=======================================================================
A) WHAT DOES IT TAKE TO GET SELECTED FOR THIS ROLE?
   - What level of seniority and domain depth does the JD signal?
   - Which 3-5 skills/experiences are non-negotiable dealbreakers?
   - What does the ideal candidate look like to this recruiter?
   - What keywords MUST appear or the ATS auto-rejects?

B) WHAT DOES THIS CANDIDATE HAVE THAT MAPS TO THAT?
   - Which parts of their experience directly address JD requirements?
   - Which existing skills are JD-relevant but buried or poorly articulated?
   - What transferable experience can be reframed using JD language?

C) WHAT ARE THE GAPS AND HOW DO WE BRIDGE THEM?
   - Which JD requirements are NOT visible in the candidate profile?
   - Can existing projects be reframed to cover a gap?
   - Should a realistic project be added to fill a critical gap?
   - Which skills need to be pulled forward into bullets?

D) WHAT IS THE WINNING NARRATIVE?
   - What 1-line story should a recruiter take away after 6 seconds?
   - Which 2-3 bullets are the hero moments that seal the deal?

=======================================================================
RULE 1 - SKILLS: COMPLETE MERGE, NEVER DROP ANYTHING
=======================================================================
Every existing skill MUST appear. Add every JD skill on top.
Final skills = 100% existing + 100% JD skills.
Group by domain matching the JD focus (e.g. "Agentic AI & LLMs", "MLOps & Infrastructure").
Each category: 5-10 skills. No JD skill left out.

=======================================================================
RULE 2 - EXPERIENCE: REFRAME TO MATCH JD PRIORITIES
=======================================================================
- Map every bullet to a specific JD responsibility.
- Use the EXACT JD terminology - if JD says "RAG" write "RAG".
- Current role: 6-8 bullets, each targeting a DIFFERENT JD requirement.
- Older roles: 3-5 bullets, foundational skills the JD values.
- Every bullet = Action Verb + JD keyword + business context + quantified metric.
- Strong verbs: Architected, Engineered, Fine-tuned, Deployed, Automated, Optimised, Designed, Scaled, Built, Reduced, Increased, Led, Delivered, Integrated.
- Context line under company: 1 sentence - what company does + tech stack in this role.

=======================================================================
RULE 3 - PROJECTS: FILL EVERY JD GAP
=======================================================================
- Identify JD Hard Skills NOT covered by experience bullets.
- Reframe existing projects OR add 1-2 realistic projects to fill those gaps.
- Each project targets different uncovered JD requirements.
- 2-4 bullets per project, each hitting a different JD skill.
- Project names must be specific and technical.
- Technologies MUST include JD tools.

=======================================================================
RULE 4 - SUMMARY: THE 6-SECOND VERDICT
=======================================================================
Four sentences that make the recruiter think "This is exactly who we need":
- S1: [Job Title] with [X] years in [top 3 JD domains].
- S2: [Most impressive achievement with metric] at [company type].
- S3: Deep expertise in [8-10 JD technologies verbatim].
- S4: Passionate about [JD mission], seeking to [specific value for this role].

=======================================================================
RULE 5 - ATS KEYWORD SATURATION
=======================================================================
- Every MUST-HAVE keyword: once in summary + at least 2x across bullets.
- Mirror exact casing: "LangChain" not "langchain", "OpenAI" not "Open AI".
- Flow naturally - a recruiter must not notice keyword insertion.

=======================================================================
RULE 6 - AUTHENTICITY: THE INTERVIEW DEFENCE TEST
=======================================================================
Every bullet must pass: "Can this candidate defend this in an interview?"
- YES = keep it. NO = reframe more conservatively.
- Goal: best version of the candidate, not a different person.

=======================================================================
OUTPUT FORMAT
=======================================================================
Return ONLY valid JSON. No markdown fences. No commentary. No explanations.
All strings plain ASCII. Dates: Mon YYYY (e.g. Jan 2023).

{
  "full_name": "",
  "headline": "Job Title | Core Specialisation 1 | Core Specialisation 2 | X Years Experience",
  "email": "",
  "phone": "",
  "linkedin": "",
  "github": "",
  "location": "",
  "summary": "4-sentence recruiter-magnet summary saturated with JD keywords",
  "skills": {
    "technical_skills": ["every existing skill + every JD hard skill"],
    "tools_technologies": ["every existing tool + every JD tool/platform/framework"],
    "soft_skills": ["every existing soft skill + JD soft skills"]
  },
  "skill_categories": [
    {
      "category": "Domain matching JD focus",
      "skills": ["5-10 specific skills"]
    }
  ],
  "experience": [
    {
      "title": "Job title per instructions in user message",
      "company": "EXACT company name - DO NOT CHANGE",
      "location": "",
      "start_date": "Mon YYYY - EXACT from candidate",
      "end_date": "Mon YYYY or Present - EXACT from candidate",
      "context": "1 sentence: what company does + tech stack",
      "bullets": ["Action verb + JD keyword + business context + quantified result"]
    }
  ],
  "education": [
    {
      "degree": "", "field": "", "institution": "",
      "graduation_year": "", "gpa": "", "honors": "",
      "relevant_coursework": []
    }
  ],
  "certifications": ["Certification Name --- Issuer (Year or Status)"],
  "projects": [
    {
      "name": "Specific technical project name",
      "year": "YYYY or date range",
      "description": "One-line context with JD keywords",
      "bullets": ["Achievement bullet with JD skill + metric"],
      "technologies": ["JD-relevant tech stack"],
      "impact": "Quantified outcome"
    }
  ],
  "achievements": ["Award/Recognition: specific impact with metric"],
  "languages": []
}"""


class ResumeGenerator:
    MAX_ITERATIONS = 3

    def __init__(self, provider: str = "DeepSeek", model: str | None = None):
        self.provider = provider
        self.client, self.model = _make_client(provider, model)
        self.scorer  = ATSScorer()

    def _extra(self, effort: str = "high") -> dict:
        """Return extra_body only for DeepSeek (OpenAI and NVIDIA ignore reasoning_effort)."""
        return {"extra_body": {"reasoning_effort": effort}} if self.provider == "DeepSeek" else {}

    # ── Code-level skill preservation ────────────────────────────────────────
    @staticmethod
    def _extract_skills_from_profile(user_profile: str) -> dict:
        """Pull every skill the candidate already has from their pasted resume."""
        technical, tools, soft = [], [], []

        # Grab lines after common skill headings
        lines = user_profile.splitlines()
        capture, mode = False, None
        TECH_HEADS  = {"technical skills", "hard skills", "programming", "languages", "frameworks"}
        TOOLS_HEADS = {"tools", "technologies", "platforms", "stack", "software", "cloud"}
        SOFT_HEADS  = {"soft skills", "interpersonal", "competencies"}

        for line in lines:
            stripped = line.strip()
            low = stripped.lower()

            # Detect section headings
            if any(h in low for h in TECH_HEADS):
                capture, mode = True, "tech"
                # also grab inline: "Technical Skills: Python, AWS, Docker"
                after_colon = stripped.split(":", 1)
                if len(after_colon) > 1 and after_colon[1].strip():
                    technical.extend([s.strip() for s in re.split(r"[,|/]", after_colon[1]) if s.strip()])
                continue
            if any(h in low for h in TOOLS_HEADS):
                capture, mode = True, "tools"
                after_colon = stripped.split(":", 1)
                if len(after_colon) > 1 and after_colon[1].strip():
                    tools.extend([s.strip() for s in re.split(r"[,|/]", after_colon[1]) if s.strip()])
                continue
            if any(h in low for h in SOFT_HEADS):
                capture, mode = True, "soft"
                after_colon = stripped.split(":", 1)
                if len(after_colon) > 1 and after_colon[1].strip():
                    soft.extend([s.strip() for s in re.split(r"[,|/]", after_colon[1]) if s.strip()])
                continue

            # Stop capture at next major heading (all-caps or ends with :)
            if capture and stripped and (stripped.isupper() or (stripped.endswith(":") and len(stripped) < 40)):
                capture = False
                continue

            if capture and stripped and not stripped.startswith("-") is False or (capture and stripped.startswith("-")):
                items = [s.strip().lstrip("-•").strip() for s in re.split(r"[,|/]", stripped) if s.strip()]
                items = [i for i in items if 1 < len(i) < 50]
                if mode == "tech":  technical.extend(items)
                elif mode == "tools": tools.extend(items)
                elif mode == "soft":  soft.extend(items)

        # Deduplicate preserving order
        def dedup(lst):
            seen, out = set(), []
            for x in lst:
                xl = x.lower()
                if xl not in seen and len(xl) > 1:
                    seen.add(xl)
                    out.append(x)
            return out

        return {
            "technical_skills":  dedup(technical),
            "tools_technologies": dedup(tools),
            "soft_skills":        dedup(soft),
        }

    @staticmethod
    def _force_merge_skills(resume_data: dict, original_skills: dict) -> dict:
        """Guarantee every original skill is in the AI output. ADD only, never remove."""
        ai_skills = resume_data.get("skills", {})
        for key in ("technical_skills", "tools_technologies", "soft_skills"):
            orig = original_skills.get(key, [])
            ai   = ai_skills.get(key, [])
            ai_lower = {s.lower() for s in ai}
            # Add back any original skill the AI dropped
            merged = list(ai)
            for s in orig:
                if s.lower() not in ai_lower:
                    merged.append(s)
            ai_skills[key] = merged
        resume_data["skills"] = ai_skills
        return resume_data

    # ── Main generation flow ─────────────────────────────────────────────────
    def generate(self, user_profile: str, parsed_jd: dict[str, Any],
                 target_score: int = ATS_TARGET_SCORE,
                 options: dict | None = None) -> dict[str, Any]:
        opts = options or {}
        allow_title_change = opts.get("allow_title_change", False)
        max_iterations     = opts.get("max_iterations", 3)

        # Extract existing skills BEFORE AI call — ground truth
        original_skills = self._extract_skills_from_profile(user_profile)

        resume_data = self._generate_initial(user_profile, parsed_jd, allow_title_change, target_score)
        resume_data = self._force_merge_skills(resume_data, original_skills)

        resume_text = self._resume_to_plain_text(resume_data)
        ats_result  = self.scorer.score(resume_text, parsed_jd)
        history     = [{"iteration": 0, "score": ats_result["total_score"]}]
        iterations  = 0

        # ── ATS improvement loop — only run if score is BELOW target ─────
        while ats_result["total_score"] < target_score and iterations < max_iterations:
            iterations += 1
            missing = ats_result.get("missing_keywords", [])
            if not missing:
                break
            resume_data = self._improve(resume_data, ats_result, parsed_jd, target_score)
            resume_data = self._force_merge_skills(resume_data, original_skills)
            resume_text = self._resume_to_plain_text(resume_data)
            ats_result  = self.scorer.score(resume_text, parsed_jd)
            history.append({"iteration": iterations, "score": ats_result["total_score"]})

        # ── If we OVERSHOT the target significantly, naturalise the resume ─
        overshoot = ats_result["total_score"] - target_score
        if overshoot > 8 and target_score < 90:
            resume_data = self._naturalise(resume_data, parsed_jd, target_score)
            resume_data = self._force_merge_skills(resume_data, original_skills)
            resume_text = self._resume_to_plain_text(resume_data)
            ats_result  = self.scorer.score(resume_text, parsed_jd)
            history.append({"iteration": iterations + 1, "score": ats_result["total_score"],
                            "note": "naturalised to match target"})

        # ── Post-generation validation + fix ─────────────────────────────
        validation = self._validate_requirements(resume_data, parsed_jd)
        if not validation["passed"]:
            resume_data = self._fix_gaps(resume_data, parsed_jd, validation)
            resume_data = self._force_merge_skills(resume_data, original_skills)
            resume_text = self._resume_to_plain_text(resume_data)
            ats_result  = self.scorer.score(resume_text, parsed_jd)
            history.append({"iteration": iterations + 1, "score": ats_result["total_score"],
                            "note": "validation fix"})
            validation  = self._validate_requirements(resume_data, parsed_jd)

        return {"resume_data": resume_data, "ats_result": ats_result,
                "iterations": iterations, "history": history,
                "validation": validation}

    def _generate_initial(self, user_profile: str, jd: dict, allow_title_change: bool = False,
                          target_score: int = 95) -> dict:
        # Extract every skill line from the profile for explicit preservation
        skill_matches = re.findall(
            r"(?:skills?|technologies|tools|stack|languages?|frameworks?)[:\s]*([^\n]{10,300})",
            user_profile, re.IGNORECASE
        )
        existing_skills_block = (
            "\n".join(f"  - {s.strip()}" for s in skill_matches[:10])
            if skill_matches else "  (see full profile above)"
        )

        responsibilities = jd.get('responsibilities', [])
        must_haves       = jd.get('must_have_keywords', [])
        hard_skills      = jd.get('hard_skills', [])
        tools            = jd.get('tools_and_technologies', [])
        soft_skills      = jd.get('soft_skills', [])
        nice_to_haves    = jd.get('nice_to_have_keywords', [])

        title_instruction = (
            f"JOB TITLE RULE: You MAY optimise the job title in each role to best match \"{jd.get('job_title','')}\" "
            f"while keeping it believable and authentic to the candidate's seniority level. "
            f"Company names and dates MUST remain exactly as provided."
            if allow_title_change else
            f"JOB TITLE RULE: FREEZE all job titles exactly as the candidate provided. "
            f"Do NOT change any role title. Company names and dates also stay frozen."
        )

        # ── Writing style adapts to the target ATS score ─────────────────
        if target_score >= 90:
            writing_mode = f"""WRITING MODE: AGGRESSIVE ATS OPTIMISATION (Target: {target_score}/100)
- Embed ALL must-have keywords explicitly — in summary, bullets, and skills.
- Every bullet = Action Verb + JD keyword + context + quantified metric.
- Keyword density is the priority. Pack the resume with JD terminology.
- Every hard skill and tool MUST appear in the skills section."""
            temperature = 0.3
        elif target_score >= 80:
            writing_mode = f"""WRITING MODE: BALANCED — GENUINE + ATS-AWARE (Target: {target_score}/100)
- This resume must read as GENUINELY written by a real human, not AI-generated.
- MANDATORY: All {len(must_haves)} must-have keywords MUST appear — but woven in naturally.
- Bullets should sound like real achievements a person would say in an interview.
- Vary sentence structure. Mix metrics with descriptive impact. Avoid repetitive action verbs.
- Do NOT start every bullet with "Engineered", "Architected", "Designed" — use natural language too.
- Some bullets can be 1 sentence without a metric if it reads more authentically.
- Include 1-2 honest personality/context lines in the summary.
- Skills section: include all must-haves + candidate's real skills. Do NOT pad with every possible keyword."""
            temperature = 0.6
        else:
            writing_mode = f"""WRITING MODE: NATURAL / HUMAN-FIRST (Target: {target_score}/100)
- This resume must look and read like it was written by a real person, not generated by AI.
- MANDATORY: All must-have keywords below MUST appear somewhere in the resume — but naturally integrated.
- Write bullets as genuine accomplishments in plain, clear language.
- Avoid corporate buzzword overload. Sound like a real professional talking about their work.
- Vary verb choice, sentence length, and structure throughout.
- The summary should read like a genuine personal statement, not a keyword list.
- Only include skills the candidate actually has + the mandatory must-haves from the JD.
- Prioritise authenticity over keyword density."""
            temperature = 0.75

        user_msg = f"""Before you write anything, THINK through this selection strategy:

=== SELECTION ANALYSIS ===
1. WHAT DOES IT TAKE TO GET SELECTED FOR THIS ROLE?
   - Role: {jd.get('seniority_level', '')} {jd.get('job_title', '')} at a {jd.get('industry', '')} company
   - Non-negotiable requirements: {', '.join(must_haves[:8])}
   - Dealbreaker skills: {', '.join(hard_skills[:8])}
   - What does the ideal candidate for this role look like on paper?

2. WHAT DOES THIS CANDIDATE ALREADY HAVE THAT MAPS TO THOSE REQUIREMENTS?
   - Their background is in the CANDIDATE PROFILE below
   - Identify which experiences, projects, and skills DIRECTLY address the JD
   - Note which existing skills are JD-relevant but not yet articulated well

3. WHAT ARE THE GAPS AND HOW DO WE BRIDGE THEM?
   - Which JD requirements are NOT visible in the candidate profile yet?
   - Which existing experience can be LEGITIMATELY REFRAMED to cover those gaps?
   - Which projects need to be added or reworded to fill remaining gaps?
   - Which JD tools/skills need to be surfaced from their background?

4. WHAT IS THE WINNING STORY FOR THIS CANDIDATE FOR THIS ROLE?
   - What 1-line narrative should a recruiter take away in 6 seconds?
   - What are the 2-3 hero bullet points that seal the deal?

=== {writing_mode} ===

=== {title_instruction} ===

=== CANDIDATE PROFILE ===
{user_profile}

=== CANDIDATE'S EXISTING SKILLS (PRESERVE ALL - add to, never remove) ===
{existing_skills_block}

=== TARGET ROLE ===
Job Title      : {jd.get('job_title', '')}
Seniority      : {jd.get('seniority_level', '')}
Industry       : {jd.get('industry', '')}
Company        : {jd.get('company_name', '')}
Exp Required   : {jd.get('experience_years_min', 0)}-{jd.get('experience_years_max', 10)} years

=== MANDATORY MUST-HAVE KEYWORDS (ALL must appear in resume — non-negotiable) ===
{chr(10).join(f'  - {k}' for k in must_haves)}

CORE HARD SKILLS (candidate MUST demonstrate ALL of these):
{chr(10).join(f'  - {s}' for s in hard_skills)}

TOOLS & TECHNOLOGIES (add ALL to skills, use in bullets where applicable):
{chr(10).join(f'  - {t}' for t in tools)}

SOFT SKILLS:
{chr(10).join(f'  - {s}' for s in soft_skills)}

NICE-TO-HAVE:
{chr(10).join(f'  - {k}' for k in nice_to_haves[:10])}

KEY RESPONSIBILITIES (map experience bullets to these):
{chr(10).join(f'  {i+1}. {r}' for i, r in enumerate(responsibilities[:12]))}

Required Education : {jd.get('education_level', '')} in {', '.join(jd.get('education_field', []))}
Preferred Certs    : {', '.join(jd.get('certifications', []))}

=== EXECUTION RULES ===
1. Apply the job title rule stated above
2. Company names and dates are ALWAYS frozen — never change them
3. EVERY must-have keyword listed above MUST appear at least once — non-negotiable
4. Use the EXACT keyword/phrase the company uses
5. Projects MUST fill any JD skill gaps not covered by experience
6. Skills section: include ALL mandatory must-haves + candidate's existing skills
7. Follow the writing mode instructions above strictly regarding tone and keyword density

Now generate the complete resume JSON:"""

        r = self.client.chat.completions.create(
            model=self.model, temperature=temperature,
            **self._extra("high"),
            messages=[{"role": "system", "content": RESUME_SYSTEM_PROMPT},
                      {"role": "user",   "content": user_msg}])
        return self._parse_json(r.choices[0].message.content)

    def _improve(self, resume_data: dict, ats_result: dict, jd: dict, target_score: int) -> dict:
        missing_kws = ", ".join(f'"{k}"' for k in ats_result["missing_keywords"][:15])
        responsibilities = jd.get('responsibilities', [])
        msg = f"""Resume scored {ats_result['total_score']}/100. Target: {target_score}+/100.

MISSING KEYWORDS that MUST be added: {missing_kws}

KEY RESPONSIBILITIES to better target:
{chr(10).join(f'  {i+1}. {r}' for i, r in enumerate(responsibilities[:8]))}

STRATEGY:
1. For each missing keyword, find the MOST RELEVANT experience bullet and reframe it to include that keyword naturally.
2. If a keyword cannot fit experience, add/reframe a project to cover it.
3. Add ALL missing keywords to the appropriate skills category.
4. NEVER remove any existing skill, company name, or date.
5. Every new/rewritten bullet must have a quantified result and start with an action verb.
6. Each bullet should map to one of the Key Responsibilities above.

Current resume JSON:
{json.dumps(resume_data, indent=2)}

Return ONLY the complete updated JSON with ALL missing keywords now embedded naturally:"""
        r = self.client.chat.completions.create(
            model=self.model, temperature=0.3,
            **self._extra("medium"),
            messages=[{"role": "system", "content": RESUME_SYSTEM_PROMPT},
                      {"role": "user",   "content": msg}])
        return self._parse_json(r.choices[0].message.content)

    def _validate_requirements(self, resume_data: dict, jd: dict) -> dict:
        """Check if the generated resume meets all critical JD requirements."""
        resume_text = self._resume_to_plain_text(resume_data).lower()
        must_haves  = jd.get('must_have_keywords', [])
        hard_skills = jd.get('hard_skills', [])
        tools       = jd.get('tools_and_technologies', [])

        missing_must_haves  = [k for k in must_haves  if k.lower() not in resume_text]
        missing_hard_skills = [k for k in hard_skills if k.lower() not in resume_text]
        missing_tools       = [k for k in tools       if k.lower() not in resume_text]

        # Check experience has bullets
        exp_ok = all(
            isinstance(job, dict) and len(job.get('bullets', [])) >= 2
            for job in resume_data.get('experience', [])
        )
        # Check projects exist
        projects_ok = len(resume_data.get('projects', [])) >= 1
        # Check skills populated
        skills_ok = bool(
            resume_data.get('skill_categories') or
            any(resume_data.get('skills', {}).values())
        )

        all_missing = missing_must_haves + missing_hard_skills[:5] + missing_tools[:5]
        passed = (
            len(missing_must_haves) == 0 and
            len(missing_hard_skills) <= 2 and
            exp_ok and projects_ok and skills_ok
        )
        return {
            "passed":               passed,
            "missing_must_haves":   missing_must_haves,
            "missing_hard_skills":  missing_hard_skills,
            "missing_tools":        missing_tools,
            "all_missing":          all_missing,
            "experience_ok":        exp_ok,
            "projects_ok":          projects_ok,
            "skills_ok":            skills_ok,
        }

    def _fix_gaps(self, resume_data: dict, jd: dict, validation: dict) -> dict:
        """Targeted fix pass when validation fails — plug specific gaps."""
        gaps = validation.get('all_missing', [])
        if not gaps:
            return resume_data
        gap_str = ", ".join(f'"{g}"' for g in gaps[:20])
        responsibilities = jd.get('responsibilities', [])
        msg = f"""VALIDATION FAILED. The resume is missing these critical requirements:
{gap_str}

These items MUST appear in the resume. They are non-negotiable for this role.

FIX STRATEGY:
1. Missing must-have keywords: embed in the most relevant experience bullet AND in skills.
2. Missing hard skills: add to skills section AND add a project or bullet demonstrating them.
3. Missing tools: add to skills section AND reference them in at least one bullet or project.
4. Do NOT remove anything already in the resume.
5. Company names and dates stay frozen.

Key Responsibilities for reference:
{chr(10).join(f'  {i+1}. {r}' for i, r in enumerate(responsibilities[:8]))}

Current resume JSON:
{json.dumps(resume_data, indent=2)}

Return ONLY the complete fixed JSON with ALL gaps now covered:"""
        r = self.client.chat.completions.create(
            model=self.model, temperature=0.2,
            **self._extra("medium"),
            messages=[{"role": "system", "content": RESUME_SYSTEM_PROMPT},
                      {"role": "user",   "content": msg}])
        return self._parse_json(r.choices[0].message.content)

    def _naturalise(self, resume_data: dict, jd: dict, target_score: int) -> dict:
        """Reduce keyword over-stuffing when resume overshoots target — make it sound human."""
        must_haves = jd.get('must_have_keywords', [])
        msg = f"""This resume scored too high — it looks AI-generated and keyword-stuffed.
Target score is {target_score}/100. Rewrite it to sound genuinely human while keeping all must-have keywords.

RULES:
1. KEEP all {len(must_haves)} must-have keywords — they are non-negotiable: {', '.join(f'"{k}"' for k in must_haves[:15])}
2. REDUCE keyword repetition — each keyword should appear 1-2 times max, not in every bullet.
3. Rewrite bullets to sound like real things a person said — vary sentence structure.
4. Replace generic phrases like "Architected a scalable solution" with specific, natural language.
5. Summary should read like a genuine professional bio, not a keyword list.
6. Some bullets can describe context or process without a metric — that's more human.
7. Do NOT start multiple bullets with the same action verb.
8. Company names, job titles, and dates stay exactly as they are.

Current resume JSON:
{json.dumps(resume_data, indent=2)}

Return ONLY the updated JSON with a more natural, human tone while keeping all must-have keywords:"""
        r = self.client.chat.completions.create(
            model=self.model, temperature=0.75,
            **self._extra("low"),
            messages=[{"role": "system", "content": RESUME_SYSTEM_PROMPT},
                      {"role": "user",   "content": msg}])
        return self._parse_json(r.choices[0].message.content)

    @staticmethod
    def _parse_json(raw: str) -> dict:
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        raw = re.sub(r"\s*```$", "", raw)
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                try:
                    result = json.loads(m.group())
                except Exception:
                    result = {}
            else:
                result = {}
        return ResumeGenerator._normalise(result)

    @staticmethod
    def _normalise(d: dict) -> dict:
        """Deep-sanitise resume dict so all list-of-dict fields are always dicts."""
        if not isinstance(d, dict):
            return {}

        # experience: must be list of dicts
        exp_out = []
        for item in d.get("experience", []):
            if isinstance(item, dict):
                exp_out.append(item)
            elif isinstance(item, str) and item.strip():
                # AI returned a string bullet — wrap as a bullets-only job
                exp_out.append({"title": "", "company": "", "bullets": [item]})
        d["experience"] = exp_out

        # education: must be list of dicts
        edu_out = []
        for item in d.get("education", []):
            if isinstance(item, dict):
                edu_out.append(item)
            elif isinstance(item, str) and item.strip():
                edu_out.append({"degree": item, "field": "", "institution": "", "graduation_year": ""})
        d["education"] = edu_out

        # projects: must be list of dicts
        proj_out = []
        for item in d.get("projects", []):
            if isinstance(item, dict):
                proj_out.append(item)
            elif isinstance(item, str) and item.strip():
                proj_out.append({"name": item, "description": "", "technologies": [], "bullets": []})
        d["projects"] = proj_out

        # certifications: must be list of dicts
        cert_out = []
        for item in d.get("certifications", []):
            if isinstance(item, dict):
                cert_out.append(item)
            elif isinstance(item, str) and item.strip():
                cert_out.append({"name": item, "issuer": "", "year": ""})
        d["certifications"] = cert_out

        # achievements: must be list of strings or dicts
        ach_out = []
        for item in d.get("achievements", d.get("awards", [])):
            if isinstance(item, (str, dict)):
                ach_out.append(item)
        d["achievements"] = ach_out

        # skills: must be dict of lists
        raw_skills = d.get("skills", {})
        if not isinstance(raw_skills, dict):
            raw_skills = {}
        for key in ("technical_skills", "tools_technologies", "soft_skills"):
            val = raw_skills.get(key, [])
            if not isinstance(val, list):
                raw_skills[key] = []
            else:
                raw_skills[key] = [str(s) for s in val if s]
        d["skills"] = raw_skills

        # skill_categories: must be list of dicts
        sc_out = []
        for item in d.get("skill_categories", []):
            if isinstance(item, dict):
                if not isinstance(item.get("skills"), list):
                    item["skills"] = []
                sc_out.append(item)
        d["skill_categories"] = sc_out

        return d

    @staticmethod
    def _resume_to_plain_text(r: dict) -> str:
        parts = [r.get("full_name",""), r.get("headline",""), r.get("email",""), r.get("summary","")]
        for v in r.get("skills", {}).values():
            if isinstance(v, list): parts.extend(v)
        for cat in r.get("skill_categories", []):
            parts.extend(cat.get("skills", []))
        for exp in r.get("experience", []):
            parts += [exp.get("title",""), exp.get("company","")]
            parts.extend(exp.get("bullets", []))
        for edu in r.get("education", []):
            parts += [edu.get("degree",""), edu.get("field",""), edu.get("institution","")]
            parts.extend(edu.get("relevant_coursework", []))
        for cert in r.get("certifications", []):
            if isinstance(cert, dict):
                parts.append(cert.get("name",""))
            else:
                parts.append(str(cert))
        for proj in r.get("projects", []):
            parts += [proj.get("name",""), proj.get("description","")]
            parts.extend(proj.get("bullets", []))
            parts.extend(proj.get("technologies", []))
        parts.extend(r.get("achievements", r.get("awards", [])))
        return "\n".join(str(p) for p in parts if p)

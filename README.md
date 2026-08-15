# 📄 ATS Resume & Cover Letter Builder

> **AI-powered resume tailoring that achieves 95%+ ATS scores — so you never get rejected by a bot.**

Built with GPT-4o · LaTeX quality output · Iterative ATS optimisation · Streamlit UI

---

## 🏗️ Architecture

```
User Background + Job Description
         │
         ▼
┌─────────────────────────┐
│   JD Parser (GPT-4o)    │  ← Extracts 30+ ATS keywords, skills, requirements
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Resume Generator       │  ← Writes ATS-optimised resume JSON
│  (GPT-4o, temp=0.3)     │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  ATS Scorer             │  ← Scores 0-100 across 8 dimensions
└──────────┬──────────────┘
           │ Score < 95? → Improve (max 3 rounds)
           ▼
┌─────────────────────────┐
│  Cover Letter Gen       │  ← Mirrors JD language, CAR format
│  (GPT-4o, temp=0.5)     │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  LaTeX Compiler         │  ← Renders Jinja2 templates → .tex → PDF
│  (pdflatex or Overleaf) │
└─────────────────────────┘
```

## 📊 ATS Scoring Breakdown

| Category | Weight | What It Checks |
|----------|--------|----------------|
| Must-Have Keywords | 35% | Exact keyword match from JD |
| Hard Skills Coverage | 25% | All required technical skills present |
| Tools & Technologies | 15% | Specific tools/platforms/frameworks |
| Soft Skills | 5% | Communication, leadership, etc. |
| Job Title Match | 5% | Target title appears in resume |
| Education | 5% | Degree level matches requirement |
| Experience | 5% | Experience section exists |
| ATS Formatting | 5% | No tables, columns, special chars |

## 🚀 Quick Start

### 1. Clone / Navigate to project
```bash
cd ats-resume-builder
```

### 2. Create Python virtual environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API key
```bash
copy .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-your-key-here
```

### 5. Run the app
```bash
streamlit run app.py
```

App opens at: http://localhost:8501

---

## 📄 Getting PDF Output

### Option A: Install MiKTeX (Windows — Recommended)
1. Download from https://miktex.org/download
2. Install with default settings
3. Restart the app — PDF compilation works automatically

### Option B: Overleaf (No Installation)
1. Download the `.tex` file from the app
2. Go to https://www.overleaf.com → New Project → Upload `.tex`
3. Click Compile → Download PDF

### Option C: TeX Live (Linux/Mac)
```bash
# Ubuntu/Debian
sudo apt install texlive-full

# Mac (Homebrew)
brew install --cask mactex
```

---

## 🎯 Why This Achieves 95%+ ATS Scores

1. **Keyword Extraction** — GPT-4o reads the JD like an ATS and identifies every scannable term
2. **Verbatim Matching** — Uses EXACT phrases from JD (ATS does string matching, not semantic)
3. **Iterative Refinement** — Scores resume → identifies gaps → improves → repeats (up to 3x)
4. **LaTeX Format** — Single-column, no tables, no images — pure text ATS can parse
5. **Standard Sections** — Uses exact section names ATS systems expect
6. **Quantified Bullets** — Numbers and metrics increase relevance scores

## 📁 Project Structure

```
ats-resume-builder/
├── app.py                      # Streamlit UI
├── resume_generator.py         # AI resume generation engine
├── cover_letter_generator.py   # AI cover letter engine
├── latex_compiler.py           # LaTeX rendering + PDF compilation
├── config.py                   # Central configuration
├── requirements.txt
├── .env.example                # Environment template
├── utils/
│   ├── jd_parser.py            # JD → structured data (GPT-4o)
│   └── ats_scorer.py           # Resume → ATS score (0-100)
├── latex_templates/
│   ├── resume.tex.j2           # ATS-safe resume LaTeX template
│   └── cover_letter.tex.j2     # Cover letter LaTeX template
└── output/                     # Generated .tex and .pdf files
```

## 💡 Tips for Best Results

- **Paste the full JD** — not a summary. The more requirements the AI sees, the better
- **Include real metrics** — "increased revenue by 23%", "led team of 8", "reduced latency 40ms"
- **List ALL your skills** — even if you think they're obvious; the AI will prioritise the relevant ones
- **Multiple applications** — run separately for each job; never use the same resume twice
- **Company name matters** — if the JD mentions the company, include it for personalisation

## 🔧 Configuration

Edit `.env`:
```env
OPENAI_API_KEY=sk-...          # Required
OPENAI_MODEL=gpt-4o            # or gpt-4-turbo, gpt-3.5-turbo
LATEX_COMPILER_PATH=           # Auto-detected if blank
```

## 📜 License
MIT — Use freely for personal job applications.

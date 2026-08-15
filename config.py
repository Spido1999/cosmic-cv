"""
config.py - Central configuration for ATS Resume Builder
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── API Key: reads from Streamlit secrets (cloud) or .env (local) ──────────
def _get_secret(key: str, fallback: str = "") -> str:
    """Try Streamlit secrets first (cloud deploy), then env vars, then fallback."""
    try:
        import streamlit as st
        val = st.secrets.get(key, None)
        if val:
            return val
    except Exception:
        pass
    return os.getenv(key, fallback)

# ── Provider base URLs only — keys are read LIVE at call-time via _live_secret ─
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# ── OpenAI config ────────────────────────────────────────────────────────────
OPENAI_BASE_URL   = "https://api.openai.com/v1"

# ── Legacy alias — model name only, NOT a secret ─────────────────────────────
OPENAI_MODEL      = _get_secret("DEEPSEEK_MODEL", "deepseek-v4-pro")  # model name only, no secret

# ── Model catalogs per provider ──────────────────────────────────────────────
DEEPSEEK_MODELS = [
    "deepseek-v4-pro",
    "deepseek-chat",
    "deepseek-reasoner",
    "deepseek-coder",
]

OPENAI_MODELS = [
    # ── GPT-4.1 family (Apr 2025) ──
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    # ── o-series reasoning models ──
    "o3",
    "o4-mini",
    "o3-mini",
    "o1",
    "o1-mini",
    # ── GPT-4o family ──
    "gpt-4o",
    "gpt-4o-mini",
    # ── Legacy ──
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
]

PROVIDER_MODELS = {
    "DeepSeek": DEEPSEEK_MODELS,
    "OpenAI":   OPENAI_MODELS,
}

# ── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR              = os.path.dirname(os.path.abspath(__file__))
LATEX_TEMPLATES_DIR   = os.path.join(BASE_DIR, "latex_templates")
OUTPUT_DIR            = os.path.join(BASE_DIR, os.getenv("OUTPUT_DIR", "output"))
LATEX_COMPILER_PATH   = os.getenv("LATEX_COMPILER_PATH", "")

# ── ATS Scoring thresholds ──────────────────────────────────────────────────
ATS_PASS_SCORE        = 80   # minimum score to show green
ATS_TARGET_SCORE      = 95   # target for "excellent" badge

# ── Ensure output dir exists ────────────────────────────────────────────────
os.makedirs(OUTPUT_DIR, exist_ok=True)

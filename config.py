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
OPENAI_BASE_URL   = "https://api.openai.com/v1"
NVIDIA_BASE_URL   = "https://integrate.api.nvidia.com/v1"

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
    # ── GPT-5.6 family (Latest · Aug 2026) ──
    "gpt-5.6-sol",
    "gpt-5.6-terra",
    "gpt-5.6-luna",
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

NVIDIA_MODELS = [
    # ── NVIDIA Nemotron (Flagship) ──
    "nvidia/nemotron-3-ultra-550b-a55b",
    "nvidia/nemotron-3.5-lightning-30b-a3b",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    # ── Meta Llama via NVIDIA NIM ──
    "meta/llama-3.3-70b-instruct",
    "meta/llama-3.1-405b-instruct",
    "meta/llama-3.1-70b-instruct",
    "meta/llama-3.1-8b-instruct",
    # ── Mistral / Mixtral ──
    "mistralai/mixtral-8x22b-instruct-v0.1",
    "mistralai/mistral-large-2-instruct",
    "mistralai/mistral-7b-instruct-v0.3",
    # ── Qwen ──
    "qwen/qwen2.5-72b-instruct",
    "qwen/qwen2.5-coder-32b-instruct",
    # ── Google Gemma ──
    "google/gemma-3-27b-it",
    "google/gemma-3n-e4b-it",
    # ── DeepSeek via NVIDIA NIM ──
    "deepseek-ai/deepseek-r1",
    "deepseek-ai/deepseek-r1-0528",
    # ── Z.ai GLM ──
    "z-ai/glm-5.2",
    # ── Poolside ──
    "poolside/laguna-xs-2.1",
]

PROVIDER_MODELS = {
    "DeepSeek": DEEPSEEK_MODELS,
    "OpenAI":   OPENAI_MODELS,
    "NVIDIA":   NVIDIA_MODELS,
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

# setup.ps1 — One-click setup for ATS Resume Builder (Windows PowerShell)
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ATS Resume Builder — Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# 1. Create virtualenv
if (-Not (Test-Path "venv")) {
    Write-Host "`n[1/4] Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host "`n[1/4] Virtual environment already exists." -ForegroundColor Green
}

# 2. Activate
Write-Host "`n[2/4] Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# 3. Install packages
Write-Host "`n[3/4] Installing Python packages..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt

# 4. Copy .env
if (-Not (Test-Path ".env")) {
    Write-Host "`n[4/4] Creating .env from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "  ⚠️  IMPORTANT: Edit .env and set your OPENAI_API_KEY" -ForegroundColor Red
} else {
    Write-Host "`n[4/4] .env already exists." -ForegroundColor Green
}

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host "  Next steps:" -ForegroundColor White
Write-Host "  1. Edit .env and add your OpenAI API key" -ForegroundColor White
Write-Host "  2. Run: streamlit run app.py" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan

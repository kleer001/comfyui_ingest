# VFX Pipeline Bootstrap Script - Conda Edition (Windows)
# Downloads and runs the installation wizard
#
# Usage:
#   irm https://raw.githubusercontent.com/kleer001/comfyui_ingest/main/scripts/bootstrap_conda.ps1 | iex

$ErrorActionPreference = "Stop"

$REPO_URL = "https://github.com/kleer001/comfyui_ingest.git"
$INSTALL_DIR = Join-Path (Get-Location) "comfyui_ingest"

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  VFX Pipeline - Automated Installer" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..."

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "X Error: git is not installed" -ForegroundColor Red
    Write-Host "   Install with: winget install Git.Git --scope user" -ForegroundColor Yellow
    exit 1
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "X Error: python is not installed" -ForegroundColor Red
    Write-Host "   Install with: winget install Anaconda.Miniconda3 --scope user" -ForegroundColor Yellow
    exit 1
}

Write-Host "OK Prerequisites met" -ForegroundColor Green
Write-Host ""

# Clone or update repository
if (Test-Path $INSTALL_DIR) {
    Write-Host "Directory $INSTALL_DIR already exists."
    $response = Read-Host "Update existing installation? (y/N)"
    if ($response -match "^[Yy]$") {
        Write-Host "Updating repository..."
        Push-Location $INSTALL_DIR
        git pull
    } else {
        Write-Host "Using existing installation at $INSTALL_DIR"
        Push-Location $INSTALL_DIR
    }
} else {
    Write-Host "Cloning repository to $INSTALL_DIR..."
    git clone $REPO_URL $INSTALL_DIR
    Push-Location $INSTALL_DIR
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  Launching Installation Wizard" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Run the wizard
python scripts/install_wizard.py $args

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Activate environment: conda activate vfx-pipeline"
Write-Host "  2. Or use: . $INSTALL_DIR\.vfx_pipeline\activate.ps1"
Write-Host "  3. Read: $INSTALL_DIR\README.md"
Write-Host ""

Pop-Location

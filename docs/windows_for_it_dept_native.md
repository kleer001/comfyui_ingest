# Windows IT Setup (Admin Required)

Run these as Administrator. Users handle everything else.

## 1. NVIDIA Driver + CUDA

```powershell
# Verify after install
nvidia-smi
nvcc --version
```

Download: https://www.nvidia.com/download/index.aspx
CUDA: https://developer.nvidia.com/cuda-toolkit-archive (11.8 or 12.1)

## 2. PowerShell Execution Policy

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
```

## 3. Long Paths

```powershell
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1
```

## Done

Users run:
```powershell
winget install Git.Git --scope user
winget install Anaconda.Miniconda3 --scope user
git clone https://github.com/kleer001/comfyui_ingest.git
cd comfyui_ingest
python scripts/install_wizard.py
```

Wizard auto-installs FFmpeg, COLMAP, and all dependencies to repo directory.

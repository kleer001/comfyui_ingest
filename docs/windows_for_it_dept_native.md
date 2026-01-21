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

Users run in PowerShell:
```powershell
irm https://raw.githubusercontent.com/kleer001/comfyui_ingest/main/scripts/bootstrap_conda.ps1 | iex
```

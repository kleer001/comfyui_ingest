# Windows Native Setup for IT Department

This document provides IT administrators with the minimal setup requirements to enable users to run the ComfyUI Ingest pipeline **natively on Windows** without Docker or WSL2.

For Docker/WSL2 installation, see [windows_for_it_dept_docker.md](windows_for_it_dept_docker.md).

## Prerequisites

- Windows 10 (version 1903+) or Windows 11 (64-bit)
- NVIDIA GPU with minimum 9 GB VRAM
- Administrator access (for initial setup only)

## Required Software Installation

IT administrators must install the following software. After initial setup, users can operate without administrator privileges.

### 1. NVIDIA GPU Driver

Download and install the latest NVIDIA GPU driver for the user's graphics card.

**Download Link:** https://www.nvidia.com/download/index.aspx

**Verification:**
```powershell
nvidia-smi
```
Should display GPU information and driver version.

### 2. CUDA Toolkit

Required for GPU-accelerated machine learning. Install CUDA Toolkit 11.8 or 12.x (match PyTorch requirements).

**Download Link:** https://developer.nvidia.com/cuda-toolkit-archive

**Recommended Version:** CUDA 11.8 or CUDA 12.1

**Installation Notes:**
- Default installation path: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x`
- Ensure "Add to PATH" is selected during installation

**Verification:**
```powershell
nvcc --version
```

### 3. Git for Windows

Required for cloning the repository and version control.

**Installation Options (choose one):**

```powershell
# Option A: winget (built into Windows 10/11)
winget install Git.Git

# Option B: Chocolatey
choco install git

# Option C: Manual download
# https://git-scm.com/download/win
```

**Verification:**
```powershell
git --version
```

### 4. Miniconda (Python Environment Manager)

Required for managing Python dependencies in isolated environments.

**Installation Options (choose one):**

```powershell
# Option A: winget
winget install Anaconda.Miniconda3

# Option B: Chocolatey
choco install miniconda3

# Option C: Manual download
# https://docs.conda.io/en/latest/miniconda.html
```

**Default Installation Path:** `C:\Users\<USERNAME>\miniconda3`

**Post-Installation:**
- Ensure conda is added to the user's PATH
- Initialize conda for PowerShell: `conda init powershell`

**Verification:**
```powershell
conda --version
```

### 5. FFmpeg

Required for video frame extraction and encoding.

**Installation Options (choose one):**

```powershell
# Option A: winget (recommended)
winget install ffmpeg

# Option B: Chocolatey
choco install ffmpeg

# Option C: Scoop
scoop install ffmpeg
```

**Verification:**
```powershell
ffmpeg -version
ffprobe -version
```

### 6. COLMAP (Optional - for Camera Tracking)

Required only if users need camera tracking/photogrammetry features.

**Installation Options (choose one):**

```powershell
# Option A: Chocolatey (recommended)
choco install colmap

# Option B: Manual download
# https://colmap.github.io/install.html
# Download pre-built Windows binaries
```

**Default Installation Paths:**
- Chocolatey: `C:\ProgramData\chocolatey\bin\colmap.exe`
- Manual: `C:\Program Files\COLMAP\COLMAP.bat`

**Verification:**
```powershell
colmap --help
```

### 7. Visual Studio Build Tools (Optional)

Required only if users need to compile C++ extensions for certain Python packages.

**Download Link:** https://visualstudio.microsoft.com/visual-cpp-build-tools/

**Required Components:**
- "Desktop development with C++" workload
- Windows 10/11 SDK
- MSVC v143 build tools

## Optional Software

### 7-Zip

For extracting model archives. Usually pre-installed on Windows.

```powershell
# If not installed:
winget install 7zip.7zip
```

### aria2

For faster parallel downloads of large model files.

```powershell
winget install aria2.aria2
```

## Critical System Configuration

**These settings are REQUIRED for the pipeline to function correctly. Without them, users will encounter errors that cannot be resolved without administrator access.**

### 1. PowerShell Execution Policy (REQUIRED)

**Impact if not configured:** Users will see "cannot be loaded because running scripts is disabled on this system" when running the activation script.

Allow running local PowerShell scripts:

```powershell
# Run as Administrator (one-time setup)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
```

**Verification:**
```powershell
Get-ExecutionPolicy -List
# LocalMachine should show "RemoteSigned"
```

### 2. Enable Long Paths (REQUIRED)

**Impact if not configured:** Installation fails with "path too long" errors when installing deep nested dependencies like ComfyUI custom nodes.

Windows has a 260-character path limit by default. This pipeline requires long path support due to nested node_modules and model directories.

**Option A: Group Policy (Domain environments)**
1. Open Group Policy Editor (`gpedit.msc`)
2. Navigate to: Computer Configuration > Administrative Templates > System > Filesystem
3. Enable "Enable Win32 long paths"

**Option B: Registry (Standalone machines)**
```powershell
# Run as Administrator
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1
```

**Verification:**
```powershell
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled"
# Should return 1
```

## Optional System Configuration

### 3. Enable Developer Mode (Optional)

Allows creating symbolic links without administrator privileges:

1. Open Windows Settings
2. Navigate to: Privacy & Security > For Developers
3. Enable "Developer Mode"

## Verification Checklist

After installation, verify all components are accessible:

```powershell
# Run these commands in a new PowerShell window

# GPU and CUDA
nvidia-smi
nvcc --version

# Core tools
git --version
conda --version
ffmpeg -version

# Optional
colmap --help
7z --help
aria2c --version
```

## User Instructions

Once IT has completed the above setup, users can bootstrap the pipeline by running in PowerShell:

```powershell
# Clone the repository
git clone https://github.com/kleer001/comfyui_ingest.git
cd comfyui_ingest

# Run the install wizard
python scripts/install_wizard.py
```

The install wizard will:
1. Detect the Windows environment
2. Create the conda environment
3. Install Python dependencies
4. Generate activation scripts (`activate.ps1`, `activate.bat`)
5. Download required AI models

## Post-Setup User Capabilities

After this one-time setup, users can operate independently without administrator privileges:
- Clone and update the repository
- Download and manage AI models
- Run the pipeline on video projects
- Install Python packages in their conda environment
- Process video projects

## Troubleshooting

### Conda Not Found

If `conda` is not recognized after installation:

```powershell
# Initialize conda for PowerShell
& "$env:USERPROFILE\miniconda3\Scripts\conda.exe" init powershell

# Restart PowerShell
```

### CUDA Not Detected

1. Verify NVIDIA driver is installed: `nvidia-smi`
2. Verify CUDA toolkit: `nvcc --version`
3. Check PATH includes CUDA bin directory:
   ```powershell
   $env:PATH -split ";" | Select-String "CUDA"
   ```

### FFmpeg Not Found

If FFmpeg was installed but not found:

```powershell
# Check if it's in a non-PATH location
Get-Command ffmpeg -ErrorAction SilentlyContinue

# Common locations to add to PATH:
# C:\ffmpeg\bin
# C:\Program Files\FFmpeg\bin
# %USERPROFILE%\scoop\apps\ffmpeg\current\bin
```

### Permission Denied Errors

If users encounter permission errors:
1. Ensure Developer Mode is enabled (for symlinks)
2. Check antivirus isn't blocking the application
3. Verify folder permissions on the installation directory

### Antivirus Interference

Some antivirus software may flag or slow down ML model downloads. Consider adding exclusions for:
- The repository directory
- The conda environments directory (`%USERPROFILE%\miniconda3\envs`)
- The models directory

## Support

For issues specific to this pipeline, see:
- Repository: https://github.com/kleer001/comfyui_ingest
- Issues: https://github.com/kleer001/comfyui_ingest/issues

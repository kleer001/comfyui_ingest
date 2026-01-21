# Windows Troubleshooting Guide

This guide covers common issues when running the VFX Pipeline on Windows and how to resolve them.

## Key Information

**Tools are auto-installed:** FFmpeg and COLMAP are automatically downloaded and installed to `.vfx_pipeline/tools/` when the wizard runs. No manual installation required.

**Everything is sandboxed:** All tools, models, and environments are installed within the repository directory. Delete the repo folder to completely remove everything.

## Quick Diagnostics

Run this in PowerShell to check your environment:

```powershell
# Check if conda is available
Get-Command conda -ErrorAction SilentlyContinue

# Check PowerShell execution policy
Get-ExecutionPolicy

# Check long paths enabled
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -ErrorAction SilentlyContinue

# Check auto-installed tools
ls .vfx_pipeline\tools\ -ErrorAction SilentlyContinue
```

---

## User Errors

These are common mistakes that users can fix themselves.

### Running from the Wrong Terminal

**Symptom:** The install wizard or scripts behave unexpectedly, or console input doesn't work.

**Cause:** Running Python scripts from Git Bash instead of PowerShell or CMD.

**Solution:** Always use **PowerShell** or **CMD** for this pipeline, not Git Bash.

```powershell
# Correct - use PowerShell
powershell
cd shot-gopher
python scripts/install_wizard.py
```

Git Bash uses a compatibility layer that doesn't support all Windows Python features (like `msvcrt` for console input).

### Using the Wrong Activation Script

**Symptom:** Activation script doesn't work or shows syntax errors.

**Cause:** Using `.bat` script in PowerShell or `.ps1` script in CMD.

**Solution:** Use the correct script for your shell:

| Shell | Activation Command |
|-------|-------------------|
| PowerShell | `. .\.vfx_pipeline\activate.ps1` |
| CMD | `.vfx_pipeline\activate.bat` |
| Git Bash | `source .vfx_pipeline/activate.sh` |

### Conda Not Initialized

**Symptom:** `conda activate` does nothing or shows "conda is not recognized".

**Cause:** Conda was installed but not initialized for PowerShell.

**Solution:**

```powershell
# Find and run conda init
& "$env:USERPROFILE\miniconda3\Scripts\conda.exe" init powershell

# Close and reopen PowerShell
# Then verify:
conda --version
```

---

## Known Limitations (Warnings)

These issues cannot be fixed by code changes. Be aware of them during installation and usage.

### Download Fallbacks Unavailable

**What:** The pipeline uses Python `requests` for downloads. Fallback methods using `wget` and `curl` are typically not available on Windows.

**Impact:** If a download fails with `requests`, there are no fallback options.

**Workaround:** If downloads fail:
1. Check your internet connection
2. Temporarily disable VPN
3. Download manually and place in the correct directory
4. Install curl via `winget install curl` for fallback support

### Antivirus May Interfere with Downloads

**What:** Windows Defender and other antivirus software actively scan downloaded files. Large ML model downloads (3GB+) may be flagged, slowed, or quarantined.

**Symptoms:**
- Downloads take much longer than expected
- Downloads fail near completion
- Model files disappear after download

**Workaround:** Ask IT to add an exclusion for the repository directory only:
- `C:\path\to\shot-gopher`

Since everything is sandboxed within the repo (tools, models, environments), only one exclusion is needed.

### COLMAP May Fail in Remote Desktop Sessions

**What:** COLMAP GPU mode requires an OpenGL context. When connected via Remote Desktop (RDP), Windows may not provide a proper GPU context.

**Symptoms:**
- COLMAP GPU extraction fails
- "Failed to create OpenGL context" errors
- Features extracted = 0

**Workaround:**
1. Run COLMAP from a local session (physically at the machine)
2. Use CPU mode: `python scripts/run_colmap.py --quality slow` (much slower)
3. Use a remote desktop solution that supports GPU passthrough (like Parsec)

### Case-Insensitive Filesystem Collisions

**What:** Windows treats `WHAM` and `wham` as the same directory. If you clone repositories with different casing, they may overwrite each other.

**Symptoms:**
- Git clone fails with "directory already exists"
- Files from one project appear in another

**Workaround:**
- Ensure consistent casing when cloning
- Delete existing directories before re-cloning
- Consider enabling case sensitivity per-folder (requires admin):
  ```powershell
  fsutil file setCaseSensitiveInfo C:\path\to\folder enable
  ```

### File Locking During Updates

**What:** Windows locks files that are in use. If a Python process or model viewer has a file open, it cannot be overwritten.

**Symptoms:**
- "Access denied" when downloading models
- Updates fail with permission errors

**Workaround:**
1. Close all Python processes: `taskkill /F /IM python.exe`
2. Close any model viewers or applications using the files
3. Retry the operation

The installer includes automatic retry logic for file locking, but persistent locks require manual intervention.

---

## Error Reference

### "cannot be loaded because running scripts is disabled"

**Full error:** `File ... cannot be loaded because running scripts is disabled on this system.`

**Fix:** Ask IT to set PowerShell execution policy (see IT guide), or run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "The system cannot find the path specified" (long paths)

**Cause:** Path exceeds 260 characters and long paths are not enabled.

**Fix:** Ask IT to enable long paths (see IT guide).

### "CUDA out of memory"

**Cause:** GPU VRAM is insufficient for the model being run.

**Fix:**
1. Close other GPU applications
2. Use a smaller model variant
3. Reduce batch size in configuration

### "No module named 'torch'" (after activation)

**Cause:** Conda environment not properly activated.

**Fix:**
```powershell
# Verify you're in the right environment
conda info --envs
conda activate vfx-pipeline

# If it still fails, reinstall
conda deactivate
conda env remove -n vfx-pipeline
python scripts/install_wizard.py
```

---

## Getting Help

If you encounter issues not covered here:

1. Check the [GitHub Issues](https://github.com/kleer001/shot-gopher/issues) for similar problems
2. Run diagnostics and include output in your report:
   ```powershell
   python -c "import sys; print(sys.platform, sys.version)"
   conda info
   nvidia-smi
   ```
3. Include the full error message and steps to reproduce

# OS Support Analysis - Installation Wizards

## Current State

### install_wizard.py (Conda-Based)
**Strengths:**
- Works on any OS where conda is available (Linux, macOS, Windows)
- Platform-agnostic conda environment management
- Robust package installation with conda/pip fallbacks

**Gaps:**
- No explicit OS detection
- No OS-specific installation instructions for missing deps
- No guidance on which wizard to use
- Missing platform-specific commands (apt vs brew vs choco)

**Current OS Coverage:**
- ✅ Linux native: Full support (assumes apt for system packages)
- ✅ macOS: Mostly works (but no Homebrew instructions for missing deps)
- ✅ WSL2: Works (conda-based, no Docker needed)
- ⚠️ Windows native: Works if conda installed (but no Windows-specific guidance)

### install_wizard_docker.py (Docker-Based)
**Strengths:**
- Explicit platform detection (Linux/WSL2/macOS/Windows)
- Detailed Docker installation instructions per platform
- NVIDIA Container Toolkit auto-installation
- Clear rejection of unsupported platforms (macOS) with helpful alternative

**Gaps:**
- Windows native Docker Desktop support could be more detailed
- No cross-reference to conda wizard for non-Docker scenarios

**Current OS Coverage:**
- ✅ Linux native: Full support with auto-installation
- ✅ WSL2: Full support with specific instructions
- ✅ macOS: Correctly rejected, suggests conda wizard
- ⚠️ Windows native: Detected but minimal guidance

---

## Recommended Enhancements

### 1. Cross-Wizard Decision Helper
Create `scripts/which_wizard.py` to help users choose:

```
Which installation method should I use?

Platform detected: Linux (native)
GPU: NVIDIA RTX 3090 (24GB VRAM)

You have TWO options:

1. Docker-based (Recommended for Linux/WSL2)
   ✓ Isolated environment
   ✓ Consistent across systems
   ✓ Easier to troubleshoot
   → Run: python scripts/install_wizard_docker.py

2. Conda-based (Works everywhere)
   ✓ Works on macOS, Linux, WSL2, Windows
   ✓ More flexible for development
   ✓ Direct access to files
   → Run: python scripts/install_wizard.py
```

### 2. install_wizard.py Enhancements

#### Add Platform Detection Module
```python
class PlatformManager:
    """Cross-platform detection and instructions."""

    @staticmethod
    def detect_platform() -> Tuple[str, str]:
        """Returns (os_name, package_manager)"""
        # Linux: ('linux', 'apt' | 'yum' | 'pacman')
        # macOS: ('macos', 'brew')
        # Windows: ('windows', 'choco')
        # WSL2: ('wsl2', 'apt')

    def get_install_instructions(self, package: str) -> Dict[str, str]:
        """Get OS-specific install instructions."""
        return {
            'linux_apt': f'sudo apt install {package}',
            'linux_yum': f'sudo yum install {package}',
            'macos': f'brew install {package}',
            'windows': f'choco install {package}',
        }
```

#### Missing Dependency Guidance
When ffmpeg/colmap/git is missing:

**Linux:**
```bash
sudo apt install ffmpeg colmap git
# or
sudo yum install ffmpeg colmap git
```

**macOS:**
```bash
# Install Homebrew first (if not installed):
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install ffmpeg colmap git
```

**Windows (via Chocolatey):**
```powershell
# Install Chocolatey first (if not installed):
# Run as Administrator in PowerShell
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

choco install ffmpeg git
# Note: COLMAP not available via choco, use conda or compile from source
```

**WSL2:**
```bash
# Same as Linux
sudo apt install ffmpeg colmap git
```

### 3. install_wizard_docker.py Enhancements

#### Windows Native Docker Desktop Support
Add detailed instructions:

```python
elif platform_name == "windows" and environment == "native":
    return """
Install Docker Desktop for Windows:

1. Download: https://www.docker.com/products/docker-desktop
2. Install Docker Desktop
3. During installation:
   - Enable "Use WSL 2 instead of Hyper-V" (recommended)
   - OR use Hyper-V (requires Windows Pro/Enterprise)
4. Restart computer when prompted
5. Open Docker Desktop and complete setup
6. Verify: docker --version

For GPU support on Windows:
- NVIDIA Container Toolkit is not supported on Windows native Docker
- Use WSL2 backend for GPU access (recommended)
- Install Ubuntu in WSL2, then run Docker there

Recommended: Use WSL2 + Docker for GPU workloads
"""
```

### 4. Unified Installation Instructions

#### Platform-Specific Quick Start Guides

**Linux Native Users:**
- **Recommended:** Docker wizard (isolated, easier)
- **Alternative:** Conda wizard (more flexible)

**macOS Users:**
- **Only option:** Conda wizard (Docker can't access GPU)
- Install dependencies via Homebrew

**WSL2 Users:**
- **Recommended:** Docker wizard (native GPU support)
- **Alternative:** Conda wizard (works but requires more setup)

**Windows Native Users:**
- **Recommended:** Install WSL2, use Docker wizard
- **Alternative:** Docker Desktop (no GPU support) or conda

---

## Implementation Priority

### High Priority (Do Now)
1. ✅ Add OS detection to install_wizard.py
2. ✅ Add OS-specific instructions for missing dependencies
3. ✅ Add cross-wizard recommendations in both wizards
4. ✅ Improve Windows native support in docker wizard

### Medium Priority
5. Create `scripts/which_wizard.py` decision helper
6. Add macOS-specific guidance (Homebrew, Metal vs CUDA)
7. Add Windows-specific conda instructions

### Low Priority (Nice to Have)
8. Auto-detect package manager on Linux (apt vs yum vs pacman)
9. Check for Homebrew on macOS and offer to install
10. Check for Chocolatey on Windows and offer to install

---

## Testing Matrix

| OS | Environment | install_wizard.py | install_wizard_docker.py |
|---|---|---|---|
| Linux | Native | ✅ Fully supported | ✅ Fully supported |
| macOS | Native | ✅ Conda only | ❌ Rejected (correct) |
| Windows | WSL2 Ubuntu | ✅ Works | ✅ Fully supported |
| Windows | Native + conda | ⚠️ Works (needs better docs) | ⚠️ Limited (no GPU) |
| Windows | Native + Docker Desktop | ❌ Not tested | ⚠️ Works (no GPU) |

---

## Summary

**Current state:** Both wizards work but lack comprehensive OS-specific guidance and cross-references.

**After enhancements:**
- Users will know which wizard to use for their platform
- Missing dependencies will have clear OS-specific installation instructions
- Both wizards will guide users to the best option for their setup
- All major platforms (Linux, macOS, WSL2, Windows) will be properly supported

**Key principle:** Docker wizard for GPU workloads on Linux/WSL2, Conda wizard for everything else (especially macOS).

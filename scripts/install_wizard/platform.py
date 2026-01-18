"""Platform detection and OS-specific instructions.

Provides platform detection and OS-specific installation instructions
for system dependencies across Linux, macOS, Windows, and WSL2.
"""

import platform
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple


class PlatformManager:
    """Handles platform detection and OS-specific instructions."""

    @staticmethod
    def detect_platform() -> Tuple[str, str, str]:
        """Detect operating system and package manager.

        Returns:
            Tuple of (os_name, environment, package_manager) where:
            - os_name: 'linux', 'macos', 'windows'
            - environment: 'native', 'wsl2'
            - package_manager: 'apt', 'yum', 'brew', 'choco', 'unknown'
        """
        system = platform.system().lower()

        if system == "linux":
            try:
                with open("/proc/version", "r") as f:
                    version_info = f.read().lower()
                    if "microsoft" in version_info or "wsl" in version_info:
                        return "linux", "wsl2", PlatformManager._detect_linux_package_manager()
            except FileNotFoundError:
                pass
            return "linux", "native", PlatformManager._detect_linux_package_manager()

        elif system == "darwin":
            has_brew = subprocess.run(
                ["which", "brew"],
                capture_output=True
            ).returncode == 0
            return "macos", "native", "brew" if has_brew else "unknown"

        elif system == "windows":
            has_choco = subprocess.run(
                ["choco", "--version"],
                capture_output=True,
                shell=True
            ).returncode == 0
            return "windows", "native", "choco" if has_choco else "unknown"

        return system, "unknown", "unknown"

    @staticmethod
    def _detect_linux_package_manager() -> str:
        """Detect Linux package manager."""
        managers = [
            ("apt", ["apt", "--version"]),
            ("apt-get", ["apt-get", "--version"]),
            ("yum", ["yum", "--version"]),
            ("dnf", ["dnf", "--version"]),
            ("pacman", ["pacman", "--version"]),
            ("zypper", ["zypper", "--version"]),
        ]

        for name, cmd in managers:
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=2)
                if result.returncode == 0:
                    if name == "apt-get":
                        return "apt"
                    return name
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        return "unknown"

    @staticmethod
    def get_system_package_install_cmd(
        package: str,
        os_name: str,
        pkg_manager: str
    ) -> Optional[str]:
        """Get command to install a system package.

        Args:
            package: Package name (may differ per OS)
            os_name: Operating system ('linux', 'macos', 'windows')
            pkg_manager: Package manager ('apt', 'yum', 'brew', etc.)

        Returns:
            Installation command string or None if not available
        """
        commands = {
            ("linux", "apt"): f"sudo apt update && sudo apt install -y {package}",
            ("linux", "yum"): f"sudo yum install -y {package}",
            ("linux", "dnf"): f"sudo dnf install -y {package}",
            ("linux", "pacman"): f"sudo pacman -S {package}",
            ("linux", "zypper"): f"sudo zypper install {package}",
            ("macos", "brew"): f"brew install {package}",
            ("windows", "choco"): f"choco install {package} -y",
        }

        return commands.get((os_name, pkg_manager))

    @staticmethod
    def get_missing_dependency_instructions(
        dependency: str,
        os_name: str,
        environment: str,
        pkg_manager: str
    ) -> str:
        """Get detailed installation instructions for missing dependency.

        Args:
            dependency: Name of missing dependency (ffmpeg, git, colmap, etc.)
            os_name: Operating system
            environment: Environment (native, wsl2)
            pkg_manager: Package manager

        Returns:
            Multi-line installation instructions
        """
        pkg_map = {
            "ffmpeg": {
                "apt": "ffmpeg",
                "yum": "ffmpeg",
                "dnf": "ffmpeg",
                "brew": "ffmpeg",
                "choco": "ffmpeg",
            },
            "git": {
                "apt": "git",
                "yum": "git",
                "dnf": "git",
                "brew": "git",
                "choco": "git",
            },
            "colmap": {
                "apt": "colmap",
                "yum": "colmap",  # May need EPEL
                "dnf": "colmap",
                "brew": "colmap",
                "choco": None,  # Not available
            },
        }

        package_name = pkg_map.get(dependency, {}).get(pkg_manager)

        if os_name == "linux":
            if pkg_manager == "apt":
                if package_name:
                    return f"""
Install {dependency} on Ubuntu/Debian:

    sudo apt update
    sudo apt install -y {package_name}
"""
                else:
                    return f"{dependency} not available via apt. Please install from source."

            elif pkg_manager in ("yum", "dnf"):
                if package_name:
                    return f"""
Install {dependency} on RHEL/CentOS/Fedora:

    sudo {pkg_manager} install -y {package_name}

Note: May require EPEL repository:
    sudo {pkg_manager} install -y epel-release
"""
                else:
                    return f"{dependency} not available via {pkg_manager}. Install from source."

            elif pkg_manager == "pacman":
                return f"""
Install {dependency} on Arch Linux:

    sudo pacman -S {package_name or dependency}
"""
            else:
                return f"""
{dependency} package manager not detected. Install manually:
    - Ubuntu/Debian: sudo apt install {dependency}
    - RHEL/CentOS: sudo yum install {dependency}
    - Arch: sudo pacman -S {dependency}
"""

        elif os_name == "macos":
            if pkg_manager == "brew":
                if package_name:
                    return f"""
Install {dependency} on macOS:

    brew install {package_name}
"""
                else:
                    return f"""
{dependency} is not available via Homebrew.
Please check the official {dependency} website for macOS installation.
"""
            else:
                return f"""
Homebrew not found. Install Homebrew first:

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

Then install {dependency}:

    brew install {package_name or dependency}
"""

        elif os_name == "windows":
            if environment == "wsl2":
                return f"""
You are in WSL2. Use Linux package manager:

    sudo apt update
    sudo apt install -y {pkg_map.get(dependency, {}).get('apt', dependency)}
"""
            else:
                if pkg_manager == "choco" and package_name:
                    return f"""
Install {dependency} on Windows via Chocolatey:

    choco install {package_name} -y
"""
                else:
                    if dependency == "colmap":
                        return """
COLMAP is not available via Chocolatey on Windows.

Options:
1. Use WSL2 (recommended for GPU workloads):
   - Install Ubuntu in WSL2
   - sudo apt install colmap

2. Use conda:
   - conda install -c conda-forge colmap

3. Build from source (advanced):
   - https://colmap.github.io/install.html
"""
                    else:
                        return f"""
Install Chocolatey first (run PowerShell as Administrator):

    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

Then install {dependency}:

    choco install {dependency} -y
"""

        return f"Installation instructions not available for {dependency} on {os_name}"

    @staticmethod
    def get_wizard_recommendation(
        os_name: str,
        environment: str,
        has_gpu: bool
    ) -> str:
        """Get recommendation for which wizard to use.

        Args:
            os_name: Operating system
            environment: Environment (native, wsl2)
            has_gpu: Whether NVIDIA GPU is available

        Returns:
            Recommendation text
        """
        if os_name == "macos":
            return """
🍎 macOS Detected

Recommendation: Use conda-based installation wizard

Why?
  • Docker on macOS cannot access NVIDIA GPUs (runs in VM)
  • Conda-based installation works natively on macOS
  • All features available except GPU-accelerated processing

Run: python scripts/install_wizard.py
"""

        elif os_name == "linux" and environment == "native" and has_gpu:
            return """
🐧 Linux + GPU Detected

You have TWO options:

1. Docker-based (Recommended for production)
   ✓ Isolated, containerized environment
   ✓ Consistent across systems
   ✓ Easier troubleshooting and deployment
   ✗ Slight overhead from containerization
   → Run: python scripts/install_wizard_docker.py

2. Conda-based (Recommended for development)
   ✓ Direct filesystem access
   ✓ More flexible for development/debugging
   ✓ Lower overhead
   ✗ More dependencies to manage manually
   → Run: python scripts/install_wizard.py

Both work great on Linux! Choose based on your workflow.
"""

        elif os_name == "linux" and environment == "wsl2" and has_gpu:
            return """
🪟 WSL2 + GPU Detected

Recommendation: Docker-based installation

Why?
  • Excellent GPU support in WSL2 via NVIDIA Container Toolkit
  • Cleaner separation between Windows and Linux environments
  • Easier to manage and troubleshoot

Alternative: Conda-based works too if you prefer direct access

Docker: python scripts/install_wizard_docker.py
Conda: python scripts/install_wizard.py
"""

        elif not has_gpu:
            return """
⚠️  No NVIDIA GPU Detected

Recommendation: Conda-based installation

Why?
  • Motion capture requires NVIDIA GPU (12GB+ VRAM)
  • Without GPU, only segmentation/roto workflows are available
  • Conda-based is simpler for CPU-only usage

Run: python scripts/install_wizard.py

Note: If you add a GPU later, you can switch to Docker wizard
"""

        else:
            return """
Choose installation method:
  • Docker: python scripts/install_wizard_docker.py
  • Conda: python scripts/install_wizard.py
"""

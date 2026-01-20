"""Platform detection and OS-specific instructions.

Provides platform detection and OS-specific installation instructions
for system dependencies across Linux, macOS, Windows, and WSL2.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def _is_windows() -> bool:
    """Check if running on Windows."""
    return sys.platform == "win32"


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
            has_brew = shutil.which("brew") is not None
            return "macos", "native", "brew" if has_brew else "unknown"

        elif system == "windows":
            pkg_manager = PlatformManager._detect_windows_package_manager()
            return "windows", "native", pkg_manager

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
    def _detect_windows_package_manager() -> str:
        """Detect Windows package manager in priority order."""
        if shutil.which("winget"):
            return "winget"
        if shutil.which("choco"):
            return "choco"
        if shutil.which("scoop"):
            return "scoop"
        return "unknown"

    @staticmethod
    def find_tool(tool_name: str) -> Optional[Path]:
        """Find a tool executable with cross-platform path search.

        Searches PATH first, then platform-specific common locations.

        Args:
            tool_name: Name of the tool (e.g., 'colmap', 'ffmpeg', '7z')

        Returns:
            Path to the executable if found, None otherwise.
        """
        path_result = shutil.which(tool_name)
        if path_result:
            return Path(path_result)

        home = Path.home()

        if _is_windows():
            search_paths = PlatformManager._get_windows_tool_paths(tool_name, home)
        else:
            search_paths = PlatformManager._get_unix_tool_paths(tool_name, home)

        for path in search_paths:
            if path.exists():
                return path

        return None

    @staticmethod
    def _get_windows_tool_paths(tool_name: str, home: Path) -> List[Path]:
        """Get Windows-specific search paths for a tool."""
        localappdata = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        programfiles = Path(os.environ.get("PROGRAMFILES", "C:/Program Files"))
        programfiles_x86 = Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"))
        programdata = Path(os.environ.get("PROGRAMDATA", "C:/ProgramData"))

        tool_paths: Dict[str, List[Path]] = {
            "colmap": [
                programfiles / "COLMAP" / "COLMAP.bat",
                programfiles_x86 / "COLMAP" / "COLMAP.bat",
                Path("C:/COLMAP/COLMAP.bat"),
                localappdata / "COLMAP" / "COLMAP.bat",
                home / "COLMAP" / "COLMAP.bat",
                programdata / "chocolatey" / "bin" / "colmap.exe",
                home / "scoop" / "apps" / "colmap" / "current" / "COLMAP.bat",
            ],
            "ffmpeg": [
                programfiles / "FFmpeg" / "bin" / "ffmpeg.exe",
                programfiles_x86 / "FFmpeg" / "bin" / "ffmpeg.exe",
                Path("C:/ffmpeg/bin/ffmpeg.exe"),
                home / "ffmpeg" / "bin" / "ffmpeg.exe",
                programdata / "chocolatey" / "bin" / "ffmpeg.exe",
                home / "scoop" / "apps" / "ffmpeg" / "current" / "bin" / "ffmpeg.exe",
            ],
            "ffprobe": [
                programfiles / "FFmpeg" / "bin" / "ffprobe.exe",
                programfiles_x86 / "FFmpeg" / "bin" / "ffprobe.exe",
                Path("C:/ffmpeg/bin/ffprobe.exe"),
                home / "ffmpeg" / "bin" / "ffprobe.exe",
                programdata / "chocolatey" / "bin" / "ffprobe.exe",
                home / "scoop" / "apps" / "ffmpeg" / "current" / "bin" / "ffprobe.exe",
            ],
            "7z": [
                programfiles / "7-Zip" / "7z.exe",
                programfiles_x86 / "7-Zip" / "7z.exe",
                programdata / "chocolatey" / "bin" / "7z.exe",
                home / "scoop" / "apps" / "7zip" / "current" / "7z.exe",
            ],
            "nvidia-smi": [
                programfiles / "NVIDIA Corporation" / "NVSMI" / "nvidia-smi.exe",
                Path("C:/Windows/System32/nvidia-smi.exe"),
            ],
            "nvcc": [
                programfiles / "NVIDIA GPU Computing Toolkit" / "CUDA" / "v12.1" / "bin" / "nvcc.exe",
                programfiles / "NVIDIA GPU Computing Toolkit" / "CUDA" / "v12.0" / "bin" / "nvcc.exe",
                programfiles / "NVIDIA GPU Computing Toolkit" / "CUDA" / "v11.8" / "bin" / "nvcc.exe",
                programfiles / "NVIDIA GPU Computing Toolkit" / "CUDA" / "v11.7" / "bin" / "nvcc.exe",
                Path("C:/CUDA/bin/nvcc.exe"),
            ],
            "aria2c": [
                programdata / "chocolatey" / "bin" / "aria2c.exe",
                home / "scoop" / "apps" / "aria2" / "current" / "aria2c.exe",
            ],
        }

        return tool_paths.get(tool_name, [])

    @staticmethod
    def _get_unix_tool_paths(tool_name: str, home: Path) -> List[Path]:
        """Get Unix-specific search paths for a tool."""
        tool_paths: Dict[str, List[Path]] = {
            "colmap": [
                Path("/usr/local/bin/colmap"),
                Path("/usr/bin/colmap"),
                home / ".local" / "bin" / "colmap",
            ],
            "ffmpeg": [
                Path("/usr/local/bin/ffmpeg"),
                Path("/usr/bin/ffmpeg"),
            ],
            "ffprobe": [
                Path("/usr/local/bin/ffprobe"),
                Path("/usr/bin/ffprobe"),
            ],
            "7z": [
                Path("/usr/bin/7z"),
                Path("/usr/bin/7za"),
                Path("/usr/bin/7zr"),
            ],
            "aria2c": [
                Path("/usr/bin/aria2c"),
                Path("/usr/local/bin/aria2c"),
            ],
        }

        return tool_paths.get(tool_name, [])

    @staticmethod
    def run_tool(
        tool_path: Path,
        args: List[str],
        **subprocess_kwargs
    ) -> subprocess.CompletedProcess:
        """Run an external tool with proper handling for Windows .bat files.

        On Windows, .bat files need shell=True or explicit cmd /c invocation.

        Args:
            tool_path: Path to the tool executable
            args: Arguments to pass to the tool
            **subprocess_kwargs: Additional args for subprocess.run

        Returns:
            CompletedProcess result
        """
        cmd = [str(tool_path)] + args

        if _is_windows() and str(tool_path).lower().endswith('.bat'):
            subprocess_kwargs['shell'] = True

        return subprocess.run(cmd, **subprocess_kwargs)

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
            ("windows", "winget"): f"winget install {package}",
            ("windows", "choco"): f"choco install {package} -y",
            ("windows", "scoop"): f"scoop install {package}",
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

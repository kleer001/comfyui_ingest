#!/usr/bin/env python3
"""Interactive installation wizard for the VFX pipeline.

Guides users through installing all dependencies for:
- Core pipeline (ComfyUI workflows, COLMAP, etc.)
- Dynamic scene segmentation (SAM3)
- Human motion capture (WHAM, TAVA, ECON)

Usage:
    python scripts/install_wizard.py
    python scripts/install_wizard.py --component mocap
    python scripts/install_wizard.py --check-only
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Colors:
    """Terminal colors for pretty output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print section header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def ask_yes_no(question: str, default: bool = True) -> bool:
    """Ask user yes/no question."""
    default_str = "Y/n" if default else "y/N"
    while True:
        response = input(f"{question} [{default_str}]: ").strip().lower()
        if not response:
            return default
        if response in ('y', 'yes'):
            return True
        if response in ('n', 'no'):
            return False
        print("Please answer yes or no.")


def run_command(cmd: List[str], check: bool = True, capture: bool = False) -> Tuple[bool, str]:
    """Run shell command and return success status and output."""
    try:
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stdout + result.stderr
        else:
            result = subprocess.run(cmd, check=check, timeout=30)
            return result.returncode == 0, ""
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False, ""


def check_python_package(package: str, import_name: Optional[str] = None) -> bool:
    """Check if Python package is installed."""
    import_name = import_name or package
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False


def check_command_available(command: str) -> bool:
    """Check if command-line tool is available."""
    success, _ = run_command(["which", command], check=False, capture=True)
    return success


def check_gpu_available() -> Tuple[bool, str]:
    """Check if NVIDIA GPU is available."""
    success, output = run_command(["nvidia-smi"], check=False, capture=True)
    if not success:
        return False, "No NVIDIA GPU detected (nvidia-smi failed)"

    # Parse VRAM
    try:
        import re
        vram_match = re.search(r'(\d+)MiB\s*/\s*(\d+)MiB', output)
        if vram_match:
            total_vram = int(vram_match.group(2))
            return True, f"{total_vram}MB total VRAM"
    except:
        pass

    return True, "GPU detected"


def get_disk_space(path: Path = Path.home()) -> Tuple[float, float]:
    """Get available and total disk space in GB.

    Args:
        path: Path to check (default: home directory)

    Returns:
        Tuple of (available_gb, total_gb)
    """
    import shutil
    try:
        stat = shutil.disk_usage(path)
        available_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        return available_gb, total_gb
    except:
        return 0.0, 0.0


def format_size_gb(size_gb: float) -> str:
    """Format size in GB to human-readable string."""
    if size_gb < 1:
        return f"{size_gb * 1024:.0f} MB"
    elif size_gb < 10:
        return f"{size_gb:.1f} GB"
    else:
        return f"{size_gb:.0f} GB"


class ComponentInstaller:
    """Base class for component installers."""

    def __init__(self, name: str, size_gb: float = 0.0):
        self.name = name
        self.installed = False
        self.size_gb = size_gb  # Estimated disk space in GB

    def check(self) -> bool:
        """Check if component is installed."""
        raise NotImplementedError

    def install(self) -> bool:
        """Install component."""
        raise NotImplementedError

    def validate(self) -> bool:
        """Validate installation."""
        return self.check()


class PythonPackageInstaller(ComponentInstaller):
    """Installer for Python packages via pip."""

    def __init__(self, name: str, package: str, import_name: Optional[str] = None, size_gb: float = 0.0):
        super().__init__(name, size_gb)
        self.package = package
        self.import_name = import_name or package

    def check(self) -> bool:
        self.installed = check_python_package(self.package, self.import_name)
        return self.installed

    def install(self) -> bool:
        print(f"\nInstalling {self.name}...")
        success, _ = run_command([sys.executable, "-m", "pip", "install", self.package])
        if success:
            print_success(f"{self.name} installed")
            self.installed = True
        else:
            print_error(f"Failed to install {self.name}")
        return success


class GitRepoInstaller(ComponentInstaller):
    """Installer for Git repositories."""

    def __init__(self, name: str, repo_url: str, install_dir: Optional[Path] = None, size_gb: float = 0.0):
        super().__init__(name, size_gb)
        self.repo_url = repo_url
        self.install_dir = install_dir or Path.home() / ".vfx_pipeline" / name.lower()

    def check(self) -> bool:
        self.installed = self.install_dir.exists() and (self.install_dir / ".git").exists()
        return self.installed

    def install(self) -> bool:
        print(f"\nInstalling {self.name} from {self.repo_url}...")

        # Create parent directory
        self.install_dir.parent.mkdir(parents=True, exist_ok=True)

        # Clone repository
        success, _ = run_command(["git", "clone", self.repo_url, str(self.install_dir)])
        if not success:
            print_error(f"Failed to clone {self.name}")
            return False

        # Run pip install if setup.py exists
        setup_py = self.install_dir / "setup.py"
        if setup_py.exists():
            print(f"  Installing {self.name} package...")
            success, _ = run_command(
                [sys.executable, "-m", "pip", "install", "-e", str(self.install_dir)]
            )
            if not success:
                print_warning(f"pip install failed for {self.name}")

        self.installed = True
        print_success(f"{self.name} cloned to {self.install_dir}")
        return True


class InstallationWizard:
    """Main installation wizard."""

    def __init__(self):
        self.components = {}
        self.setup_components()

    def setup_components(self):
        """Define all installable components."""

        # Core dependencies
        self.components['core'] = {
            'name': 'Core Pipeline',
            'required': True,
            'installers': [
                PythonPackageInstaller('NumPy', 'numpy', size_gb=0.1),
                PythonPackageInstaller('OpenCV', 'opencv-python', 'cv2', size_gb=0.3),
                PythonPackageInstaller('Pillow', 'pillow', 'PIL', size_gb=0.05),
            ]
        }

        # PyTorch (special handling for CUDA)
        self.components['pytorch'] = {
            'name': 'PyTorch',
            'required': True,
            'installers': [
                PythonPackageInstaller('PyTorch', 'torch', size_gb=6.0),  # With CUDA
            ]
        }

        # COLMAP
        self.components['colmap'] = {
            'name': 'COLMAP',
            'required': False,
            'installers': [],  # System install, check only
            'size_gb': 0.5,  # If installed via conda
        }

        # Motion capture dependencies
        self.components['mocap_core'] = {
            'name': 'Motion Capture Core',
            'required': False,
            'installers': [
                PythonPackageInstaller('SMPL-X', 'smplx', size_gb=0.1),
                PythonPackageInstaller('Trimesh', 'trimesh', size_gb=0.05),
            ]
        }

        # WHAM (code ~0.1GB + checkpoints ~2.5GB)
        self.components['wham'] = {
            'name': 'WHAM',
            'required': False,
            'installers': [
                GitRepoInstaller(
                    'WHAM',
                    'https://github.com/yohanshin/WHAM.git',
                    Path.home() / ".vfx_pipeline" / "WHAM",
                    size_gb=3.0  # Code + checkpoints
                )
            ]
        }

        # TAVA (code ~0.05GB + checkpoints ~1.5GB)
        self.components['tava'] = {
            'name': 'TAVA',
            'required': False,
            'installers': [
                GitRepoInstaller(
                    'TAVA',
                    'https://github.com/facebookresearch/tava.git',
                    Path.home() / ".vfx_pipeline" / "tava",
                    size_gb=2.0  # Code + checkpoints
                )
            ]
        }

        # ECON (code ~0.2GB + dependencies ~1GB + checkpoints ~4GB + SMPL-X models ~0.5GB)
        self.components['econ'] = {
            'name': 'ECON',
            'required': False,
            'installers': [
                GitRepoInstaller(
                    'ECON',
                    'https://github.com/YuliangXiu/ECON.git',
                    Path.home() / ".vfx_pipeline" / "ECON",
                    size_gb=6.0  # Code + dependencies + checkpoints + models
                )
            ]
        }

    def check_system_requirements(self):
        """Check system requirements."""
        print_header("System Requirements Check")

        # Python version
        py_version = sys.version_info
        if py_version >= (3, 8):
            print_success(f"Python {py_version.major}.{py_version.minor}.{py_version.micro}")
        else:
            print_error(f"Python {py_version.major}.{py_version.minor} (3.8+ required)")
            return False

        # Git
        if check_command_available("git"):
            print_success("Git available")
        else:
            print_error("Git not found (required for cloning repositories)")
            return False

        # Disk space
        available_gb, total_gb = get_disk_space()
        if available_gb > 0:
            used_pct = ((total_gb - available_gb) / total_gb) * 100
            if available_gb >= 50:
                print_success(f"Disk space: {format_size_gb(available_gb)} available ({used_pct:.0f}% used)")
            elif available_gb >= 20:
                print_warning(f"Disk space: {format_size_gb(available_gb)} available ({used_pct:.0f}% used)")
                print_info("Full installation requires ~40 GB")
            else:
                print_error(f"Disk space: {format_size_gb(available_gb)} available ({used_pct:.0f}% used)")
                print_info("Insufficient space - full installation requires ~40 GB")
                return False
        else:
            print_warning("Could not check disk space")

        # GPU
        has_gpu, gpu_info = check_gpu_available()
        if has_gpu:
            print_success(f"GPU: {gpu_info}")
        else:
            print_warning(f"No GPU detected - CPU-only mode (slower)")
            print_info("Motion capture requires NVIDIA GPU with 12GB+ VRAM")

        # ffmpeg
        if check_command_available("ffmpeg"):
            print_success("ffmpeg available")
        else:
            print_warning("ffmpeg not found (required for video ingestion)")
            print_info("Install: sudo apt install ffmpeg")

        # COLMAP
        if check_command_available("colmap"):
            print_success("COLMAP available")
        else:
            print_warning("COLMAP not found (optional, for 3D reconstruction)")
            print_info("Install: sudo apt install colmap")

        return True

    def check_all_components(self) -> Dict[str, bool]:
        """Check status of all components."""
        status = {}

        for comp_id, comp_info in self.components.items():
            all_installed = all(installer.check() for installer in comp_info['installers'])
            status[comp_id] = all_installed

        return status

    def print_status(self, status: Dict[str, bool]):
        """Print installation status."""
        print_header("Installation Status")

        for comp_id, comp_info in self.components.items():
            is_installed = status.get(comp_id, False)
            required = " (required)" if comp_info['required'] else ""

            if is_installed:
                print_success(f"{comp_info['name']}{required}")
            else:
                if comp_info['required']:
                    print_error(f"{comp_info['name']}{required}")
                else:
                    print_warning(f"{comp_info['name']} - not installed")

    def calculate_space_needed(self, component_ids: List[str]) -> float:
        """Calculate total disk space needed for components.

        Args:
            component_ids: List of component IDs to install

        Returns:
            Total disk space needed in GB
        """
        total_gb = 0.0
        for comp_id in component_ids:
            comp_info = self.components.get(comp_id, {})
            for installer in comp_info.get('installers', []):
                total_gb += installer.size_gb
            # Add component-level size (for things like COLMAP)
            total_gb += comp_info.get('size_gb', 0.0)
        return total_gb

    def show_space_estimate(self, component_ids: List[str]):
        """Show disk space estimate for installation.

        Args:
            component_ids: List of component IDs to install
        """
        print_header("Disk Space Estimate")

        # Calculate per-component
        breakdown = []
        total_gb = 0.0

        for comp_id in component_ids:
            comp_info = self.components.get(comp_id, {})
            comp_size = sum(inst.size_gb for inst in comp_info.get('installers', []))
            comp_size += comp_info.get('size_gb', 0.0)

            if comp_size > 0:
                breakdown.append((comp_info['name'], comp_size))
                total_gb += comp_size

        # Sort by size (largest first)
        breakdown.sort(key=lambda x: x[1], reverse=True)

        # Print breakdown
        for name, size_gb in breakdown:
            print(f"  {name:30s} {format_size_gb(size_gb):>10s}")

        print("  " + "-" * 42)
        print(f"  {'Total':30s} {format_size_gb(total_gb):>10s}")

        # Additional space for working data
        working_space = 10.0  # ~10 GB per project
        print(f"\n  {'Working space (per project)':30s} ~{format_size_gb(working_space):>9s}")
        print(f"  {'Recommended total':30s} ~{format_size_gb(total_gb + working_space):>9s}")

        # Check available space
        available_gb, _ = get_disk_space()
        if available_gb > 0:
            print(f"\n  Available disk space: {format_size_gb(available_gb)}")

            if available_gb >= total_gb + working_space:
                print_success("Sufficient disk space available")
            elif available_gb >= total_gb:
                print_warning("Sufficient for installation, but limited working space")
            else:
                print_error(f"Insufficient disk space (need {format_size_gb(total_gb)})")
                return False

        print()
        return True

    def install_component(self, comp_id: str) -> bool:
        """Install a component."""
        comp_info = self.components[comp_id]

        print(f"\n{Colors.BOLD}Installing {comp_info['name']}...{Colors.ENDC}")

        success = True
        for installer in comp_info['installers']:
            if not installer.check():
                if not installer.install():
                    success = False
                    break
            else:
                print_success(f"{installer.name} already installed")

        return success

    def interactive_install(self, component: Optional[str] = None):
        """Interactive installation flow."""
        print_header("VFX Pipeline Installation Wizard")

        # System requirements
        if not self.check_system_requirements():
            print_error("\nSystem requirements not met. Please install missing components.")
            return False

        # Check current status
        status = self.check_all_components()
        self.print_status(status)

        # Determine what to install
        if component:
            # Specific component requested
            if component not in self.components:
                print_error(f"Unknown component: {component}")
                print_info(f"Available: {', '.join(self.components.keys())}")
                return False

            to_install = [component]
        else:
            # Interactive selection
            print("\n" + "="*60)
            print("What would you like to install?")
            print("="*60)
            print("1. Core pipeline only (COLMAP, segmentation)")
            print("2. Core + Motion capture (WHAM, TAVA, ECON)")
            print("3. Custom selection")
            print("4. Nothing (check only)")

            while True:
                choice = input("\nChoice [1-4]: ").strip()
                if choice == '1':
                    to_install = ['core', 'pytorch']
                    break
                elif choice == '2':
                    to_install = ['core', 'pytorch', 'mocap_core', 'wham', 'tava', 'econ']
                    break
                elif choice == '3':
                    to_install = []
                    for comp_id, comp_info in self.components.items():
                        if ask_yes_no(f"Install {comp_info['name']}?", default=False):
                            to_install.append(comp_id)
                    break
                elif choice == '4':
                    return True
                else:
                    print("Invalid choice")

        # Show disk space estimate
        if to_install:
            if not self.show_space_estimate(to_install):
                print_error("\nInsufficient disk space for installation")
                return False

            # Confirm installation
            if not ask_yes_no("\nProceed with installation?", default=True):
                print_info("Installation cancelled")
                return True

        # Install components
        print_header("Installing Components")

        for comp_id in to_install:
            if not status.get(comp_id, False):
                if not self.install_component(comp_id):
                    print_error(f"Failed to install {self.components[comp_id]['name']}")
                    if self.components[comp_id]['required']:
                        return False

        # Final status
        final_status = self.check_all_components()
        self.print_status(final_status)

        # Post-installation instructions
        self.print_post_install_instructions(final_status)

        return True

    def print_post_install_instructions(self, status: Dict[str, bool]):
        """Print post-installation instructions."""
        print_header("Next Steps")

        # SMPL-X models
        if status.get('mocap_core', False):
            print("\n📦 SMPL-X Body Models:")
            print("  1. Register at https://smpl-x.is.tue.mpg.de/")
            print("  2. Download SMPL-X models")
            print("  3. Place in ~/.smplx/")
            print("     mkdir -p ~/.smplx && cp SMPLX_*.pkl ~/.smplx/")

        # WHAM checkpoints
        if status.get('wham', False):
            wham_dir = Path.home() / ".vfx_pipeline" / "WHAM"
            print("\n📦 WHAM Checkpoints:")
            print("  1. Visit https://github.com/yohanshin/WHAM")
            print("  2. Download pretrained checkpoints")
            print(f"  3. Place in {wham_dir}/checkpoints/")

        # TAVA checkpoints
        if status.get('tava', False):
            tava_dir = Path.home() / ".vfx_pipeline" / "tava"
            print("\n📦 TAVA Checkpoints:")
            print("  1. Visit https://github.com/facebookresearch/tava")
            print("  2. Download pretrained models")
            print(f"  3. Place in {tava_dir}/checkpoints/")

        # ECON checkpoints
        if status.get('econ', False):
            econ_dir = Path.home() / ".vfx_pipeline" / "ECON"
            print("\n📦 ECON Checkpoints:")
            print("  1. Visit https://github.com/YuliangXiu/ECON")
            print("  2. Download pretrained models")
            print(f"  3. Place in {econ_dir}/data/")

        # ComfyUI
        print("\n🎨 ComfyUI Setup:")
        print("  1. Clone ComfyUI: git clone https://github.com/comfyanonymous/ComfyUI.git")
        print("  2. Install custom nodes:")
        print("     - ComfyUI-VideoHelperSuite")
        print("     - ComfyUI-Depth-Anything-V3")
        print("     - ComfyUI-SAM2 (for segmentation)")
        print("  3. Start server: python main.py --listen")

        # Testing
        print("\n✅ Test Installation:")
        print("  python scripts/run_pipeline.py --help")
        print("  python scripts/run_mocap.py --check")

        # Documentation
        print("\n📖 Documentation:")
        print("  README.md - Pipeline overview and usage")
        print("  TESTING.md - Testing and validation guide")
        print("  IMPLEMENTATION_NOTES.md - Developer notes")


def main():
    parser = argparse.ArgumentParser(
        description="Interactive installation wizard for VFX pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--component",
        type=str,
        choices=['core', 'pytorch', 'colmap', 'mocap_core', 'wham', 'tava', 'econ'],
        help="Install specific component"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check installation status only (don't install)"
    )

    args = parser.parse_args()

    wizard = InstallationWizard()

    if args.check_only:
        wizard.check_system_requirements()
        status = wizard.check_all_components()
        wizard.print_status(status)
        sys.exit(0)

    success = wizard.interactive_install(component=args.component)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

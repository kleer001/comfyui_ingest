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


class ComponentInstaller:
    """Base class for component installers."""

    def __init__(self, name: str):
        self.name = name
        self.installed = False

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

    def __init__(self, name: str, package: str, import_name: Optional[str] = None):
        super().__init__(name)
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

    def __init__(self, name: str, repo_url: str, install_dir: Optional[Path] = None):
        super().__init__(name)
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
                PythonPackageInstaller('NumPy', 'numpy'),
                PythonPackageInstaller('OpenCV', 'opencv-python', 'cv2'),
                PythonPackageInstaller('Pillow', 'pillow', 'PIL'),
            ]
        }

        # PyTorch (special handling for CUDA)
        self.components['pytorch'] = {
            'name': 'PyTorch',
            'required': True,
            'installers': [
                PythonPackageInstaller('PyTorch', 'torch'),
            ]
        }

        # COLMAP
        self.components['colmap'] = {
            'name': 'COLMAP',
            'required': False,
            'installers': [],  # System install, check only
        }

        # Motion capture dependencies
        self.components['mocap_core'] = {
            'name': 'Motion Capture Core',
            'required': False,
            'installers': [
                PythonPackageInstaller('SMPL-X', 'smplx'),
                PythonPackageInstaller('Trimesh', 'trimesh'),
            ]
        }

        # WHAM
        self.components['wham'] = {
            'name': 'WHAM',
            'required': False,
            'installers': [
                GitRepoInstaller(
                    'WHAM',
                    'https://github.com/yohanshin/WHAM.git',
                    Path.home() / ".vfx_pipeline" / "WHAM"
                )
            ]
        }

        # TAVA
        self.components['tava'] = {
            'name': 'TAVA',
            'required': False,
            'installers': [
                GitRepoInstaller(
                    'TAVA',
                    'https://github.com/facebookresearch/tava.git',
                    Path.home() / ".vfx_pipeline" / "tava"
                )
            ]
        }

        # ECON
        self.components['econ'] = {
            'name': 'ECON',
            'required': False,
            'installers': [
                GitRepoInstaller(
                    'ECON',
                    'https://github.com/YuliangXiu/ECON.git',
                    Path.home() / ".vfx_pipeline" / "ECON"
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

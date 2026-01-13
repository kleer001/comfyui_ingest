#!/usr/bin/env python3
"""Patch ComfyUI to fix BrokenPipeError during model downloads.

This script checks if ComfyUI needs patching and applies fixes if necessary.
It only patches if the vulnerable code pattern is detected - does nothing
if already patched or if ComfyUI has the fix upstream.

Usage:
    python scripts/patch_comfyui.py
    python scripts/patch_comfyui.py --check  # Just check, don't patch
    python scripts/patch_comfyui.py --comfyui-path /path/to/ComfyUI

Run this once after installing ComfyUI, then restart ComfyUI for changes to take effect.
"""

import re
import sys
from pathlib import Path

# Try to import env_config for INSTALL_DIR
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from env_config import INSTALL_DIR
    DEFAULT_COMFYUI_DIR = INSTALL_DIR / "ComfyUI"
except ImportError:
    DEFAULT_COMFYUI_DIR = Path(__file__).parent.parent / ".vfx_pipeline" / "ComfyUI"


def check_needs_patch(logger_path: Path) -> tuple[bool, str]:
    """Check if logger.py needs the BrokenPipeError patch.

    Returns:
        (needs_patch, reason) tuple
    """
    if not logger_path.exists():
        return False, "file not found"

    content = logger_path.read_text()

    # Check if already has error handling (patched or fixed upstream)
    if "except (OSError, ValueError)" in content:
        return False, "already patched by this script"

    if "except OSError" in content or "except BrokenPipeError" in content:
        return False, "already fixed upstream (has OSError/BrokenPipeError handling)"

    # Check for the vulnerable pattern: flush without try/except
    vulnerable_patterns = [
        r"def flush\(self\):\n        super\(\)\.flush\(\)",  # 8-space indent
        r"def flush\(self\):\n    super\(\)\.flush\(\)",      # 4-space indent
    ]

    for pattern in vulnerable_patterns:
        if re.search(pattern, content):
            return True, "vulnerable pattern found (flush without error handling)"

    # Check if flush method exists at all
    if "def flush(self)" in content:
        return False, "flush method exists but has different structure (may be safe)"

    return False, "no flush method found"


def patch_logger(comfyui_path: Path, dry_run: bool = False) -> bool:
    """Patch ComfyUI's logger.py to handle flush errors gracefully.

    Args:
        comfyui_path: Path to ComfyUI installation
        dry_run: If True, only check and report, don't modify

    Returns:
        True if patch was applied (or would be applied in dry_run)
    """
    logger_path = comfyui_path / "app" / "logger.py"

    print(f"  Checking: {logger_path}")
    needs_patch, reason = check_needs_patch(logger_path)

    if not needs_patch:
        print(f"  Status: No patch needed ({reason})")
        return False

    print(f"  Status: {reason}")

    if dry_run:
        print("  Action: Would patch (dry-run mode)")
        return True

    try:
        content = logger_path.read_text()

        # Apply patch based on detected pattern
        patterns = [
            ("def flush(self):\n        super().flush()", "        "),
            ("def flush(self):\n    super().flush()", "    "),
        ]

        for old_pattern, indent in patterns:
            if old_pattern in content:
                new_pattern = f"""def flush(self):
{indent}try:
{indent}    super().flush()
{indent}except (OSError, ValueError):
{indent}    pass  # Ignore flush errors (BrokenPipe, etc.)"""
                patched = content.replace(old_pattern, new_pattern)
                logger_path.write_text(patched)
                print("  Action: Patched successfully!")
                return True

        print("  Action: Pattern not found for patching")
        return False

    except Exception as e:
        print(f"  Error: {e}")
        return False


def patch_prestartup(comfyui_path: Path, dry_run: bool = False) -> bool:
    """Check for and patch ComfyUI-Manager's prestartup_script.py if needed."""
    prestartup_paths = [
        comfyui_path / "custom_nodes" / "ComfyUI-Manager" / "prestartup_script.py",
        comfyui_path / "custom_nodes" / "comfyui-manager" / "prestartup_script.py",
    ]

    for prestartup_path in prestartup_paths:
        if not prestartup_path.exists():
            continue

        print(f"  Checking: {prestartup_path}")
        content = prestartup_path.read_text()

        # Check if already patched
        if "except (OSError, ValueError)" in content and "original_stderr.flush" in content:
            print("  Status: Already patched")
            return False

        # Look for vulnerable flush function
        pattern = r"def flush\(self\):\n        self\.original_stderr\.flush\(\)"
        if not re.search(pattern, content):
            print("  Status: No vulnerable pattern found")
            return False

        print("  Status: Vulnerable pattern found")

        if dry_run:
            print("  Action: Would patch (dry-run mode)")
            return True

        replacement = """def flush(self):
        try:
            self.original_stderr.flush()
        except (OSError, ValueError):
            pass  # Ignore flush errors"""

        patched = re.sub(pattern, replacement, content)
        prestartup_path.write_text(patched)
        print("  Action: Patched successfully!")
        return True

    print("  ComfyUI-Manager prestartup_script.py not found (optional)")
    return False


def get_comfyui_version(comfyui_path: Path) -> str:
    """Try to get ComfyUI version from various sources."""
    # Try pyproject.toml
    pyproject = comfyui_path / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)

    # Try git describe
    try:
        import subprocess
        result = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            cwd=comfyui_path,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    return "unknown"


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Patch ComfyUI to fix BrokenPipeError during model downloads",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script only patches if the vulnerable code pattern is detected.
If ComfyUI already has the fix (either from this script or upstream),
no changes will be made.

See: https://github.com/Comfy-Org/ComfyUI/pull/11629
"""
    )
    parser.add_argument(
        "--comfyui-path",
        type=Path,
        default=DEFAULT_COMFYUI_DIR,
        help=f"Path to ComfyUI installation (default: {DEFAULT_COMFYUI_DIR})"
    )
    parser.add_argument(
        "--check", "-c",
        action="store_true",
        help="Only check if patching is needed, don't modify files"
    )

    args = parser.parse_args()
    comfyui_path = args.comfyui_path.resolve()

    print("ComfyUI Patch Checker")
    print("=" * 50)
    print(f"ComfyUI path: {comfyui_path}")

    if not comfyui_path.exists():
        print(f"\nError: ComfyUI not found at {comfyui_path}")
        print("Use --comfyui-path to specify the correct location")
        sys.exit(1)

    if not (comfyui_path / "main.py").exists():
        print(f"\nError: {comfyui_path} doesn't look like a ComfyUI installation")
        print("(main.py not found)")
        sys.exit(1)

    version = get_comfyui_version(comfyui_path)
    print(f"ComfyUI version: {version}")
    print(f"Mode: {'Check only' if args.check else 'Patch if needed'}")
    print()

    print("Checking logger.py...")
    logger_patched = patch_logger(comfyui_path, dry_run=args.check)

    print()
    print("Checking ComfyUI-Manager...")
    prestartup_patched = patch_prestartup(comfyui_path, dry_run=args.check)

    print()
    print("=" * 50)

    if args.check:
        if logger_patched or prestartup_patched:
            print("Result: Patches ARE needed")
            print("Run without --check to apply patches")
            sys.exit(1)
        else:
            print("Result: No patches needed")
            sys.exit(0)
    else:
        if logger_patched or prestartup_patched:
            print("Result: Patches applied!")
            print()
            print("IMPORTANT: Restart ComfyUI for changes to take effect.")
        else:
            print("Result: No patches were needed")


if __name__ == "__main__":
    main()

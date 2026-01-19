"""Automatic log capture and rotation for bug reporting.

Captures all terminal output (stdout/stderr) to timestamped log files
with automatic rotation (keeps newest 10 logs). Log files include OS
and environment context for debugging.

Usage:
    from log_manager import LogCapture

    with LogCapture() as log:
        # Your code here - all output automatically captured
        run_pipeline()

    # Log file automatically saved and rotated
"""

import sys
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Optional, TextIO

from install_wizard.platform import PlatformManager
from env_config import is_in_container


class TeeWriter:
    """Write to multiple streams simultaneously (tee-like behavior).

    Fails gracefully - if writing to one stream fails, continues with others.
    Always prioritizes the first stream (typically stdout/stderr) to ensure
    user sees output even if log file writing fails.
    """

    def __init__(self, *streams: TextIO):
        self.streams = streams

    def write(self, data: str) -> None:
        """Write data to all streams.

        If writing to any stream fails, continues with remaining streams.
        Always writes to first stream (stdout/stderr) first.
        """
        for stream in self.streams:
            try:
                stream.write(data)
                stream.flush()
            except Exception:
                pass

    def flush(self) -> None:
        """Flush all streams.

        If flushing any stream fails, continues with remaining streams.
        """
        for stream in self.streams:
            try:
                stream.flush()
            except Exception:
                pass


class LogCapture:
    """Context manager for capturing terminal output to log files.

    Automatically:
    - Captures stdout and stderr
    - Displays output to terminal (tee behavior)
    - Saves to timestamped log file
    - Rotates logs (keeps newest 10)
    - Includes system metadata (OS, environment, command)

    IMPORTANT: This class is designed to be fail-safe. If logging setup
    fails for any reason (permissions, disk space, etc.), it will silently
    disable logging and allow the wrapped code to run normally. This ensures
    that logging never interrupts critical operations like renders or simulations.

    Attributes:
        log_dir: Directory where logs are stored (default: logs/)
        max_logs: Maximum number of logs to keep (default: 10)
    """

    def __init__(self, log_dir: Path = None, max_logs: int = 10):
        """Initialize log capture.

        Args:
            log_dir: Directory for log files (default: repo_root/logs/)
            max_logs: Maximum number of logs to keep (default: 10)
        """
        if log_dir is None:
            repo_root = Path(__file__).parent.parent
            log_dir = repo_root / "logs"

        self.log_dir = Path(log_dir)
        self.max_logs = max_logs
        self.log_file: Optional[Path] = None
        self.log_handle: Optional[TextIO] = None
        self._logging_enabled = False

        self.stdout_buffer = StringIO()
        self.stderr_buffer = StringIO()

        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

    def __enter__(self):
        """Start log capture.

        If logging setup fails for any reason, silently disables logging
        and continues without interrupting the wrapped code.
        """
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = self._generate_log_filename()
            self.log_handle = open(self.log_file, 'w', encoding='utf-8')
            self._write_log_header()

            sys.stdout = TeeWriter(self._original_stdout, self.stdout_buffer, self.log_handle)
            sys.stderr = TeeWriter(self._original_stderr, self.stderr_buffer, self.log_handle)

            self._logging_enabled = True

        except Exception:
            self._logging_enabled = False
            if self.log_handle:
                try:
                    self.log_handle.close()
                except Exception:
                    pass
            self.log_handle = None
            self.log_file = None

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop log capture and finalize log file.

        Always restores original stdout/stderr, even if logging failed.
        Never raises exceptions to avoid interrupting user code.
        """
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr

        if self._logging_enabled and self.log_handle:
            try:
                if exc_type is not None:
                    self.log_handle.write(f"\n{'='*80}\n")
                    self.log_handle.write(f"FATAL ERROR: {exc_type.__name__}: {exc_val}\n")
                    self.log_handle.write(f"{'='*80}\n")
            except Exception:
                pass

            try:
                self.log_handle.close()
            except Exception:
                pass

        if self._logging_enabled:
            try:
                self._rotate_logs()
            except Exception:
                pass

        return False

    def _generate_log_filename(self) -> Path:
        """Generate timestamped log filename with OS and environment.

        Format: YYYYMMDD_HHMMSS_microseconds_<osname>_<conda|docker>.log
        Examples:
            20260119_143022_123456_linux_conda.log
            20260119_150033_789012_macos_docker.log
            20260119_161544_345678_windows_conda.log

        Microseconds ensure unique filenames even if multiple logs
        are created in the same second.

        Returns:
            Path to log file
        """
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        microseconds = f"{now.microsecond:06d}"

        os_name, environment, _ = PlatformManager.detect_platform()

        if environment == "wsl2":
            os_name = "wsl2"

        env_type = "docker" if is_in_container() else "conda"

        filename = f"{timestamp}_{microseconds}_{os_name}_{env_type}.log"
        return self.log_dir / filename

    def _write_log_header(self) -> None:
        """Write metadata header to log file."""
        import platform
        import subprocess
        import sys as sys_module

        os_name, environment, pkg_mgr = PlatformManager.detect_platform()
        env_type = "docker" if is_in_container() else "conda"

        git_commit = self._get_git_commit()

        header = f"""{'='*80}
VFX Pipeline Log
{'='*80}
Timestamp:       {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Git Commit:      {git_commit}
OS:              {os_name} ({environment})
Package Manager: {pkg_mgr}
Environment:     {env_type}
Python Version:  {sys_module.version.split()[0]}
Platform:        {platform.platform()}
Command:         {' '.join(sys_module.argv)}
{'='*80}

"""
        self.log_handle.write(header)
        self.log_handle.flush()

    def _get_git_commit(self) -> str:
        """Get current git commit hash and branch.

        Returns:
            Git commit info or 'unknown' if not available.
            Format: "abc1234 (branch-name)" or "abc1234 (detached HEAD)"
        """
        try:
            import subprocess
            repo_root = Path(__file__).parent.parent

            commit_result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=2
            )

            if commit_result.returncode != 0:
                return "unknown (not a git repository)"

            commit_hash = commit_result.stdout.strip()

            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=2
            )

            if branch_result.returncode == 0:
                branch = branch_result.stdout.strip()
                return f"{commit_hash} ({branch})"
            else:
                return commit_hash

        except Exception:
            return "unknown"

    def _rotate_logs(self) -> None:
        """Keep only the newest max_logs log files."""
        log_files = sorted(
            self.log_dir.glob("*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        for old_log in log_files[self.max_logs:]:
            old_log.unlink()
            print(f"Rotated old log: {old_log.name}", file=self._original_stdout)

    def get_log_path(self) -> Optional[Path]:
        """Get path to current log file.

        Returns:
            Path to log file, or None if not capturing
        """
        return self.log_file


def get_recent_logs(log_dir: Path = None, count: int = 10) -> list[Path]:
    """Get list of recent log files.

    Args:
        log_dir: Directory containing logs (default: repo_root/logs/)
        count: Number of recent logs to return (default: 10)

    Returns:
        List of log file paths, newest first
    """
    if log_dir is None:
        repo_root = Path(__file__).parent.parent
        log_dir = repo_root / "logs"

    log_files = sorted(
        log_dir.glob("*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    return log_files[:count]


def print_log_summary(log_file: Path) -> None:
    """Print summary of a log file (header + last 20 lines).

    Args:
        log_file: Path to log file
    """
    if not log_file.exists():
        print(f"Log file not found: {log_file}", file=sys.stderr)
        return

    lines = log_file.read_text(encoding='utf-8').splitlines()

    header_end = 0
    for i, line in enumerate(lines):
        if line.startswith("="*80) and i > 0:
            header_end = i + 2
            break

    print("\n".join(lines[:header_end]))

    if len(lines) > header_end + 20:
        print(f"\n... ({len(lines) - header_end - 20} lines omitted) ...\n")
        print("\n".join(lines[-20:]))
    else:
        print("\n".join(lines[header_end:]))

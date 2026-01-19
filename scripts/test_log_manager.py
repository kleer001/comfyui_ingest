#!/usr/bin/env python3
"""Comprehensive tests for log_manager.py fail-safe behavior.

Tests that logging never interrupts critical user code, even when:
- Log directory can't be created (permissions)
- Log file can't be written (disk full, permissions)
- Exceptions occur in user code
- Log rotation fails

All tests should pass without raising exceptions.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent))

from log_manager import LogCapture, get_recent_logs


def test_normal_operation():
    """Test 1: Normal operation - logging should work."""
    print("\n=== Test 1: Normal Operation ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_log_dir = Path(tmpdir) / "logs"

        with LogCapture(log_dir=test_log_dir) as capture:
            print("Test message to stdout")
            print("Test message to stderr", file=sys.stderr)

        logs = list(test_log_dir.glob("*.log"))
        if logs:
            print(f"✓ Log file created: {logs[0].name}")
            content = logs[0].read_text()
            if "Test message to stdout" in content and "Test message to stderr" in content:
                print("✓ Both stdout and stderr captured")
            else:
                print("✗ FAIL: Messages not in log")
        else:
            print("✗ FAIL: No log file created")


def test_cannot_create_directory():
    """Test 2: Log directory creation fails - user code should still run."""
    print("\n=== Test 2: Cannot Create Directory ===")

    user_code_ran = False

    with patch('pathlib.Path.mkdir', side_effect=PermissionError("No permission")):
        try:
            with LogCapture(log_dir="/nonexistent/readonly/logs"):
                print("User code running despite logging failure")
                user_code_ran = True
        except PermissionError:
            print("✗ FAIL: PermissionError not caught - user code interrupted")

    if user_code_ran:
        print("✓ User code ran successfully despite directory creation failure")
    else:
        print("✗ FAIL: User code did not run")


def test_cannot_open_log_file():
    """Test 3: Log file open fails - user code should still run."""
    print("\n=== Test 3: Cannot Open Log File ===")

    user_code_ran = False

    original_open = open
    def mock_open(file, *args, **kwargs):
        if str(file).endswith('.log'):
            raise OSError("Disk full")
        return original_open(file, *args, **kwargs)

    with patch('builtins.open', side_effect=mock_open):
        try:
            with LogCapture():
                print("User code running despite log file open failure")
                user_code_ran = True
        except OSError:
            print("✗ FAIL: OSError not caught - user code interrupted")

    if user_code_ran:
        print("✓ User code ran successfully despite file open failure")
    else:
        print("✗ FAIL: User code did not run")


def test_exception_in_user_code():
    """Test 4: Exception in user code - should be logged and propagated."""
    print("\n=== Test 4: Exception in User Code ===")

    exception_caught = False

    with tempfile.TemporaryDirectory() as tmpdir:
        test_log_dir = Path(tmpdir) / "logs"

        try:
            with LogCapture(log_dir=test_log_dir):
                print("About to raise exception")
                raise ValueError("Test exception")
        except ValueError as e:
            if str(e) == "Test exception":
                exception_caught = True
                print("✓ Exception propagated correctly")

        logs = list(test_log_dir.glob("*.log"))
        if logs:
            content = logs[0].read_text()
            if "FATAL ERROR" in content and "ValueError" in content:
                print("✓ Exception logged to file")
            else:
                print("✗ FAIL: Exception not properly logged")
        else:
            print("⚠ Warning: No log file (logging may have failed silently)")

    if not exception_caught:
        print("✗ FAIL: Exception not propagated")


def test_log_rotation():
    """Test 5: Log rotation - should keep only newest N logs."""
    print("\n=== Test 5: Log Rotation ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_log_dir = Path(tmpdir) / "logs"
        max_logs = 3

        for i in range(5):
            with LogCapture(log_dir=test_log_dir, max_logs=max_logs):
                print(f"Creating log {i+1}")

        logs = list(test_log_dir.glob("*.log"))
        if len(logs) == max_logs:
            print(f"✓ Rotation working: {len(logs)} logs kept (max: {max_logs})")
        else:
            print(f"✗ FAIL: Expected {max_logs} logs, found {len(logs)}")


def test_nested_capture():
    """Test 6: Nested LogCapture (should be avoided, but shouldn't crash)."""
    print("\n=== Test 6: Nested Capture (edge case) ===")

    user_code_ran = False

    with tempfile.TemporaryDirectory() as tmpdir:
        test_log_dir = Path(tmpdir) / "logs"

        try:
            with LogCapture(log_dir=test_log_dir):
                print("Outer capture")
                with LogCapture(log_dir=test_log_dir):
                    print("Inner capture")
                    user_code_ran = True
                print("Back to outer")
        except Exception as e:
            print(f"✗ FAIL: Nested capture raised exception: {e}")

    if user_code_ran:
        print("✓ Nested capture handled (not recommended, but doesn't crash)")
    else:
        print("✗ FAIL: Inner code did not run")


def test_write_failure_during_operation():
    """Test 7: Write fails during operation - should not crash."""
    print("\n=== Test 7: Write Failure During Operation ===")

    user_code_completed = False

    with tempfile.TemporaryDirectory() as tmpdir:
        test_log_dir = Path(tmpdir) / "logs"

        try:
            with LogCapture(log_dir=test_log_dir) as capture:
                print("Message 1")

                if capture.log_handle:
                    capture.log_handle.close()

                print("Message 2 (log file closed)")
                user_code_completed = True
        except Exception as e:
            print(f"✗ FAIL: Exception raised when log file closed: {e}")

    if user_code_completed:
        print("✓ Continued running even after log file was closed")
    else:
        print("✗ FAIL: Did not complete user code")


def test_git_unavailable():
    """Test 8: Git unavailable - should still log with 'unknown'."""
    print("\n=== Test 8: Git Unavailable ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_log_dir = Path(tmpdir) / "logs"

        with patch('subprocess.run', side_effect=FileNotFoundError("git not found")):
            try:
                with LogCapture(log_dir=test_log_dir):
                    print("Running without git")
            except FileNotFoundError:
                print("✗ FAIL: FileNotFoundError not caught")

        logs = list(test_log_dir.glob("*.log"))
        if logs:
            content = logs[0].read_text()
            if "Git Commit:" in content and "unknown" in content:
                print("✓ Log created with 'unknown' git commit")
            else:
                print("✗ FAIL: Git commit line not handled properly")
        else:
            print("✗ FAIL: No log file created")


def main():
    """Run all tests."""
    print("="*80)
    print("LOG MANAGER FAIL-SAFE TEST SUITE")
    print("="*80)
    print("\nTesting that logging NEVER interrupts user code...")

    tests = [
        test_normal_operation,
        test_cannot_create_directory,
        test_cannot_open_log_file,
        test_exception_in_user_code,
        test_log_rotation,
        test_nested_capture,
        test_write_failure_during_operation,
        test_git_unavailable,
    ]

    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n✗ CRITICAL FAILURE in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80)
    print("\nIf all tests passed with ✓, logging is fail-safe.")
    print("User code will never be interrupted by logging failures.\n")


if __name__ == "__main__":
    main()

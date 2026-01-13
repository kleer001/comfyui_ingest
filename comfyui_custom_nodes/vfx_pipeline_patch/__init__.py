"""VFX Pipeline Patch - Auto-fixes BrokenPipeError in ComfyUI.

This custom node patches ComfyUI's logger to handle flush errors gracefully.
It runs automatically when ComfyUI loads custom nodes - no manual action needed.

The patch fixes BrokenPipeError that occurs when tqdm progress bars try to
flush stderr during model downloads (e.g., HuggingFace downloads).

See: https://github.com/Comfy-Org/ComfyUI/pull/11629
"""

import sys


def _patch_flush_errors():
    """Monkey-patch any stream wrappers to handle flush errors."""
    # Patch sys.stderr if it has a flush method that might fail
    original_stderr = sys.stderr

    class SafeStderr:
        """Wrapper that catches flush errors."""

        def __init__(self, stream):
            self._stream = stream

        def write(self, data):
            try:
                return self._stream.write(data)
            except (OSError, ValueError, BrokenPipeError):
                pass

        def flush(self):
            try:
                self._stream.flush()
            except (OSError, ValueError, BrokenPipeError):
                pass  # Ignore flush errors

        def __getattr__(self, name):
            return getattr(self._stream, name)

    # Only wrap if not already wrapped
    if not isinstance(sys.stderr, SafeStderr):
        sys.stderr = SafeStderr(original_stderr)

    # Also try to patch the ComfyUI logger if it exists
    try:
        from app import logger as comfy_logger

        # Find any custom stream classes and patch their flush methods
        for name in dir(comfy_logger):
            obj = getattr(comfy_logger, name)
            if isinstance(obj, type) and hasattr(obj, "flush"):
                original_flush = obj.flush

                def safe_flush(self, _original=original_flush):
                    try:
                        _original(self)
                    except (OSError, ValueError, BrokenPipeError):
                        pass

                obj.flush = safe_flush
    except ImportError:
        pass  # ComfyUI logger not available yet, that's OK


# Apply patch immediately when this module is imported
_patch_flush_errors()

# ComfyUI requires these to recognize this as a valid custom node
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

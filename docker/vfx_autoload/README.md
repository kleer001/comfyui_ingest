# ComfyUI Workflow Auto-Loader

A simple ComfyUI frontend extension that automatically loads a workflow when the page opens.

## Features

- **URL parameter support**: Load any workflow via `?workflow=/path/to/file.json`
- **Default location fallback**: Automatically loads from `/input/auto_load_workflow.json`
- **No browser caching**: Works reliably with Docker, tunnels, and changing URLs
- **Minimal footprint**: Single file, ~60 lines, no dependencies

## Installation

Copy this folder to your ComfyUI extensions directory:

```bash
cp -r vfx_autoload /path/to/ComfyUI/web/extensions/
```

Or with Docker, mount it as a volume:

```yaml
volumes:
  - ./vfx_autoload:/path/to/ComfyUI/web/extensions/vfx_autoload:ro
```

## Usage

### Method 1: URL Parameter

Open ComfyUI with a workflow path in the URL:

```
http://localhost:8188/?workflow=/input/my_workflow.json
```

The path is relative to ComfyUI's web root. Common locations:
- `/input/` - ComfyUI's input directory
- `/output/` - ComfyUI's output directory
- `/user/default/workflows/` - User's saved workflows

### Method 2: Default Location

Place your workflow at the default location and it will load automatically:

```bash
cp my_workflow.json /path/to/ComfyUI/input/auto_load_workflow.json
```

The URL parameter takes precedence if both are present.

## Why This Extension?

ComfyUI doesn't have native support for loading a workflow via command line or URL parameter ([feature request #9858](https://github.com/comfyanonymous/ComfyUI/issues/9858)).

Existing solutions like ComfyUI-Custom-Scripts use browser localStorage, which:
- Doesn't work with Docker (different browser sessions)
- Breaks when URLs change (tunnels, port forwarding)
- Requires manual setup in the browser

This extension solves these issues by:
- Using URL parameters (stateless, shareable)
- Fetching from server paths (works with any browser)
- Requiring zero browser-side configuration

## Integration Example

Launch ComfyUI and open a specific workflow:

```python
import webbrowser
import subprocess

# Start ComfyUI
subprocess.Popen(["python", "main.py", "--listen", "0.0.0.0"])

# Open browser with workflow
webbrowser.open("http://localhost:8188/?workflow=/input/my_workflow.json")
```

## License

MIT - Use freely in your own projects.

## Credits

Created for [shot-gopher](https://github.com/kleer001/shot-gopher) VFX pipeline.

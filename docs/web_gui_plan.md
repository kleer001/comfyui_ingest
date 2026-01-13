# Web GUI Implementation Plan

A local web interface for the VFX Pipeline - drag-and-drop video processing with real-time progress monitoring.

## Overview

The web GUI provides a browser-based interface to the existing pipeline, served from a local Python server. Users can upload videos, configure processing stages, monitor progress, and download results without touching the command line.

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│                    User's Browser                        │
│         http://localhost:5000                           │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                 Web Server (FastAPI)                     │
│  ├── Static files (HTML/CSS/JS)                         │
│  ├── REST API endpoints                                 │
│  └── WebSocket for real-time progress                   │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│               Existing Pipeline Scripts                  │
│  ├── run_pipeline.py                                    │
│  ├── env_config.py (paths, env settings)                │
│  └── comfyui_utils.py (workflow execution)              │
└─────────────────────────────────────────────────────────┘
```

## Design Principles

1. **Minimal new code** - Reuse existing scripts, don't rewrite pipeline logic
2. **No external services** - Everything runs locally, no cloud dependencies
3. **No build step** - Vanilla HTML/CSS/JS, no npm/webpack
4. **Single entry point** - One command to start: `python scripts/start_web.py`
5. **Respect existing config** - Use `env_config.py` for all paths

## MVP Features

### Must Have
- [ ] Drag-and-drop video upload
- [ ] Stage selection (checkboxes or preset)
- [ ] Roto prompt text input (when roto enabled)
- [ ] "Start Processing" button
- [ ] Progress display (current stage, percentage)
- [ ] "Done" state with output file listing
- [ ] "Open Folder" button to reveal outputs

### Nice to Have (Post-MVP)
- [ ] Thumbnail previews of each pass
- [ ] Log viewer (collapsible)
- [ ] Job history / project list
- [ ] Re-run with different settings
- [ ] Download ZIP of all outputs
- [ ] Side-by-side comparison viewer

## File Structure

```
comfyui_ingest/
├── web/                          # NEW: Web UI package
│   ├── __init__.py
│   ├── server.py                 # FastAPI application
│   ├── api.py                    # REST API endpoints
│   ├── websocket.py              # WebSocket handlers
│   ├── pipeline_runner.py        # Pipeline execution wrapper
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── app.js            # Frontend logic
│   └── templates/
│       └── index.html            # Main page
├── scripts/
│   ├── start_web.py              # NEW: Entry point
│   └── ...
```

## API Design

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve main HTML page |
| `/api/upload` | POST | Upload video file, returns `project_id` |
| `/api/projects` | GET | List all projects |
| `/api/projects/{id}` | GET | Get project status and details |
| `/api/projects/{id}/start` | POST | Start processing with config |
| `/api/projects/{id}/stop` | POST | Cancel processing |
| `/api/projects/{id}/outputs` | GET | List output files |
| `/api/system/status` | GET | Check ComfyUI, disk space, etc. |

### WebSocket

| Event | Direction | Description |
|-------|-----------|-------------|
| `connect` | Client→Server | Establish connection for project |
| `progress` | Server→Client | Stage progress update |
| `log` | Server→Client | Log line (optional) |
| `stage_complete` | Server→Client | Stage finished |
| `pipeline_complete` | Server→Client | All stages done |
| `error` | Server→Client | Error occurred |

### Request/Response Examples

**Upload Video:**
```http
POST /api/upload
Content-Type: multipart/form-data

file: <video_file>
name: "My_Shot"  (optional, defaults to filename)
```

Response:
```json
{
  "project_id": "my_shot_20240115_143022",
  "project_dir": "/path/to/vfx_projects/My_Shot",
  "video_info": {
    "duration": 10.5,
    "fps": 24.0,
    "resolution": [1920, 1080],
    "frame_count": 252
  }
}
```

**Start Processing:**
```http
POST /api/projects/{id}/start
Content-Type: application/json

{
  "stages": ["ingest", "depth", "roto", "cleanplate"],
  "roto_prompt": "person",
  "skip_existing": false
}
```

**Progress WebSocket Message:**
```json
{
  "type": "progress",
  "stage": "roto",
  "stage_index": 2,
  "total_stages": 4,
  "progress": 0.42,
  "frame": 84,
  "total_frames": 200,
  "message": "Processing frame 84..."
}
```

## UI States

### State 1: Ready (Initial)

```
┌─────────────────────────────────────────────────────────┐
│                    VFX Pipeline                         │
│                                                         │
│         ┌─────────────────────────────────┐            │
│         │                                 │            │
│         │      Drop video here            │            │
│         │      or click to browse         │            │
│         │                                 │            │
│         │      Supported: mp4, mov, avi   │            │
│         │                                 │            │
│         └─────────────────────────────────┘            │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Recent Projects:                                       │
│  (none yet)                                            │
│                                                         │
│  System Status: ● ComfyUI running                      │
└─────────────────────────────────────────────────────────┘
```

### State 2: Configure

```
┌─────────────────────────────────────────────────────────┐
│  hero_shot.mp4                              [✕ Cancel] │
│  1920x1080 • 24fps • 252 frames • 10.5s               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Project Name: [hero_shot___________________]          │
│                                                         │
│  Processing Stages:                                     │
│  ☑ Depth Maps                                          │
│  ☑ Segmentation (Roto)                                 │
│      Prompt: [person______________________]            │
│  ☑ Clean Plate                                         │
│  ☐ Camera Solve (COLMAP)                               │
│  ☐ Materials (GS-IR) - Requires COLMAP                 │
│  ☐ Motion Capture - Requires COLMAP                    │
│                                                         │
│  ─────────────── Quick Presets ───────────────         │
│  [Quick Preview]  [Full VFX]  [Everything]             │
│                                                         │
│  ☐ Skip existing outputs                               │
│                                                         │
│                              [▶ Start Processing]      │
└─────────────────────────────────────────────────────────┘
```

### State 3: Processing

```
┌─────────────────────────────────────────────────────────┐
│  hero_shot                                  [■ Cancel] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Stage 2 of 4: Segmentation                            │
│                                                         │
│  ████████████████░░░░░░░░░░░░░░  42%                  │
│                                                         │
│  Frame 84 / 200                                        │
│  Elapsed: 2m 34s • Remaining: ~3m 30s                  │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  ✓ Ingest           200 frames extracted               │
│  ✓ Depth            200 depth maps                     │
│  ◐ Segmentation     84/200 masks...                    │
│  ○ Clean Plate      pending                            │
│                                                         │
│                                           [▼ Show Log] │
└─────────────────────────────────────────────────────────┘
```

### State 4: Complete

```
┌─────────────────────────────────────────────────────────┐
│  hero_shot                          ✓ Complete         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Output Passes:                                         │
│                                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │ source  │ │  depth  │ │  roto   │ │ clean   │      │
│  │  [img]  │ │  [img]  │ │  [img]  │ │  [img]  │      │
│  │ 200 fr  │ │ 200 fr  │ │ 200 fr  │ │ 200 fr  │      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
│                                                         │
│  Total processing time: 6m 04s                         │
│                                                         │
│  [📁 Open Folder]                   [🔄 Run Again]     │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│  [← New Project]                                       │
└─────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Foundation (Backend)
1. Create `web/` package structure
2. Implement FastAPI server with static file serving
3. Create upload endpoint with video validation
4. Implement project status endpoint
5. Create pipeline runner wrapper (calls `run_pipeline.py`)

### Phase 2: Core UI (Frontend)
1. HTML page with drop zone
2. CSS styling (dark theme, clean layout)
3. JavaScript for drag-and-drop upload
4. Stage selection form
5. Basic progress polling (before WebSocket)

### Phase 3: Real-Time Progress
1. WebSocket server integration
2. Pipeline output parsing for progress
3. Frontend WebSocket client
4. Real-time progress bar updates
5. Log streaming (optional)

### Phase 4: Polish
1. Project history / listing
2. Thumbnail generation for outputs
3. Error handling and display
4. "Open Folder" integration
5. System status checks

## Technical Decisions

### Why FastAPI?
- Async-native (good for WebSocket + long-running tasks)
- Automatic OpenAPI docs at `/docs`
- Built-in WebSocket support
- Minimal boilerplate

### Why Vanilla JS?
- No build step required
- Works offline
- Small bundle size (it's just a few KB)
- Easy to modify

### Why Local Server (not GitHub Pages)?
- Can't execute backend code from static hosting
- Can't access local filesystem
- Can't run GPU processing remotely
- Simpler architecture (no CORS issues)

## Dependencies

**New Python packages:**
```
fastapi>=0.100.0
uvicorn>=0.23.0
python-multipart>=0.0.6  # For file uploads
websockets>=11.0         # For real-time progress
```

**Optional (for thumbnails):**
```
pillow>=9.0.0            # Already in requirements
```

## Entry Point

`scripts/start_web.py`:
```python
#!/usr/bin/env python3
"""Launch the VFX Pipeline web interface."""

import webbrowser
import uvicorn
from env_config import check_conda_env_or_warn

def main():
    check_conda_env_or_warn()

    host = "127.0.0.1"
    port = 5000
    url = f"http://{host}:{port}"

    print(f"""
╔════════════════════════════════════════════════════════╗
║           VFX Pipeline Web Interface                   ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║   Server running at: {url}                     ║
║                                                        ║
║   Press Ctrl+C to stop                                 ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
""")

    # Open browser
    webbrowser.open(url)

    # Start server
    uvicorn.run("web.server:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    main()
```

## Integration with Existing Code

The web server will:

1. **Import from `env_config.py`:**
   - `DEFAULT_PROJECTS_DIR` - where to create projects
   - `INSTALL_DIR` - where ComfyUI lives
   - `check_conda_env_or_warn()` - environment validation

2. **Import from `comfyui_utils.py`:**
   - `check_comfyui_running()` - system status
   - `DEFAULT_COMFYUI_URL` - ComfyUI endpoint

3. **Call `run_pipeline.py` via subprocess:**
   - Capture stdout/stderr for progress parsing
   - Pass through all configuration options
   - Handle cancellation via process termination

4. **Use existing project structure:**
   - Same folder layout as CLI
   - Same workflow templates
   - Compatible with `janitor.py` maintenance

## Open Questions

1. **Multi-user support?** - MVP assumes single user. Queue system needed for concurrent processing.

2. **File size limits?** - Large videos (10GB+) may need chunked upload or path-based input.

3. **ComfyUI auto-start?** - Should web server start ComfyUI automatically, or require it pre-running?

4. **Authentication?** - MVP has none. Add basic auth if exposing to network.

## Success Criteria

MVP is complete when:
- [ ] User can drag video onto page
- [ ] User can select stages and enter roto prompt
- [ ] User can start processing
- [ ] User sees progress updates
- [ ] User sees completion with output listing
- [ ] User can click to open output folder
- [ ] All without touching command line (after initial `start_web.py`)

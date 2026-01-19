# Pipeline Script Refactor Roadmap

**Goal:** Split `run_pipeline.py` (1544 lines) into 4-5 focused modules.

## Current Structure Analysis

| Section | Lines | Description |
|---------|-------|-------------|
| Imports/Constants | 1-77 | Stage definitions, formats |
| General Utilities | 80-507 | FFmpeg, subprocess, file ops |
| Workflow Manipulation | 520-794 | ComfyUI JSON updates |
| Stage Runners | 267-520, 797-855 | External script wrappers |
| Main Orchestration | 857-1373 | `run_pipeline()` function |
| CLI | 1376-1544 | argparse `main()` |

## Proposed Module Split

### 1. `pipeline_utils.py` (~180 lines)
General-purpose utilities with no pipeline-specific logic.

**Move:**
- `run_command()` - subprocess wrapper with streaming
- `get_frame_count()` - ffprobe frame counter
- `extract_frames()` - ffmpeg frame extraction
- `get_video_info()` - ffprobe metadata
- `generate_preview_movie()` - ffmpeg movie generation
- `get_image_dimensions()` - ffprobe dimensions
- `clear_gpu_memory()` - torch VRAM cleanup

### 2. `workflow_utils.py` (~200 lines)
ComfyUI workflow JSON manipulation.

**Move:**
- `get_comfyui_output_dir()`
- `refresh_workflow_from_template()`
- `update_segmentation_prompt()`
- `update_matanyone_input()`
- `update_cleanplate_resolution()`
- `combine_mattes()`
- `combine_mask_sequences()`

### 3. `stage_runners.py` (~150 lines)
Thin wrappers that invoke external scripts.

**Move:**
- `run_export_camera()`
- `run_colmap_reconstruction()`
- `export_camera_to_vfx_formats()`
- `run_mocap()`
- `run_gsir_materials()`
- `setup_project()`

### 4. `run_pipeline.py` (~500 lines, trimmed)
Orchestration only - imports from above modules.

**Keep:**
- Constants: `STAGES`, `STAGE_ORDER`, `START_FRAME`, `SUPPORTED_FORMATS`
- `sanitize_stages()`
- `run_pipeline()` - main orchestration (consider further inline comments removal)
- `main()` - CLI entry point

## Dependency Graph

```
run_pipeline.py
├── pipeline_utils.py (no internal deps)
├── workflow_utils.py
│   └── pipeline_utils.py (for get_image_dimensions)
└── stage_runners.py
    └── pipeline_utils.py (for run_command)
```

## Implementation Steps

1. **Create `pipeline_utils.py`**
   - Extract utility functions
   - Add `__all__` exports
   - Update imports in `run_pipeline.py`

2. **Create `workflow_utils.py`**
   - Extract workflow manipulation functions
   - Import `get_image_dimensions` from `pipeline_utils`

3. **Create `stage_runners.py`**
   - Extract external script wrappers
   - Import `run_command` from `pipeline_utils`

4. **Trim `run_pipeline.py`**
   - Update imports to use new modules
   - Remove moved functions
   - Result: ~500 lines of pure orchestration

5. **Verify & Test**
   - Run existing integration tests
   - Test `--list-stages`, `--help`
   - Run a simple pipeline (ingest + depth)

## Optional: Further Trimming

If still too long after split, consider:

- **Extract stage blocks** from `run_pipeline()` into separate functions like `_run_depth_stage()`, `_run_roto_stage()` - each stage is ~30-60 lines
- **Move CLI parsing** to `cli.py` if argparse section grows

## File Size Targets

| Module | Target Lines | Content |
|--------|-------------|---------|
| `pipeline_utils.py` | ~180 | FFmpeg/subprocess utilities |
| `workflow_utils.py` | ~200 | Workflow JSON manipulation |
| `stage_runners.py` | ~150 | External script wrappers |
| `run_pipeline.py` | ~500 | Orchestration + CLI |
| **Total** | ~1030 | ~500 lines saved via deduplication/cleanup |

---

**Priority:** Medium (code quality, maintainability)
**Risk:** Low (pure refactor, no behavior change)
**Testing:** Existing integration tests cover all paths

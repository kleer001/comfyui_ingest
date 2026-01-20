# Pipeline Orchestrator Documentation

Automated end-to-end VFX processing pipeline.

**Quick links**: [Stages](stages.md) | [Troubleshooting](troubleshooting.md) | [Installation](install_wizard.md)

---

## Overview

`run_pipeline.py` orchestrates the entire VFX pipeline from a single command:

| Stage | Purpose | Details |
|-------|---------|---------|
| **ingest** | Extract frames from video | [docs](stages.md#ingest---frame-extraction) |
| **depth** | Depth maps (Depth-Anything-V3) | [docs](stages.md#depth---depth-analysis) |
| **roto** | Segmentation masks (SAM3) | [docs](stages.md#roto---segmentation) |
| **matanyone** | Matte refinement for people | [docs](stages.md#matanyone---video-matting) |
| **cleanplate** | Object removal (ProPainter) | [docs](stages.md#cleanplate---clean-plate-generation) |
| **colmap** | Camera tracking & 3D reconstruction | [docs](stages.md#colmap---camera-tracking) |
| **mocap** | Human motion capture (WHAM + ECON) | [docs](stages.md#mocap---motion-capture) |
| **gsir** | PBR material decomposition | [docs](stages.md#gsir---material-decomposition) |
| **camera** | Export camera to Alembic | [docs](stages.md#camera---camera-export) |

---

## Quick Start

### Process Full Pipeline

```bash
python scripts/run_pipeline.py /path/to/footage.mp4 -n "MyShot"
```

### Process Specific Stages

```bash
python scripts/run_pipeline.py footage.mp4 -s depth,roto,cleanplate
```

### List Available Stages

```bash
python scripts/run_pipeline.py footage.mp4 -l
```

---

## Command Line Options

### Short Options

```bash
-n NAME            # Project name
-p DIR             # Projects directory
-s STAGES          # Stages to run (comma-separated)
-c URL             # ComfyUI API URL
-f FPS             # Override frame rate
-e                 # Skip existing output
-l                 # List available stages

# COLMAP options
-q QUALITY         # Quality (low/medium/high/slow)
-d                 # Dense reconstruction
-m                 # Generate mesh
-M                 # Disable masks

# GS-IR options
-i ITERATIONS      # Training iterations
-g PATH            # GS-IR installation path
```

### Long Options

```bash
--name NAME                  # Project name
--projects-dir DIR           # Projects directory (default: ../vfx_projects)
--stages STAGES              # Stages to run (comma-separated or "all")
--comfyui-url URL           # ComfyUI API URL (default: http://127.0.0.1:8188)
--fps FPS                    # Override frame rate (default: auto-detect)
--skip-existing             # Skip stages with existing output
--list-stages               # List available stages and exit

# Roto/Segmentation options
--prompt TEXT               # Segmentation prompt (default: 'person')
                            # Comma-separated for multiple: 'person,bag,ball'
--separate-instances        # Separate multi-person masks into individual
                            # instance directories (person_0/, person_1/, etc.)

# COLMAP options
--colmap-quality QUALITY    # Quality preset: low, medium, high, slow
                            # 'slow' is for minimal camera motion footage
--colmap-dense             # Run dense reconstruction (slower)
--colmap-mesh              # Generate mesh from dense reconstruction
--colmap-no-masks          # Disable automatic use of segmentation masks

# GS-IR options
--gsir-iterations N        # Total training iterations (default: 35000)
--gsir-path PATH           # Path to GS-IR installation (default: auto-detect)

# Automation options
--no-auto-comfyui          # Don't auto-start ComfyUI (assume already running)
--auto-movie               # Generate preview MP4s from completed image sequences
--no-overwrite             # Keep existing output files instead of clearing them
```

---

## Usage Examples

### Basic: Depth + Camera Export

```bash
python scripts/run_pipeline.py footage.mp4 -n "Shot01" -s depth,camera
```

Fastest workflow for basic VFX matchmoving.

### Full Segmentation Pipeline

```bash
python scripts/run_pipeline.py footage.mp4 -s ingest,depth,roto,matanyone,cleanplate
```

Complete pipeline with person matte refinement for clean plates.

### Multi-Object Segmentation

```bash
python scripts/run_pipeline.py footage.mp4 -s roto --prompt "person,bag,ball"
```

Creates separate mask directories: `roto/person/`, `roto/bag/`, `roto/ball/`

### Multi-Person Instance Separation

```bash
python scripts/run_pipeline.py footage.mp4 -s roto --prompt "person" --separate-instances
```

Splits multiple people into `roto/person_0/`, `roto/person_1/`, etc.

### High-Quality COLMAP with Dense Reconstruction

```bash
python scripts/run_pipeline.py footage.mp4 -s colmap,camera -q high -d -m
```

### Resume After Interruption

```bash
python scripts/run_pipeline.py footage.mp4 -s all -e
```

The `-e` flag skips stages that already have output.

### Generate Preview Movies

```bash
python scripts/run_pipeline.py footage.mp4 -s depth,roto,cleanplate --auto-movie
```

Creates `preview/depth.mp4`, `preview/roto.mp4`, `preview/cleanplate.mp4`.

---

## Project Structure

Pipeline creates this directory structure:

```
../vfx_projects/MyShot/
├── source/
│   └── frames/              # Extracted frames (frame_0001.png, ...)
├── workflows/               # ComfyUI workflow copies
├── depth/                   # Depth maps
├── roto/                    # Segmentation masks (per-prompt subdirs)
│   ├── person/
│   ├── bag/
│   └── combined/            # Consolidated masks (for cleanplate)
├── matte/                   # MatAnyone refined mattes
├── cleanplate/              # Clean plates
├── colmap/
│   ├── sparse/0/            # Sparse 3D model
│   ├── dense/               # Dense point cloud (optional)
│   └── meshed/              # Mesh (optional)
├── mocap/
│   ├── wham/                # Pose estimates
│   └── econ/                # 3D reconstructions
├── gsir/
│   ├── model/               # Checkpoints
│   └── materials/           # PBR textures (albedo, roughness, metallic)
├── camera/
│   ├── extrinsics.json      # Camera transforms
│   ├── intrinsics.json      # Camera parameters
│   └── camera.abc           # Alembic export
└── preview/                 # Preview movies (if --auto-movie)
```

---

## ComfyUI Integration

Pipeline auto-starts ComfyUI for stages that need it (depth, roto, matanyone, cleanplate).

### Manual ComfyUI Control

```bash
# Disable auto-start
python scripts/run_pipeline.py footage.mp4 -s depth --no-auto-comfyui

# Custom URL (remote server)
python scripts/run_pipeline.py footage.mp4 -c http://192.168.1.100:8188
```

### Workflow Customization

Workflows are copied to `MyShot/workflows/` on first run. Edit these per-shot:

```
workflow_templates/01_analysis.json → MyShot/workflows/01_analysis.json
```

---

## Advanced Usage

### Run Individual Scripts

```bash
python scripts/run_colmap.py MyShot -q high
python scripts/run_mocap.py MyShot
python scripts/export_camera.py MyShot --fps 24
```

### Batch Processing

```bash
for video in footage/*.mp4; do
    name=$(basename "$video" .mp4)
    python scripts/run_pipeline.py "$video" -n "$name" -s all -e
done
```

### DCC Integration

Pipeline outputs work with:

| Application | Camera | Point Cloud | Mesh |
|-------------|--------|-------------|------|
| Maya | .abc | - | .ply |
| Houdini | .abc | .ply | .ply |
| Blender | .abc/.fbx | .ply | .ply |
| Nuke | convert from .abc | - | - |

---

## Related Documentation

- **[Stages](stages.md)** - Detailed documentation for each pipeline stage
- **[Troubleshooting](troubleshooting.md)** - Common issues, solutions, and performance tips
- **[Installation](install_wizard.md)** - Set up components before running pipeline
- **[Janitor](janitor.md)** - Maintain and update installed components
- **[Component Scripts](component_scripts.md)** - Individual script documentation

---

## Quick Reference

```bash
# Full pipeline
python scripts/run_pipeline.py footage.mp4 -n "Shot" -s all

# Common workflows
python scripts/run_pipeline.py footage.mp4 -s depth,camera              # Matchmove only
python scripts/run_pipeline.py footage.mp4 -s roto,cleanplate           # Object removal
python scripts/run_pipeline.py footage.mp4 -s colmap,mocap              # Motion capture

# Resume/skip existing
python scripts/run_pipeline.py footage.mp4 -s all -e

# List stages
python scripts/run_pipeline.py footage.mp4 -l
```

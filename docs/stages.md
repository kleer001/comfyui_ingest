# Pipeline Stages Reference

Detailed documentation for each stage in the VFX pipeline.

**Quick links**: [run_pipeline.py](run_pipeline.md) | [Troubleshooting](troubleshooting.md) | [Installation](install_wizard.md)

---

## Stage Overview

| Stage | Purpose | Input | Output |
|-------|---------|-------|--------|
| [ingest](#ingest---frame-extraction) | Extract frames | Video file | PNG sequence |
| [depth](#depth---depth-analysis) | Depth maps | Frames | Depth PNGs + camera JSON |
| [roto](#roto---segmentation) | Segmentation | Frames | Binary masks |
| [matanyone](#matanyone---video-matting) | Matte refinement | Person masks | Alpha mattes |
| [cleanplate](#cleanplate---clean-plate-generation) | Object removal | Frames + masks | Clean plates |
| [colmap](#colmap---camera-tracking) | Camera tracking | Frames | 3D reconstruction |
| [mocap](#mocap---motion-capture) | Motion capture | Frames + camera | Pose + mesh |
| [gsir](#gsir---material-decomposition) | PBR materials | COLMAP model | Albedo, roughness, metallic |
| [camera](#camera---camera-export) | Export camera | Camera JSON | Alembic/FBX |

---

## ingest - Frame Extraction

Extracts frames from video file using ffmpeg.

**Input**: Movie file (mp4, mov, avi, mkv, webm, mxf)
**Output**: `source/frames/frame_0001.png, frame_0002.png, ...`

**Options**:
- `--fps` - Override frame rate (default: auto-detect from video metadata)

**Example**:
```bash
python scripts/run_pipeline.py footage.mp4 -s ingest -f 24
```

**Frame Numbering**:
- Starts at 0001 (due to ComfyUI and WHAM constraints)
- Zero-padded 4 digits (0001, 0002, ..., 9999)

---

## depth - Depth Analysis

Generates depth maps using Depth-Anything-V3.

**Input**: `source/frames/*.png`
**Output**: `depth/*.png`, `camera/extrinsics.json`, `camera/intrinsics.json`

**Requirements**:
- ComfyUI server running (see [ComfyUI docs](comfyui.md))
- DepthAnythingV3 custom node installed

**Workflow**: `01_analysis.json`

**Example**:
```bash
python scripts/run_pipeline.py footage.mp4 -s depth
```

**Notes**:
- Also generates camera data from depth (useful when COLMAP fails)
- ~7GB VRAM required

---

## roto - Segmentation

Creates segmentation masks using SAM3 (Segment Anything Model 3).

**Input**: `source/frames/*.png`
**Output**: `roto/<prompt>/*.png` (binary masks in per-prompt subdirectories)

**Requirements**:
- ComfyUI server running
- SAM3 custom node installed (~3.2GB model, auto-downloads)

**Workflow**: `02_segmentation.json`

### Multi-Prompt Support

Segment multiple objects in a single run:

```bash
python scripts/run_pipeline.py footage.mp4 -s roto --prompt "person,bag,backpack"
```

Each prompt creates its own subdirectory:
```
roto/
├── person/     # Person masks
├── bag/        # Bag masks
└── backpack/   # Backpack masks
```

### Instance Separation

When multiple people are in frame, SAM3 may combine them into a single mask. Use `--separate-instances` to split them:

```bash
python scripts/run_pipeline.py footage.mp4 -s roto --prompt "person" --separate-instances
```

Creates separate directories for each detected person:
```
roto/
├── person_0/     # First person's masks
├── person_1/     # Second person's masks
└── person_2/     # Third person's masks
```

**Use Cases**:
- Object removal (clean plates)
- Selective color grading
- COLMAP masking (improves camera tracking)
- Individual actor extraction
- Per-person motion capture

---

## matanyone - Video Matting

Refines person segmentation masks into clean alpha mattes using MatAnyone.

**Input**: `roto/person/*.png` (or any subdirectory containing "person" in its name)
**Output**: `matte/<person_dir>/*.png` (refined alpha mattes)

**Requirements**:
- ComfyUI server running
- ComfyUI-MatAnyone custom node installed
- MatAnyone model checkpoint (~450MB)
- **9GB+ VRAM** (NVIDIA GPU required)

**Workflow**: `04_matanyone.json`

### What It Does

- Takes rough SAM3 person masks as input
- Produces clean alpha mattes with proper edge detail (hair, clothing edges)
- Uses temporal consistency for stable results across frames
- Combines multiple person mattes into `roto/combined/` for cleanplate

### Limitations

- **Human-focused only**: MatAnyone is trained specifically on people. Non-human objects (cars, bags, etc.) will not benefit from this refinement.
- Automatically skipped if no person-related masks are found in `roto/`
- Automatically skipped if workflow file is not present

**Example**:
```bash
python scripts/run_pipeline.py footage.mp4 -s ingest,roto,matanyone,cleanplate
```

---

## cleanplate - Clean Plate Generation

Generates clean plates by removing objects from segmented areas using ProPainter.

**Input**: `source/frames/*.png`, `roto/*/*.png` (mask subdirectories), optionally `matte/*.png`
**Output**: `cleanplate/*.png`, `roto/combined_*.png` (consolidated masks)

**Requirements**:
- ComfyUI server running
- Segmentation masks from `roto` stage
- ~6GB VRAM

**Workflow**: `03_cleanplate.json`

### Mask Consolidation

Before running inpainting, cleanplate consolidates all masks:

1. Collects masks from all `roto/` subdirectories
2. If MatAnyone refined mattes exist in `matte/`, substitutes them for person masks
3. OR-combines all mask sources into `roto/combined_*.png`

This ensures the inpainting receives a single unified mask covering all dynamic regions.

---

## colmap - Camera Tracking

COLMAP Structure-from-Motion reconstruction.

**Input**: `source/frames/*.png`, optional: `roto/*.png` (masks)
**Output**:
- `colmap/sparse/0/` - Sparse 3D model
- `colmap/dense/` - Dense point cloud (if `--colmap-dense`)
- `colmap/meshed/` - Mesh (if `--colmap-mesh`)

**Options**:
- `-q low|medium|high|slow` - Quality preset (default: medium)
- `-d` - Run dense reconstruction
- `-m` - Generate mesh (requires `-d`)
- `-M` - Disable automatic mask usage

### Quality Presets

| Preset | Feature Extraction | Matching | Speed | Use Case |
|--------|-------------------|----------|-------|----------|
| Low | Fast | Vocab tree | Fast | Quick preview |
| Medium | Normal | Vocab tree | Medium | Default |
| High | Detailed | Exhaustive | Slow | Production |
| Slow | Detailed | Exhaustive | Slowest | Minimal camera motion |

**Example**:
```bash
# High quality with dense reconstruction
python scripts/run_pipeline.py footage.mp4 -s colmap -q high -d
```

### Mask Integration

If `roto/*.png` exists, COLMAP automatically uses masks to ignore moving objects and improve camera tracking. Disable with `-M` if masks are causing issues.

**See also**: [Troubleshooting COLMAP](troubleshooting.md#colmap-reconstruction-failed)

---

## mocap - Motion Capture

Human motion capture using WHAM + ECON.

**Input**:
- `source/frames/*.png`
- `camera/extrinsics.json` (from COLMAP or depth stage)

**Output**:
- `mocap/wham/` - WHAM pose estimates
- `mocap/econ/` - ECON 3D reconstructions
- `mocap/mesh_sequence/` - Exported mesh sequence

**Requirements**:
- WHAM, ECON installed (see [Installation](install_wizard.md))
- Camera data (run `colmap` or `depth` stage first)
- 12GB+ VRAM recommended

**Example**:
```bash
python scripts/run_pipeline.py actor_footage.mp4 -s colmap,mocap
```

### Pipeline

1. **WHAM** extracts pose from video (world-grounded motion)
2. **ECON** reconstructs detailed 3D clothed human with SMPL-X compatibility
3. **Texture projection** (optional, use `--skip-texture` to disable)

**See also**: [Troubleshooting Mocap](troubleshooting.md#motion-capture-requires-camera-data)

---

## gsir - Material Decomposition

GS-IR (Gaussian Splatting Inverse Rendering) for PBR material extraction.

**Input**: `colmap/sparse/0/` (COLMAP sparse model)
**Output**:
- `gsir/model/chkpnt{N}.pth` - Trained model checkpoints
- `gsir/materials/` - Extracted PBR textures (albedo, roughness, metallic)

**Options**:
- `-i ITERATIONS` - Total training iterations (default: 35000)
- `-g PATH` - Path to GS-IR installation

**Example**:
```bash
python scripts/run_pipeline.py footage.mp4 -s colmap,gsir -i 50000
```

### Training Time

| Iterations | Time | Quality |
|------------|------|---------|
| 30k | ~30 min | Quick preview |
| 35k | ~40 min | Default |
| 50k | ~60 min | High quality |

---

## camera - Camera Export

Export camera data to Alembic format for use in DCCs (Maya, Houdini, Blender).

**Input**: `camera/extrinsics.json`, `camera/intrinsics.json`
**Output**:
- `camera/camera.abc` - Alembic camera export
- `camera/camera.fbx` - FBX camera export (if available)

**Example**:
```bash
python scripts/run_pipeline.py footage.mp4 -s depth,camera
```

### DCC Compatibility

| Application | Import Method |
|-------------|---------------|
| Maya | File → Import → Alembic |
| Houdini | Alembic SOP |
| Blender | File → Import → Alembic |
| Nuke | ReadGeo (convert from ABC) |

---

## Related Documentation

- **[run_pipeline.py](run_pipeline.md)** - Main pipeline orchestrator
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Installation](install_wizard.md)** - Component installation
- **[Project Structure](run_pipeline.md#project-structure)** - Output directory layout

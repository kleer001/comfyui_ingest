# Troubleshooting & Performance

Common issues, solutions, and performance optimization tips.

**Quick links**: [run_pipeline.py](run_pipeline.md) | [Stages](stages.md) | [Installation](install_wizard.md)

---

## Quick Diagnostics

```bash
# Check installation health
python scripts/janitor.py -H

# Verify ComfyUI is running
curl http://127.0.0.1:8188/system_stats

# Check GPU memory
nvidia-smi

# View project logs
ls -lh MyShot/*.log
```

---

## Common Errors

### ComfyUI Not Running

**Symptom**: `ConnectionError: Cannot connect to ComfyUI at http://127.0.0.1:8188`

**Solution**:
```bash
cd .vfx_pipeline/ComfyUI
python main.py --listen
```

Or use auto-start (default behavior):
```bash
python scripts/run_pipeline.py footage.mp4 -s depth
# ComfyUI starts automatically
```

To disable auto-start:
```bash
python scripts/run_pipeline.py footage.mp4 -s depth --no-auto-comfyui
```

**Verify server**:
```bash
curl http://127.0.0.1:8188/system_stats
```

---

### Workflow Not Found

**Symptom**: `Workflow not found: workflows/01_analysis.json`

**Cause**: Pipeline copies workflows from `workflow_templates/` to project directory on first run.

**Solutions**:
1. Check `workflow_templates/` exists in repository root
2. Manually copy workflows:
   ```bash
   cp workflow_templates/*.json MyShot/workflows/
   ```
3. Re-run with `ingest` stage to trigger setup:
   ```bash
   python scripts/run_pipeline.py footage.mp4 -s ingest,depth
   ```

---

### COLMAP Reconstruction Failed

**Symptom**: `COLMAP reconstruction failed` or empty `colmap/sparse/0/`

**Common causes and solutions**:

#### Insufficient Features
- Use higher quality: `-q high`
- Ensure footage has trackable features (texture, edges)
- Avoid pure white/black/smooth surfaces

#### Moving Objects Confusing Tracker
- Run `roto` stage first to generate masks
- Pipeline automatically uses masks if available
- Or explicitly: `python scripts/run_pipeline.py footage.mp4 -s roto,colmap`

#### Too Little Camera Motion
- Use `-q slow` preset for minimal motion footage
- COLMAP needs parallax to triangulate 3D points

#### Motion Blur
- No easy fix - requires sharp frames
- Try lower resolution input
- Consider frame interpolation to get sharper frames

**Debug**:
```bash
cat MyShot/colmap.log
```

---

### Motion Capture Requires Camera Data

**Symptom**: `Skipping (camera data required - run colmap stage first)`

**Cause**: Mocap stage needs camera transforms from either COLMAP or depth stage.

**Solutions**:

```bash
# Option 1: Use COLMAP (more accurate)
python scripts/run_pipeline.py footage.mp4 -s colmap,mocap

# Option 2: Use Depth-Anything-V3 camera (faster, less accurate)
python scripts/run_pipeline.py footage.mp4 -s depth,mocap
```

**Check camera data exists**:
```bash
ls MyShot/camera/
# Should contain: extrinsics.json, intrinsics.json
```

---

### Out of Memory (GPU)

**Symptom**: `CUDA out of memory` or `RuntimeError: CUDA error`

**Solutions**:

1. **Clear GPU memory between stages** (automatic, but can force):
   ```bash
   python -c "import torch; torch.cuda.empty_cache()"
   ```

2. **Reduce batch size** in ComfyUI workflows:
   - Edit `MyShot/workflows/*.json`
   - Find batch size nodes and reduce values

3. **Process fewer frames**:
   ```bash
   # Extract subset of frames first
   ffmpeg -i footage.mp4 -vframes 100 -start_number 1 frames/frame_%04d.png
   ```

4. **Check what's using GPU**:
   ```bash
   nvidia-smi
   # Kill other GPU processes if needed
   ```

**VRAM Requirements by Stage**:

| Stage | VRAM Required |
|-------|---------------|
| Depth (DA3) | ~7 GB |
| Roto (SAM3) | ~4 GB |
| MatAnyone | ~9 GB |
| Cleanplate | ~6 GB |
| COLMAP | ~2-4 GB |
| Mocap | ~12 GB |

---

### Stage Failed (General)

**Symptom**: `Stage failed` without specific error

**Debug steps**:

1. **Check logs**:
   ```bash
   ls -lh MyShot/*.log
   cat MyShot/depth.log  # or relevant stage
   ```

2. **Run stage in isolation**:
   ```bash
   python scripts/run_pipeline.py footage.mp4 -s depth --no-auto-comfyui
   ```

3. **Check ComfyUI console** for Python errors

4. **Verify inputs exist**:
   ```bash
   ls MyShot/source/frames/ | head
   ```

---

### SAM3 Model Download Failed

**Symptom**: `Error downloading model` or `Connection refused`

**Note**: SAM3 downloads from public `1038lab/sam3` repo - no token needed.

**Solutions**:
1. Check internet connection
2. Retry (temporary HuggingFace issues)
3. Manual download:
   ```bash
   pip install huggingface_hub
   python -c "from huggingface_hub import hf_hub_download; hf_hub_download('1038lab/sam3', 'sam3.pt', local_dir='.vfx_pipeline/ComfyUI/models/sam3')"
   ```

---

## Performance Optimization

### Parallel Processing

Some stages can run simultaneously in separate terminals:

```bash
# Terminal 1: Depth analysis
python scripts/run_pipeline.py footage.mp4 -s depth

# Terminal 2: Segmentation (independent of depth)
python scripts/run_pipeline.py footage.mp4 -s roto
```

**Stage Dependencies**:
```
ingest ─┬─► depth ──────────────────────┬─► camera
        │                               │
        ├─► roto ─► matanyone ─► cleanplate
        │
        └─► colmap ─┬─► mocap
                    └─► gsir
```

---

### Skip Existing Output

Use `-e` to avoid re-processing completed stages:

```bash
python scripts/run_pipeline.py footage.mp4 -s all -e
```

Checks for:
- Frame files in `source/frames/`
- Depth maps in `depth/`
- Masks in `roto/`
- COLMAP model in `colmap/sparse/0/`
- Camera file in `camera/camera.abc`

---

### Quality vs Speed Tradeoffs

**Fast preview** (low quality):
```bash
python scripts/run_pipeline.py footage.mp4 -s depth,colmap,camera -q low
```

**Production quality** (slow):
```bash
python scripts/run_pipeline.py footage.mp4 -s all -q high -d -m
```

**Balanced** (default):
```bash
python scripts/run_pipeline.py footage.mp4 -s all
```

---

### Disk Space Management

Pipeline generates large amounts of data:

| Stage | Size per 1000 frames |
|-------|---------------------|
| Frames (PNG) | 2-5 GB |
| Depth | 1-2 GB |
| Roto | 500 MB |
| Cleanplate | 2-5 GB |
| COLMAP sparse | 50-200 MB |
| COLMAP dense | 5-20 GB |
| Mocap | 500 MB - 2 GB |
| GS-IR | 2-5 GB |

**Total for full pipeline**: 15-40 GB per shot

**Clean up intermediate data**:
```bash
# Keep only final outputs
rm -rf MyShot/depth MyShot/roto

# Or keep depth but remove roto
rm -rf MyShot/roto
```

**Check disk usage**:
```bash
du -sh MyShot/*
```

---

### GPU Memory Management

The pipeline automatically clears GPU memory between stages. If you still have issues:

1. **Restart ComfyUI** between heavy stages
2. **Use `--no-auto-comfyui`** and manually restart ComfyUI
3. **Process in batches**:
   ```bash
   # First half
   python scripts/run_pipeline.py footage.mp4 -s depth
   # Restart ComfyUI
   # Second half
   python scripts/run_pipeline.py footage.mp4 -s roto
   ```

---

## Advanced Debugging

### Enable Verbose Logging

```bash
# Set environment variable
export VFX_DEBUG=1
python scripts/run_pipeline.py footage.mp4 -s depth
```

### Check ComfyUI Workflow Execution

1. Open ComfyUI UI: http://127.0.0.1:8188
2. Load workflow from `MyShot/workflows/`
3. Run manually to see node-by-node execution
4. Check for red (error) nodes

### Validate Installation

```bash
# Full health check
python scripts/janitor.py -H

# Detailed report
python scripts/janitor.py -R

# Attempt repairs
python scripts/janitor.py -r -y
```

---

## Getting Help

Before reporting issues:

1. Run `python scripts/janitor.py -H` and include output
2. Include full error message
3. Include system info:
   ```bash
   uname -a
   python --version
   nvidia-smi
   ```

**Report issues**: [GitHub Issues](https://github.com/kleer001/comfyui_ingest/issues)

---

## Related Documentation

- **[run_pipeline.py](run_pipeline.md)** - Main pipeline orchestrator
- **[Stages](stages.md)** - Detailed stage documentation
- **[Installation](install_wizard.md)** - Component installation
- **[Janitor](janitor.md)** - Maintenance and repairs

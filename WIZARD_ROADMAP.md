# Installation Wizard Enhancement Roadmap

## Overview
Comprehensive quality-of-life improvements to make the installation wizard production-ready with automatic environment management, checkpoint downloading, progress tracking, validation, and recovery capabilities.

## Architecture Design

### Phase 1: Foundation (Conda + State Management)
**Goal**: Automatic conda environment handling and installation state tracking

#### 1.1 Conda Environment Manager
```python
class CondaEnvironmentManager:
    - detect_conda() -> bool
    - get_current_env() -> Optional[str]
    - create_environment(name: str, python_version: str) -> bool
    - activate_environment(name: str) -> str  # Returns activation command
    - install_package_conda(package: str) -> bool
    - install_package_pip(package: str) -> bool
```

**Features**:
- Auto-detect conda installation
- Check if in conda environment
- Create dedicated `vfx-pipeline` environment if needed
- Handle conda-first packages (PyTorch, CUDA)
- Generate activation scripts

**Decision Tree**:
```
Is conda installed?
├─ No → Error: "Please install conda first"
└─ Yes → Is user in conda env?
    ├─ Yes (base) → Create vfx-pipeline env
    ├─ Yes (other) → Warn, recommend vfx-pipeline, ask to continue
    └─ No → Error: "conda not in PATH"
```

#### 1.2 Installation State Manager
```python
class InstallationStateManager:
    state_file: Path  # ~/.vfx_pipeline/install_state.json

    - load_state() -> Dict
    - save_state(state: Dict)
    - mark_component_started(comp_id: str)
    - mark_component_completed(comp_id: str)
    - mark_component_failed(comp_id: str, error: str)
    - get_incomplete_components() -> List[str]
    - can_resume() -> bool
```

**State Schema**:
```json
{
  "version": "1.0",
  "environment": "vfx-pipeline",
  "timestamp": "2026-01-11T10:30:00",
  "components": {
    "core": {"status": "completed", "timestamp": "..."},
    "pytorch": {"status": "in_progress", "timestamp": "..."},
    "wham": {"status": "failed", "error": "...", "timestamp": "..."}
  },
  "checkpoints": {
    "wham": {"downloaded": false, "path": null},
    "tava": {"downloaded": true, "path": "~/.vfx_pipeline/tava/checkpoints"}
  }
}
```

### Phase 2: Download Management
**Goal**: Automatic checkpoint downloading with progress tracking

#### 2.1 Checkpoint Downloader
```python
class CheckpointDownloader:
    - download_file(url: str, dest: Path, show_progress: bool) -> bool
    - verify_checksum(file: Path, expected: str) -> bool
    - download_wham_checkpoints() -> bool
    - download_tava_checkpoints() -> bool
    - download_econ_checkpoints() -> bool
    - download_smplx_models() -> bool  # Requires user credentials
```

**Checkpoint Metadata**:
```python
CHECKPOINTS = {
    'wham': {
        'files': [
            {
                'url': 'https://github.com/yohanshin/WHAM/releases/download/v1.0/wham_checkpoint.pth',
                'filename': 'wham_checkpoint.pth',
                'sha256': '...',
                'size_mb': 1200
            }
        ],
        'dest_dir': '~/.vfx_pipeline/WHAM/checkpoints'
    },
    # ... more
}
```

**Notes**:
- SMPL-X requires registration → guide user through manual download OR implement OAuth
- Use `requests` with streaming for large files
- Resume partial downloads with `Range` headers

#### 2.2 Progress Bar Manager (ncurses)
```python
class ProgressBarManager:
    using_curses: bool

    - init_screen()
    - cleanup_screen()
    - create_progress_bar(label: str, total: int) -> ProgressBar
    - update_progress(bar_id: int, current: int)
    - add_log_line(text: str)
```

**Features**:
- Multi-line progress bars (one per component)
- Live log output below progress bars
- Fallback to simple print if terminal doesn't support curses
- Handle terminal resize

**Visual Layout**:
```
╔════════════════════════════════════════════════════════╗
║  VFX Pipeline Installation                             ║
╠════════════════════════════════════════════════════════╣
║  PyTorch          [████████████--------]  67%  2.1GB   ║
║  WHAM Checkpoint  [████----------------]  25%  300MB   ║
║                                                        ║
║  Log:                                                  ║
║  → Installing PyTorch with CUDA support...             ║
║  → Downloading WHAM checkpoint from GitHub...          ║
╚════════════════════════════════════════════════════════╝
```

### Phase 3: Validation & Configuration
**Goal**: Verify installation and generate config files

#### 3.1 Post-Install Validator
```python
class InstallationValidator:
    - validate_python_imports() -> Dict[str, bool]
    - validate_checkpoint_files() -> Dict[str, bool]
    - validate_smplx_models() -> bool
    - run_smoke_tests() -> Dict[str, str]  # Returns test results
    - generate_validation_report() -> str
```

**Smoke Tests**:
```python
def test_pytorch_cuda():
    import torch
    return torch.cuda.is_available()

def test_wham_load():
    # Try loading WHAM model
    pass

def test_colmap():
    # Run colmap --version
    pass
```

#### 3.2 Configuration Generator
```python
class ConfigurationGenerator:
    - generate_env_config() -> Dict
    - write_config_file(path: Path)
    - generate_activation_script() -> str
    - create_project_template(name: str, path: Path)
```

**Generated Files**:

1. `~/.vfx_pipeline/config.json`:
```json
{
  "environment": "vfx-pipeline",
  "paths": {
    "wham": "~/.vfx_pipeline/WHAM",
    "tava": "~/.vfx_pipeline/tava",
    "econ": "~/.vfx_pipeline/ECON",
    "smplx_models": "~/.smplx"
  },
  "python": "/opt/conda/envs/vfx-pipeline/bin/python",
  "version": "1.0"
}
```

2. `~/.vfx_pipeline/activate.sh`:
```bash
#!/bin/bash
# VFX Pipeline Environment Activation
conda activate vfx-pipeline
export PYTHONPATH="${PYTHONPATH}:${HOME}/.vfx_pipeline/WHAM:${HOME}/.vfx_pipeline/tava:${HOME}/.vfx_pipeline/ECON"
export WHAM_DIR="${HOME}/.vfx_pipeline/WHAM"
export TAVA_DIR="${HOME}/.vfx_pipeline/tava"
export ECON_DIR="${HOME}/.vfx_pipeline/ECON"
echo "✓ VFX Pipeline environment activated"
```

### Phase 4: Maintenance Commands
**Goal**: Update and uninstall functionality

#### 4.1 Update Manager
```python
class UpdateManager:
    - check_updates() -> Dict[str, str]  # component -> new_version
    - update_component(comp_id: str) -> bool
    - update_all() -> bool
```

Commands:
```bash
python scripts/install_wizard.py --check-updates
python scripts/install_wizard.py --update wham
python scripts/install_wizard.py --update-all
```

#### 4.2 Uninstall Manager
```python
class UninstallManager:
    - uninstall_component(comp_id: str, remove_checkpoints: bool) -> bool
    - uninstall_all(remove_env: bool) -> bool
    - clean_cache() -> float  # Returns GB freed
```

Commands:
```bash
python scripts/install_wizard.py --uninstall wham
python scripts/install_wizard.py --uninstall-all
python scripts/install_wizard.py --clean-cache
```

## Implementation Order

### Sprint 1: Foundation (Est. ~200 LOC)
1. CondaEnvironmentManager class
2. InstallationStateManager class
3. Integrate with existing wizard
4. Test: Create env, track state, resume

### Sprint 2: Downloads (Est. ~300 LOC)
1. CheckpointDownloader class
2. Define checkpoint metadata
3. Implement progress tracking (simple first)
4. Test: Download WHAM checkpoint

### Sprint 3: Progress UI (Est. ~250 LOC)
1. ProgressBarManager with ncurses
2. Integrate with git clone
3. Integrate with pip install
4. Integrate with downloads
5. Test: Full install with progress bars

### Sprint 4: Validation (Est. ~200 LOC)
1. InstallationValidator class
2. Smoke tests for each component
3. Generate validation report
4. Test: Run validation on fresh install

### Sprint 5: Configuration (Est. ~150 LOC)
1. ConfigurationGenerator class
2. Generate config.json
3. Generate activate.sh
4. Test: Source activation script

### Sprint 6: Maintenance (Est. ~200 LOC)
1. UpdateManager class
2. UninstallManager class
3. Add CLI arguments
4. Test: Update, uninstall, clean

### Sprint 7: Integration & Polish (Est. ~100 LOC)
1. Wire everything together
2. Error handling improvements
3. Help text and documentation
4. End-to-end testing

**Total Estimated**: ~1,400 new lines of code

## Testing Strategy

### Unit Tests
- Mock conda commands
- Mock file downloads
- Mock git operations
- Test state persistence

### Integration Tests
- Fresh environment creation
- Resume interrupted installation
- Full install → validate → uninstall cycle
- Update existing installation

### Edge Cases
- No conda installed
- No internet connection (for downloads)
- Insufficient disk space
- Corrupted checkpoints
- Terminal without curses support
- Interrupted downloads

## Rollout Plan

1. Implement in `scripts/install_wizard_v2.py` (keep original)
2. Test thoroughly
3. Add `--experimental-wizard` flag
4. Gather feedback
5. Merge into main wizard
6. Update documentation

## Dependencies to Add

```txt
requests>=2.31.0      # For HTTP downloads
tqdm>=4.65.0          # Fallback progress bars
curses                # Built-in on Linux/Mac
hashlib               # Built-in (checksum verification)
```

## Success Criteria

- [ ] Can detect conda and create environment automatically
- [ ] Can resume interrupted installations
- [ ] Downloads all checkpoints automatically (except SMPL-X)
- [ ] Shows real-time progress with ncurses
- [ ] Validates installation with smoke tests
- [ ] Generates working activation script
- [ ] Can update individual components
- [ ] Can uninstall cleanly
- [ ] Works on fresh Ubuntu system with conda
- [ ] Complete in <15 minutes on 100Mbps connection

## Risk Mitigation

**Risk**: Checkpoint URLs change or become unavailable
- **Mitigation**: Store metadata in config, easy to update

**Risk**: ncurses not available on system
- **Mitigation**: Fallback to tqdm or simple print

**Risk**: Conda command differences across versions
- **Mitigation**: Test against conda 4.x, 23.x, 24.x

**Risk**: Network failures during large downloads
- **Mitigation**: Implement resume capability with Range headers

**Risk**: State file corruption
- **Mitigation**: Atomic writes, backup previous state

## Future Enhancements (Out of Scope)

- Docker container build
- Multi-platform support (Windows, macOS)
- GUI wizard (Electron or web-based)
- Cloud checkpoint hosting
- Automatic SMPL-X OAuth flow
- Telemetry/analytics (opt-in)

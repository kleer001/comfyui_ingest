# Installation Wizard TODOs

Extracted from OS_SUPPORT_ANALYSIS.md

## High Priority

- [ ] **Add Depth Anything V3 camera pose estimation**
  - Current depth workflow uses Video Depth Anything (VDA) which only outputs depth
  - DA3 `DepthAnythingV3_MultiView` node outputs camera extrinsics + intrinsics
  - Would enable lightweight matchmove without COLMAP for simple shots
  - Requires: ComfyUI-DepthAnythingV3 custom nodes + updated workflow

- [ ] **Implement GVHMR for improved motion capture**
  - See [GVHMR Transition Roadmap](GVHMR_TRANSITION_ROADMAP.md)
  - Replaces WHAM with more accurate world-grounded motion recovery
  - 7-10mm lower error, better camera motion handling
  - Supports COLMAP focal length input for improved accuracy

## Medium Priority

- [ ] **Add which_wizard.py decision helper script**
  - Detect platform (Linux/macOS/WSL2/Windows) and GPU
  - Recommend best wizard for user's setup
  - Show pros/cons of each option

- [ ] **Add macOS-specific guidance**
  - Homebrew installation instructions
  - Metal vs CUDA limitations explanation

- [ ] **Add Windows-specific conda instructions**
  - Chocolatey/manual install paths for dependencies

## Low Priority

- [ ] **Auto-detect Linux package manager**
  - Support apt, yum, pacman

- [ ] **Check for Homebrew on macOS and offer to install**

- [ ] **Check for Chocolatey on Windows and offer to install**

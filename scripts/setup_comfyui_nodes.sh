#!/bin/bash
# Setup ComfyUI custom nodes on host for Docker mounting
# Run this once to install the required nodes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
NODES_DIR="$REPO_ROOT/.vfx_pipeline/ComfyUI/custom_nodes"

echo "Setting up ComfyUI custom nodes in: $NODES_DIR"
mkdir -p "$NODES_DIR"
cd "$NODES_DIR"

# Required nodes for the VFX pipeline
NODES=(
    "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git"
    "https://github.com/PozzettiAndrea/ComfyUI-SAM3.git"
    "https://github.com/yuvraj108c/ComfyUI-Video-Depth-Anything.git"
    "https://github.com/daniabib/ComfyUI_ProPainter_Nodes.git"
    "https://github.com/FuouM/ComfyUI-MatAnyone.git"
)

for repo in "${NODES[@]}"; do
    name=$(basename "$repo" .git)
    if [ -d "$name" ]; then
        echo "  $name - already exists, pulling latest..."
        (cd "$name" && git pull --ff-only 2>/dev/null || echo "    (could not fast-forward)")
    else
        echo "  $name - cloning..."
        git clone --depth 1 "$repo"
    fi
done

echo ""
echo "Done! Custom nodes installed to: $NODES_DIR"
echo ""
echo "Note: Python dependencies will be installed automatically by ComfyUI"
echo "on first run, or you can use ComfyUI Manager to manage them."

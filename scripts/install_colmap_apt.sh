#!/bin/bash
#
# COLMAP Quick Installation via APT
# ==================================
# Fast installation using Ubuntu/Debian packages.
# This is the quickest option but may not have the latest features.
#
# For the latest version with all features, use install_colmap_source.sh instead.
#
# Usage:
#   ./install_colmap_apt.sh
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}  COLMAP Quick Install (APT)${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

# Detect distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo -e "Detected: ${GREEN}${PRETTY_NAME}${NC}"
else
    echo "Unknown distribution"
fi
echo ""

# Update and install
echo -e "${BLUE}[1/3] Updating package lists...${NC}"
sudo apt-get update

echo ""
echo -e "${BLUE}[2/3] Installing COLMAP and dependencies...${NC}"

# Install COLMAP and common dependencies
sudo apt-get install -y \
    colmap \
    libcgal-dev \
    libceres-dev \
    libflann-dev \
    libfreeimage-dev

echo ""
echo -e "${BLUE}[3/3] Verifying installation...${NC}"

if command -v colmap &> /dev/null; then
    echo -e "${GREEN}COLMAP installed successfully!${NC}"
    echo ""
    colmap --version 2>/dev/null || echo "Version check not supported on this build"
    echo ""

    # Check for CUDA support
    if colmap help 2>&1 | grep -q "CUDA"; then
        echo -e "CUDA support: ${GREEN}Available${NC}"
    else
        echo -e "CUDA support: ${YELLOW}Not available (CPU-only)${NC}"
        echo -e "${YELLOW}For GPU support, build from source with install_colmap_source.sh${NC}"
    fi
else
    echo -e "${YELLOW}COLMAP not found after installation${NC}"
    echo "You may need to build from source instead."
    echo "Run: ./install_colmap_source.sh"
    exit 1
fi

echo ""
echo -e "${BLUE}=======================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""
echo "Test with: colmap help"
echo ""

# Quick test with project script
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
if [ -f "${SCRIPT_DIR}/run_colmap.py" ]; then
    echo "Testing project integration..."
    python "${SCRIPT_DIR}/run_colmap.py" --check && \
        echo -e "${GREEN}Ready to use!${NC}" || \
        echo -e "${YELLOW}Check installation${NC}"
fi

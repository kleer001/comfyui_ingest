#!/bin/bash
#
# COLMAP Installation from Source
# ================================
# This script builds and installs COLMAP from source, bypassing conda's
# slow dependency solver. It installs all dependencies via apt and builds
# the latest COLMAP with full feature support.
#
# Usage:
#   ./install_colmap_source.sh [OPTIONS]
#
# Options:
#   --no-cuda      Build without CUDA/GPU support (CPU-only)
#   --prefix PATH  Install prefix (default: /usr/local)
#   --jobs N       Number of parallel build jobs (default: auto)
#   --help         Show this help message
#
# Requirements:
#   - Ubuntu 20.04+ or Debian 11+
#   - sudo access for installing dependencies
#   - ~4GB disk space for build
#   - ~20-45 minutes build time depending on hardware
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
INSTALL_PREFIX="/usr/local"
BUILD_CUDA=1
BUILD_JOBS=$(nproc 2>/dev/null || echo 4)
BUILD_DIR="/tmp/colmap_build_$$"
COLMAP_VERSION="3.9.1"  # Latest stable as of 2024

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cuda)
            BUILD_CUDA=0
            shift
            ;;
        --prefix)
            INSTALL_PREFIX="$2"
            shift 2
            ;;
        --jobs)
            BUILD_JOBS="$2"
            shift 2
            ;;
        --help|-h)
            head -30 "$0" | tail -25
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}  COLMAP Installation from Source${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""
echo -e "Install prefix: ${GREEN}${INSTALL_PREFIX}${NC}"
echo -e "Build jobs: ${GREEN}${BUILD_JOBS}${NC}"
echo -e "CUDA support: ${GREEN}$([ $BUILD_CUDA -eq 1 ] && echo "Yes (if available)" || echo "No")${NC}"
echo -e "Build directory: ${GREEN}${BUILD_DIR}${NC}"
echo ""

# Check for CUDA
CUDA_PATH=""
if [ $BUILD_CUDA -eq 1 ]; then
    # Check common CUDA locations
    for cuda_dir in /usr/local/cuda /usr/local/cuda-12 /usr/local/cuda-11 /usr/local/cuda-12.* /usr/local/cuda-11.*; do
        if [ -f "$cuda_dir/bin/nvcc" ]; then
            CUDA_PATH="$cuda_dir"
            break
        fi
    done

    if [ -z "$CUDA_PATH" ]; then
        echo -e "${YELLOW}Warning: CUDA not found. Building CPU-only version.${NC}"
        echo -e "${YELLOW}To enable GPU support, install CUDA toolkit first:${NC}"
        echo -e "${YELLOW}  https://developer.nvidia.com/cuda-downloads${NC}"
        echo ""
        BUILD_CUDA=0
    else
        echo -e "${GREEN}Found CUDA at: ${CUDA_PATH}${NC}"
        export PATH="${CUDA_PATH}/bin:$PATH"
        export LD_LIBRARY_PATH="${CUDA_PATH}/lib64:$LD_LIBRARY_PATH"
    fi
fi

# Function to print step headers
step() {
    echo ""
    echo -e "${BLUE}[STEP] $1${NC}"
    echo "----------------------------------------"
}

# Function to check if command exists
check_cmd() {
    command -v "$1" >/dev/null 2>&1
}

# Cleanup on exit
cleanup() {
    if [ -d "$BUILD_DIR" ]; then
        echo -e "\n${YELLOW}Cleaning up build directory...${NC}"
        rm -rf "$BUILD_DIR"
    fi
}
trap cleanup EXIT

########################################
# Step 1: Install system dependencies
########################################
step "Installing system dependencies"

# Update package lists
sudo apt-get update

# Core build tools
sudo apt-get install -y \
    git \
    cmake \
    ninja-build \
    build-essential \
    pkg-config

# COLMAP dependencies
sudo apt-get install -y \
    libboost-all-dev \
    libeigen3-dev \
    libflann-dev \
    libfreeimage-dev \
    libmetis-dev \
    libgoogle-glog-dev \
    libgflags-dev \
    libsqlite3-dev \
    libglew-dev \
    qtbase5-dev \
    libqt5opengl5-dev \
    libcgal-dev \
    libceres-dev

# Additional for CUDA builds
if [ $BUILD_CUDA -eq 1 ]; then
    sudo apt-get install -y \
        libcudnn8 libcudnn8-dev 2>/dev/null || true
fi

echo -e "${GREEN}Dependencies installed successfully${NC}"

########################################
# Step 2: Create build directory
########################################
step "Setting up build directory"

mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

echo -e "${GREEN}Build directory ready: ${BUILD_DIR}${NC}"

########################################
# Step 3: Clone COLMAP source
########################################
step "Cloning COLMAP source"

if [ -d "colmap" ]; then
    rm -rf colmap
fi

git clone --branch ${COLMAP_VERSION} --depth 1 https://github.com/colmap/colmap.git

echo -e "${GREEN}COLMAP ${COLMAP_VERSION} cloned successfully${NC}"

########################################
# Step 4: Configure COLMAP build
########################################
step "Configuring COLMAP build"

cd colmap
mkdir -p build
cd build

# Build options
CMAKE_OPTS=(
    -GNinja
    -DCMAKE_BUILD_TYPE=Release
    -DCMAKE_INSTALL_PREFIX="${INSTALL_PREFIX}"
)

# CUDA options
if [ $BUILD_CUDA -eq 1 ]; then
    CMAKE_OPTS+=(
        -DCUDA_ENABLED=ON
        -DCMAKE_CUDA_ARCHITECTURES="native"
    )
    if [ -n "$CUDA_PATH" ]; then
        CMAKE_OPTS+=(-DCUDA_TOOLKIT_ROOT_DIR="${CUDA_PATH}")
    fi
    echo -e "${GREEN}Configuring with CUDA support${NC}"
else
    CMAKE_OPTS+=(-DCUDA_ENABLED=OFF)
    echo -e "${YELLOW}Configuring without CUDA (CPU-only)${NC}"
fi

# Run cmake
cmake "${CMAKE_OPTS[@]}" ..

echo -e "${GREEN}Configuration complete${NC}"

########################################
# Step 5: Build COLMAP
########################################
step "Building COLMAP (this may take 15-30 minutes)"

# Start time
START_TIME=$(date +%s)

ninja -j${BUILD_JOBS}

# End time
END_TIME=$(date +%s)
BUILD_TIME=$((END_TIME - START_TIME))
BUILD_MINUTES=$((BUILD_TIME / 60))
BUILD_SECONDS=$((BUILD_TIME % 60))

echo -e "${GREEN}Build complete in ${BUILD_MINUTES}m ${BUILD_SECONDS}s${NC}"

########################################
# Step 6: Install COLMAP
########################################
step "Installing COLMAP to ${INSTALL_PREFIX}"

sudo ninja install

# Update library cache
sudo ldconfig

echo -e "${GREEN}COLMAP installed successfully${NC}"

########################################
# Step 7: Verify installation
########################################
step "Verifying installation"

# Check if colmap is in PATH
if check_cmd colmap; then
    echo -e "${GREEN}COLMAP is available in PATH${NC}"
    colmap --version || true
else
    echo -e "${YELLOW}COLMAP installed but not in PATH${NC}"
    echo -e "Add to your shell profile: export PATH=\"${INSTALL_PREFIX}/bin:\$PATH\""

    # Try to run from full path
    if [ -x "${INSTALL_PREFIX}/bin/colmap" ]; then
        echo ""
        "${INSTALL_PREFIX}/bin/colmap" --version || true
    fi
fi

# Quick functionality test
echo ""
echo "Testing COLMAP help command..."
if colmap help 2>/dev/null | head -5; then
    echo -e "${GREEN}COLMAP is working correctly${NC}"
else
    echo -e "${YELLOW}COLMAP installed but may need PATH update${NC}"
fi

########################################
# Summary
########################################
echo ""
echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}  Installation Complete!${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""
echo -e "COLMAP version: ${GREEN}${COLMAP_VERSION}${NC}"
echo -e "Install location: ${GREEN}${INSTALL_PREFIX}${NC}"
echo -e "CUDA support: ${GREEN}$([ $BUILD_CUDA -eq 1 ] && echo "Enabled" || echo "Disabled (CPU-only)")${NC}"
echo ""
echo -e "To verify, run: ${GREEN}colmap --version${NC}"
echo ""

if [ "$INSTALL_PREFIX" != "/usr/local" ]; then
    echo -e "${YELLOW}Note: Add to your PATH if needed:${NC}"
    echo -e "  export PATH=\"${INSTALL_PREFIX}/bin:\$PATH\""
    echo ""
fi

# Test with project's run_colmap.py
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
if [ -f "${SCRIPT_DIR}/run_colmap.py" ]; then
    echo "Testing with project's run_colmap.py..."
    python "${SCRIPT_DIR}/run_colmap.py" --check && \
        echo -e "${GREEN}Project integration verified!${NC}" || \
        echo -e "${YELLOW}Project check failed - verify PATH settings${NC}"
fi

echo ""
echo -e "${GREEN}Done!${NC}"

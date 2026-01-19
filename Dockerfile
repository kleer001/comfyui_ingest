# VFX Ingest Platform - Docker Image
# Multi-stage build for optimized layer caching

# Stage 1: Build COLMAP from source with CUDA support using vcpkg
# Use devel image for nvcc compiler
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04 AS colmap-builder

ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies and vcpkg prerequisites
RUN apt-get update && apt-get install -y \
    git \
    cmake \
    ninja-build \
    build-essential \
    pkg-config \
    curl \
    zip \
    unzip \
    tar \
    autoconf \
    automake \
    libtool \
    python3 \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    libxrandr-dev \
    libxinerama-dev \
    libxcursor-dev \
    libxi-dev \
    && rm -rf /var/lib/apt/lists/*

# Clone vcpkg and bootstrap
WORKDIR /opt
RUN git clone https://github.com/Microsoft/vcpkg.git && \
    cd vcpkg && \
    ./bootstrap-vcpkg.sh

# Install COLMAP dependencies via vcpkg (static linking)
# This ensures FreeImage is statically linked, triggering FreeImage_Initialise()
ENV VCPKG_ROOT=/opt/vcpkg
RUN /opt/vcpkg/vcpkg install \
    freeimage \
    boost-program-options \
    boost-filesystem \
    boost-graph \
    boost-system \
    eigen3 \
    flann \
    sqlite3 \
    ceres[suitesparse] \
    glew \
    cgal \
    glog \
    gtest \
    --triplet x64-linux

# Clone and build COLMAP with vcpkg dependencies
WORKDIR /tmp
RUN git clone https://github.com/colmap/colmap.git && \
    cd colmap && \
    git checkout 3.9.1 && \
    mkdir build && cd build && \
    cmake .. -GNinja \
        -DCMAKE_TOOLCHAIN_FILE=/opt/vcpkg/scripts/buildsystems/vcpkg.cmake \
        -DCMAKE_CUDA_ARCHITECTURES="60;70;75;80;86;89;90" \
        -DCMAKE_BUILD_TYPE=Release \
        -DCUDA_ENABLED=ON \
        -DGUI_ENABLED=OFF \
        -DCMAKE_INSTALL_PREFIX=/usr/local && \
    ninja && \
    ninja install

# Stage 2: Base image with system dependencies
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04 AS base

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Install system packages
# Note: Most COLMAP dependencies are statically linked via vcpkg
# Only system libraries needed at runtime (OpenGL, X11, etc.)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    python3.10 \
    python3-pip \
    wget \
    curl \
    xvfb \
    libgl1-mesa-glx \
    libglu1-mesa \
    libglew2.2 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy built COLMAP from builder stage
# With vcpkg static linking, all dependencies (including FreeImage) are in the binary
COPY --from=colmap-builder /usr/local/bin/colmap /usr/local/bin/colmap

# Create application directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Stage 3: Python dependencies
FROM base AS python-deps

# Copy requirements
COPY requirements.txt /tmp/

# Install Python packages
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Install PyTorch with CUDA support
RUN pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install smplx (required for mocap)
RUN pip3 install --no-cache-dir smplx

# Stage 4: ComfyUI and custom nodes
FROM python-deps AS comfyui

# Create .vfx_pipeline directory structure
RUN mkdir -p /app/.vfx_pipeline

# Clone ComfyUI and install its requirements
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /app/.vfx_pipeline/ComfyUI && \
    pip3 install --no-cache-dir -r /app/.vfx_pipeline/ComfyUI/requirements.txt

# Clone custom nodes
WORKDIR /app/.vfx_pipeline/ComfyUI/custom_nodes
RUN git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git && \
    git clone https://github.com/yuvraj108c/ComfyUI-Video-Depth-Anything.git && \
    git clone https://github.com/PozzettiAndrea/ComfyUI-SAM3.git && \
    git clone https://github.com/daniabib/ComfyUI_ProPainter_Nodes.git && \
    git clone https://github.com/FuouM/ComfyUI-MatAnyone.git

# Install custom node dependencies
RUN for dir in */; do \
        if [ -f "$dir/requirements.txt" ]; then \
            pip3 install --no-cache-dir -r "$dir/requirements.txt"; \
        fi; \
    done

# Install SAM3 GPU-accelerated NMS (speeds up video tracking 5-10x)
# Only attempt if nvcc (CUDA compiler) is available
RUN cd ComfyUI-SAM3 && \
    if command -v nvcc >/dev/null 2>&1; then \
        echo "CUDA toolkit found, installing SAM3 GPU NMS..." && \
        python3 install.py; \
    else \
        echo "Skipping SAM3 GPU NMS (nvcc not available - will use CPU fallback at runtime)"; \
    fi

WORKDIR /app

# Stage 5: Pipeline scripts
FROM comfyui AS pipeline

# Copy pipeline scripts
COPY scripts/ /app/scripts/
COPY workflow_templates/ /app/workflow_templates/

# Copy web application (if exists)
COPY web/ /app/web/

# Set Python path
ENV PYTHONPATH=/app/scripts:$PYTHONPATH

# Copy entrypoint
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Mark as container environment
ENV CONTAINER=true \
    VFX_INSTALL_DIR=/app/.vfx_pipeline \
    VFX_MODELS_DIR=/models \
    VFX_PROJECTS_DIR=/workspace/projects \
    COMFYUI_OUTPUT_DIR=/workspace \
    QT_QPA_PLATFORM=offscreen

# Expose ports
EXPOSE 8188

# Volumes
VOLUME ["/models", "/workspace"]

# Entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["--help"]

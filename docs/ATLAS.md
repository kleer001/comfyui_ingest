# 🗺️ VFX Ingest Platform - Containerization Atlas

## Overview

This atlas documents the strategic transition of the VFX Ingest Platform from a local conda-based installation to a containerized, web-accessible system optimized for artist-friendly deployment.

## Purpose

The current installation requires technical expertise:
- Conda environment setup
- COLMAP compilation/installation challenges
- Multiple model downloads with authentication
- Command-line interface

The atlas guides the transition to:
- Docker-based deployment (eliminates installation complexity)
- Web-based interface (artist-friendly GUI)
- Robust, repeatable environments

## Atlas Structure

This atlas contains three sequential roadmaps:

### 📋 [Roadmap 1: Docker Migration](ROADMAP-1-DOCKER.md)
**Status:** 🟡 In Progress
**Goal:** Replicate current CLI functionality in Docker containers

Migrate existing Python CLI workflow into Docker containers while maintaining exact feature parity. Users still interact via command-line but benefit from containerized dependencies.

**Key Outcomes:**
- Dockerfile + docker-compose configuration
- Container-aware code modifications (SOLID/DRY principles)
- Model persistence via volume mounts
- Comprehensive testing plan
- Validated feature parity with local installation

**Target Timeline:** 2-3 weeks

---

### 🔌 [Roadmap 2: API Backend](ROADMAP-2-API.md)
**Status:** ⚪ Not Started
**Goal:** Build REST/WebSocket API backend (no UI)

Create FastAPI backend with proper layered architecture (Services, Repositories, DTOs). Fully testable API that manages projects and pipeline execution.

**Key Outcomes:**
- REST API for project management
- WebSocket API for real-time progress
- Service layer with business logic
- Repository layer for data access
- Comprehensive unit + integration tests
- API fully validated before UI development

**Target Timeline:** 2-3 weeks

---

### 🌐 [Roadmap 3: Web UI Frontend](ROADMAP-3-WEB-UI.md)
**Status:** ⚪ Not Started
**Goal:** Build browser-based UI (presentation layer only)

Create artist-friendly web interface that consumes the API. Pure presentation layer with zero business logic.

**Key Outcomes:**
- HTML templates with server-side rendering
- JavaScript API client (abstraction layer)
- Real-time WebSocket updates
- Responsive CSS styling
- End-to-end UI testing
- One-click startup/shutdown

**Target Timeline:** 2-3 weeks

---

## Dependencies

```
Roadmap 1 (Docker)
    ↓
Roadmap 2 (API Backend)
    ↓
Roadmap 3 (Web UI Frontend)
```

**Critical:** Each roadmap must be **fully tested and validated** before proceeding to the next. This ensures:
- API is stable before building UI
- Backend works independently (could support CLI, mobile, etc.)
- Clear separation of concerns (backend ≠ frontend)

## Success Criteria

### Roadmap 1 Complete When:
- [ ] `docker-compose up` starts all services
- [ ] All existing pipeline stages work identically
- [ ] Models persist between container restarts
- [ ] Output files accessible from host
- [ ] COLMAP works without host installation
- [ ] Performance comparable to local installation
- [ ] Integration tests pass (all stages)
- [ ] Code follows SOLID/DRY principles

### Roadmap 2 Complete When:
- [ ] REST API endpoints operational (CRUD projects, start/stop jobs)
- [ ] WebSocket streams real-time progress
- [ ] Service layer enforces all business rules
- [ ] Repository layer abstracts data access
- [ ] Unit tests cover all services (90%+ coverage)
- [ ] Integration tests validate API contracts
- [ ] API documented with OpenAPI/Swagger
- [ ] Can be used independently (no UI required)

### Roadmap 3 Complete When:
- [ ] Web UI loads and displays dashboard
- [ ] Can create/manage projects via browser
- [ ] Real-time progress visible in UI
- [ ] Graceful shutdown with active job warnings
- [ ] Frontend has zero business logic (API calls only)
- [ ] End-to-end tests validate user flows
- [ ] One-command startup opens browser automatically
- [ ] Works on all major browsers (Chrome, Firefox, Safari, Edge)

## Current State

**Branch:** `claude/containerize-colmap-pipeline-vAOqu`

**Existing Architecture:**
- Python 3.10+ conda environment
- ComfyUI with custom nodes (SAM3, Depth Anything, MatAnyone, ProPainter)
- COLMAP for camera tracking
- FFmpeg for video processing
- Multiple ML models (~15-20GB total)
- Project-based directory structure

**Pain Points Being Addressed:**
- COLMAP installation difficulties across platforms
- Complex conda environment setup
- Command-line interface barrier for artists
- Dependency version conflicts

## Navigation

- **Start Here:** [Roadmap 1: Docker Migration](ROADMAP-1-DOCKER.md)
- **Next:** [Roadmap 2: API Backend](ROADMAP-2-API.md)
- **Finally:** [Roadmap 3: Web UI Frontend](ROADMAP-3-WEB-UI.md)

## Maintenance

These documents are living specifications and should be updated as:
- Phases complete (mark with ✅)
- Blockers encountered (document in phase notes)
- Requirements change (update success criteria)
- New dependencies discovered (add to relevant roadmap)

---

**Last Updated:** 2026-01-17
**Current Phase:** Roadmap 1, Phase 1A
**Next Milestone:** Working Dockerfile with all dependencies

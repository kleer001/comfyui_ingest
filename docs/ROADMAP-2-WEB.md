# 🌐 Roadmap 2: Web Interface

**Goal:** Add browser-based GUI layer for artist-friendly access

**Status:** ⚪ Not Started

**Dependencies:** Roadmap 1 (Docker Migration) must be complete

---

## Overview

This roadmap builds a FastAPI web application on top of the containerized pipeline, providing an intuitive browser interface for non-technical artists.

### Architecture Principles

**SOLID + DRY + Clean Architecture:**
- **Single Responsibility** - Each layer has one job
- **Separation of Concerns** - Data, Logic, UI are separate
- **Dependency Inversion** - Layers depend on abstractions, not implementations
- **DRY** - Reusable services, no duplication

### Layered Architecture

```
┌────────────────────────────────────────────┐
│   Frontend (Browser)                       │
│   - Pure presentation (HTML/CSS/JS)        │
│   - Makes API calls ONLY                   │
│   - Zero business logic                    │
└────────────────────────────────────────────┘
              ↓ HTTP/REST/WebSocket
┌────────────────────────────────────────────┐
│   API Layer (FastAPI Routers)              │
│   - Request/response handling              │
│   - Input validation (Pydantic models)     │
│   - Delegates to services                  │
│   - Returns DTOs (Data Transfer Objects)   │
└────────────────────────────────────────────┘
              ↓ Service calls
┌────────────────────────────────────────────┐
│   Service Layer (Business Logic)           │
│   - ProjectService                         │
│   - PipelineService                        │
│   - Orchestration and workflows            │
│   - Business rules                         │
└────────────────────────────────────────────┘
              ↓ Repository calls
┌────────────────────────────────────────────┐
│   Repository Layer (Data Access)           │
│   - ProjectRepository                      │
│   - JobRepository                          │
│   - Abstracts storage mechanism            │
└────────────────────────────────────────────┘
              ↓ Reads/writes
┌────────────────────────────────────────────┐
│   Storage (Filesystem/DB)                  │
│   - Project directories                    │
│   - State files (JSON)                     │
│   - (Future: PostgreSQL)                   │
└────────────────────────────────────────────┘
```

### Key Principles
- **Frontend**: Dumb UI - only renders data from API
- **API Layer**: Thin controllers - validate input, delegate to services
- **Services**: Business logic - orchestration, rules, workflows
- **Repositories**: Data access - abstract storage details
- **No cross-layer violations**: Each layer only talks to layer below

---

## Phase 2A: Foundation & Data Layer ⚪

**Goal:** Set up project structure with proper layering

### Deliverables
- `web/` directory structure with layers
- Pydantic models (DTOs and domain entities)
- Repository layer for data access
- Database/storage abstraction

### Tasks

#### Task 2A.1: Create Layered Directory Structure
**Directory Structure:**
```
web/
├── server.py                   # FastAPI app entry point
├── config.py                   # Configuration management
│
├── api/                        # API Layer (Controllers)
│   ├── __init__.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── projects.py         # Project API endpoints
│   │   ├── pipeline.py         # Pipeline API endpoints
│   │   └── system.py           # System API endpoints (health, shutdown)
│   └── dependencies.py         # FastAPI dependencies (DI)
│
├── services/                   # Service Layer (Business Logic)
│   ├── __init__.py
│   ├── project_service.py      # Project management business logic
│   ├── pipeline_service.py     # Pipeline execution orchestration
│   └── websocket_service.py    # WebSocket broadcast service
│
├── repositories/               # Repository Layer (Data Access)
│   ├── __init__.py
│   ├── base.py                 # Base repository interface
│   ├── project_repository.py   # Project data access
│   └── job_repository.py       # Pipeline job data access
│
├── models/                     # Data Models
│   ├── __init__.py
│   ├── domain.py               # Domain entities (internal)
│   └── dto.py                  # DTOs (API contracts)
│
├── ui/                         # UI Layer (Presentation)
│   ├── routers/
│   │   ├── __init__.py
│   │   └── pages.py            # HTML page routes
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── project_new.html
│   │   ├── project_view.html
│   │   └── processing.html
│   └── static/
│       ├── css/
│       │   └── styles.css
│       ├── js/
│       │   ├── api-client.js   # API client (abstraction)
│       │   ├── dashboard.js    # Dashboard UI logic
│       │   └── processing.js   # Processing UI logic
│       └── img/
│
└── utils/                      # Utilities
    ├── __init__.py
    └── websocket_manager.py    # WebSocket connection manager
```

**Success Criteria:**
- [ ] Directory structure created
- [ ] Layers clearly separated
- [ ] No cross-layer dependencies

---

#### Task 2A.2: Define Domain Models
**File:** `web/models/domain.py`

```python
"""Domain entities - internal representation."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List


class ProjectStatus(str, Enum):
    """Project status enumeration."""
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"
    UNKNOWN = "unknown"


class JobStatus(str, Enum):
    """Pipeline job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Project:
    """Project domain entity."""
    name: str
    path: Path
    status: ProjectStatus
    video_path: Optional[Path]
    stages: List[str]
    created_at: datetime
    updated_at: datetime

    @property
    def source_dir(self) -> Path:
        return self.path / "source"

    @property
    def frames_dir(self) -> Path:
        return self.path / "source" / "frames"

    @property
    def state_file(self) -> Path:
        return self.path / "project_state.json"


@dataclass
class PipelineJob:
    """Pipeline job domain entity."""
    project_name: str
    stages: List[str]
    status: JobStatus
    current_stage: Optional[str]
    progress: float  # 0.0 to 1.0
    message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]
```

**Success Criteria:**
- [ ] Domain models represent business concepts
- [ ] No framework dependencies (FastAPI, etc.)
- [ ] Type-safe with dataclasses

---

#### Task 2A.3: Define DTOs (API Contracts)
**File:** `web/models/dto.py`

```python
"""Data Transfer Objects - API contracts."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from web.models.domain import ProjectStatus, JobStatus


class ProjectDTO(BaseModel):
    """Project data for API responses."""
    name: str
    status: ProjectStatus
    video_path: Optional[str] = None
    stages: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectCreateRequest(BaseModel):
    """Request to create a new project."""
    name: str = Field(..., min_length=1, max_length=100)
    stages: List[str] = Field(default_factory=list)


class ProjectListResponse(BaseModel):
    """Response with list of projects."""
    projects: List[ProjectDTO]
    total: int


class JobDTO(BaseModel):
    """Pipeline job data for API responses."""
    project_name: str
    stages: List[str]
    status: JobStatus
    current_stage: Optional[str] = None
    progress: float = Field(ge=0.0, le=1.0)
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class JobStartRequest(BaseModel):
    """Request to start a pipeline job."""
    stages: List[str] = Field(..., min_items=1)


class JobStartResponse(BaseModel):
    """Response after starting a job."""
    status: str
    job: JobDTO


class ProgressUpdate(BaseModel):
    """Real-time progress update (WebSocket)."""
    stage: str
    progress: float = Field(ge=0.0, le=1.0)
    status: JobStatus
    message: str
```

**Success Criteria:**
- [ ] DTOs use Pydantic for validation
- [ ] Clear request/response models
- [ ] No business logic in DTOs

---

#### Task 2A.4: Implement Repository Layer
**File:** `web/repositories/base.py`

```python
"""Base repository interface."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')


class Repository(ABC, Generic[T]):
    """Base repository interface."""

    @abstractmethod
    def get(self, id: str) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    def list(self) -> List[T]:
        """List all entities."""
        pass

    @abstractmethod
    def save(self, entity: T) -> T:
        """Save entity."""
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete entity by ID."""
        pass
```

**File:** `web/repositories/project_repository.py`

```python
"""Project repository - data access for projects."""

from pathlib import Path
from typing import Optional, List
import json
from datetime import datetime
import shutil

from web.models.domain import Project, ProjectStatus
from web.repositories.base import Repository


class ProjectRepository(Repository[Project]):
    """Repository for project data access."""

    def __init__(self, projects_dir: Path):
        self.projects_dir = projects_dir
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def get(self, name: str) -> Optional[Project]:
        """Get project by name."""
        project_path = self.projects_dir / name

        if not project_path.exists():
            return None

        return self._load_project(project_path)

    def list(self) -> List[Project]:
        """List all projects."""
        projects = []

        if not self.projects_dir.exists():
            return projects

        for project_path in self.projects_dir.iterdir():
            if project_path.is_dir():
                project = self._load_project(project_path)
                if project:
                    projects.append(project)

        return sorted(projects, key=lambda p: p.updated_at, reverse=True)

    def save(self, project: Project) -> Project:
        """Save project."""
        # Ensure directory exists
        project.path.mkdir(parents=True, exist_ok=True)

        # Save state file
        state = {
            "name": project.name,
            "status": project.status.value,
            "video_path": str(project.video_path) if project.video_path else None,
            "stages": project.stages,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
        }

        with open(project.state_file, "w") as f:
            json.dump(state, f, indent=2)

        return project

    def delete(self, name: str) -> bool:
        """Delete project."""
        project_path = self.projects_dir / name

        if project_path.exists():
            shutil.rmtree(project_path)
            return True

        return False

    def _load_project(self, project_path: Path) -> Optional[Project]:
        """Load project from filesystem."""
        state_file = project_path / "project_state.json"

        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)

            return Project(
                name=state.get("name", project_path.name),
                path=project_path,
                status=ProjectStatus(state.get("status", "unknown")),
                video_path=Path(state["video_path"]) if state.get("video_path") else None,
                stages=state.get("stages", []),
                created_at=datetime.fromisoformat(state["created_at"]),
                updated_at=datetime.fromisoformat(state["updated_at"]),
            )
        else:
            # Legacy project without state file
            return Project(
                name=project_path.name,
                path=project_path,
                status=ProjectStatus.UNKNOWN,
                video_path=None,
                stages=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
```

**File:** `web/repositories/job_repository.py`

```python
"""Job repository - in-memory storage for pipeline jobs."""

from typing import Optional, Dict
from web.models.domain import PipelineJob, JobStatus
from web.repositories.base import Repository


class JobRepository(Repository[PipelineJob]):
    """Repository for pipeline job data (in-memory)."""

    def __init__(self):
        self._jobs: Dict[str, PipelineJob] = {}

    def get(self, project_name: str) -> Optional[PipelineJob]:
        """Get job by project name."""
        return self._jobs.get(project_name)

    def list(self) -> list[PipelineJob]:
        """List all jobs."""
        return list(self._jobs.values())

    def save(self, job: PipelineJob) -> PipelineJob:
        """Save job."""
        self._jobs[job.project_name] = job
        return job

    def delete(self, project_name: str) -> bool:
        """Delete job."""
        if project_name in self._jobs:
            del self._jobs[project_name]
            return True
        return False

    def get_active_jobs(self) -> list[PipelineJob]:
        """Get all running jobs."""
        return [
            job for job in self._jobs.values()
            if job.status == JobStatus.RUNNING
        ]
```

**Success Criteria:**
- [ ] Repositories handle all data access
- [ ] No SQL or file I/O outside repositories
- [ ] Repository interface allows future DB migration
- [ ] Type-safe with domain models

---

### Phase 2A Exit Criteria

- [ ] Layered directory structure in place
- [ ] Domain models defined (no framework deps)
- [ ] DTOs defined (Pydantic validation)
- [ ] Repository layer implemented
- [ ] Data access abstracted from business logic
- [ ] No cross-layer violations

---

## Phase 2B: Service Layer (Business Logic) ⚪

**Goal:** Implement business logic separate from API/UI

### Deliverables
- `ProjectService` - Project management logic
- `PipelineService` - Pipeline execution orchestration
- `WebSocketService` - Real-time update broadcasting

### Tasks

#### Task 2B.1: Implement Project Service
**File:** `web/services/project_service.py`

```python
"""Project service - business logic for project management."""

from pathlib import Path
from datetime import datetime
from typing import Optional, List
import shutil

from web.models.domain import Project, ProjectStatus
from web.models.dto import ProjectDTO, ProjectCreateRequest, ProjectListResponse
from web.repositories.project_repository import ProjectRepository


class ProjectService:
    """Service for project management business logic."""

    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo

    def list_projects(self) -> ProjectListResponse:
        """List all projects."""
        projects = self.project_repo.list()

        return ProjectListResponse(
            projects=[self._to_dto(p) for p in projects],
            total=len(projects),
        )

    def get_project(self, name: str) -> Optional[ProjectDTO]:
        """Get project by name."""
        project = self.project_repo.get(name)

        if not project:
            return None

        return self._to_dto(project)

    def create_project(
        self,
        request: ProjectCreateRequest,
        projects_dir: Path
    ) -> ProjectDTO:
        """Create a new project."""
        # Business rule: Project name must be unique
        existing = self.project_repo.get(request.name)
        if existing:
            raise ValueError(f"Project '{request.name}' already exists")

        # Create project entity
        now = datetime.now()
        project = Project(
            name=request.name,
            path=projects_dir / request.name,
            status=ProjectStatus.CREATED,
            video_path=None,
            stages=request.stages,
            created_at=now,
            updated_at=now,
        )

        # Persist
        project = self.project_repo.save(project)

        return self._to_dto(project)

    def save_uploaded_video(
        self,
        project_name: str,
        video_filename: str,
        video_content: bytes
    ) -> ProjectDTO:
        """Save uploaded video to project."""
        project = self.project_repo.get(project_name)
        if not project:
            raise ValueError(f"Project '{project_name}' not found")

        # Save video file
        video_path = project.source_dir / video_filename
        video_path.parent.mkdir(parents=True, exist_ok=True)

        with open(video_path, "wb") as f:
            f.write(video_content)

        # Update project
        project.video_path = video_path
        project.updated_at = datetime.now()

        project = self.project_repo.save(project)

        return self._to_dto(project)

    def delete_project(self, name: str) -> bool:
        """Delete a project."""
        return self.project_repo.delete(name)

    def update_project_status(
        self,
        name: str,
        status: ProjectStatus
    ) -> Optional[ProjectDTO]:
        """Update project status."""
        project = self.project_repo.get(name)
        if not project:
            return None

        project.status = status
        project.updated_at = datetime.now()

        project = self.project_repo.save(project)

        return self._to_dto(project)

    @staticmethod
    def _to_dto(project: Project) -> ProjectDTO:
        """Convert domain entity to DTO."""
        return ProjectDTO(
            name=project.name,
            status=project.status,
            video_path=str(project.video_path) if project.video_path else None,
            stages=project.stages,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
```

**Success Criteria:**
- [ ] All project business logic in service
- [ ] Service validates business rules
- [ ] Service converts domain ↔ DTO
- [ ] No direct file I/O (delegates to repository)

---

#### Task 2B.2: Implement Pipeline Service
**File:** `web/services/pipeline_service.py`

```python
"""Pipeline service - orchestrates pipeline execution."""

import asyncio
import subprocess
from datetime import datetime
from typing import Optional, Callable, Awaitable

from web.models.domain import PipelineJob, JobStatus, ProjectStatus
from web.models.dto import (
    JobDTO, JobStartRequest, JobStartResponse, ProgressUpdate
)
from web.repositories.job_repository import JobRepository
from web.services.project_service import ProjectService


class PipelineService:
    """Service for pipeline execution orchestration."""

    def __init__(
        self,
        job_repo: JobRepository,
        project_service: ProjectService
    ):
        self.job_repo = job_repo
        self.project_service = project_service

    async def start_job(
        self,
        project_name: str,
        request: JobStartRequest,
        progress_callback: Optional[Callable[[ProgressUpdate], Awaitable[None]]] = None
    ) -> JobStartResponse:
        """Start a pipeline job."""
        # Business rule: Only one job per project at a time
        existing_job = self.job_repo.get(project_name)
        if existing_job and existing_job.status == JobStatus.RUNNING:
            raise ValueError(f"Job already running for project '{project_name}'")

        # Create job
        job = PipelineJob(
            project_name=project_name,
            stages=request.stages,
            status=JobStatus.PENDING,
            current_stage=None,
            progress=0.0,
            message=None,
            started_at=None,
            completed_at=None,
            error=None,
        )

        job = self.job_repo.save(job)

        # Update project status
        self.project_service.update_project_status(
            project_name,
            ProjectStatus.PROCESSING
        )

        # Start pipeline process
        asyncio.create_task(
            self._run_pipeline(job, progress_callback)
        )

        return JobStartResponse(
            status="started",
            job=self._to_dto(job)
        )

    async def stop_job(self, project_name: str) -> bool:
        """Stop a running job."""
        job = self.job_repo.get(project_name)
        if not job:
            return False

        if job.status != JobStatus.RUNNING:
            return False

        # TODO: Terminate subprocess
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now()

        self.job_repo.save(job)

        # Update project status
        self.project_service.update_project_status(
            project_name,
            ProjectStatus.FAILED
        )

        return True

    def get_job(self, project_name: str) -> Optional[JobDTO]:
        """Get job status."""
        job = self.job_repo.get(project_name)
        if not job:
            return None

        return self._to_dto(job)

    async def _run_pipeline(
        self,
        job: PipelineJob,
        progress_callback: Optional[Callable[[ProgressUpdate], Awaitable[None]]]
    ):
        """Run the pipeline process."""
        # Update job to running
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        self.job_repo.save(job)

        try:
            # Build command
            cmd = [
                "python", "/app/scripts/run_pipeline.py",
                "--name", job.project_name,
                "--stages", ",".join(job.stages),
                "--json-output",
            ]

            # Start subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Monitor output
            async for line in process.stdout:
                await self._process_output_line(job, line, progress_callback)

            # Wait for completion
            await process.wait()

            # Update final status
            if process.returncode == 0:
                job.status = JobStatus.COMPLETE
                job.progress = 1.0

                # Update project status
                self.project_service.update_project_status(
                    job.project_name,
                    ProjectStatus.COMPLETE
                )
            else:
                job.status = JobStatus.FAILED
                job.error = "Pipeline exited with error"

                # Update project status
                self.project_service.update_project_status(
                    job.project_name,
                    ProjectStatus.FAILED
                )

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)

            # Update project status
            self.project_service.update_project_status(
                job.project_name,
                ProjectStatus.FAILED
            )

        finally:
            job.completed_at = datetime.now()
            self.job_repo.save(job)

    async def _process_output_line(
        self,
        job: PipelineJob,
        line: bytes,
        progress_callback: Optional[Callable[[ProgressUpdate], Awaitable[None]]]
    ):
        """Process a line of output from pipeline."""
        import json

        try:
            data = json.loads(line.decode())

            # Update job state
            if "stage" in data:
                job.current_stage = data["stage"]
            if "progress" in data:
                job.progress = data["progress"]
            if "status" in data:
                job.status = JobStatus(data["status"])
            if "message" in data:
                job.message = data["message"]

            self.job_repo.save(job)

            # Notify via callback
            if progress_callback:
                update = ProgressUpdate(
                    stage=data.get("stage", ""),
                    progress=data.get("progress", 0.0),
                    status=JobStatus(data.get("status", "running")),
                    message=data.get("message", ""),
                )
                await progress_callback(update)

        except json.JSONDecodeError:
            # Regular log line, ignore
            pass

    @staticmethod
    def _to_dto(job: PipelineJob) -> JobDTO:
        """Convert domain entity to DTO."""
        return JobDTO(
            project_name=job.project_name,
            stages=job.stages,
            status=job.status,
            current_stage=job.current_stage,
            progress=job.progress,
            message=job.message,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error=job.error,
        )
```

**Success Criteria:**
- [ ] Pipeline orchestration in service
- [ ] Business rules enforced (one job at a time)
- [ ] Delegates to repositories for data
- [ ] Async/await for background execution

---

#### Task 2B.3: Implement WebSocket Service
**File:** `web/services/websocket_service.py`

```python
"""WebSocket service - manages real-time updates."""

from fastapi import WebSocket
from typing import Dict, Set
from web.models.dto import ProgressUpdate


class WebSocketService:
    """Service for managing WebSocket connections and broadcasting."""

    def __init__(self):
        # Map project_name -> set of WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_name: str):
        """Register a WebSocket connection."""
        await websocket.accept()

        if project_name not in self._connections:
            self._connections[project_name] = set()

        self._connections[project_name].add(websocket)

    def disconnect(self, websocket: WebSocket, project_name: str):
        """Unregister a WebSocket connection."""
        if project_name in self._connections:
            self._connections[project_name].discard(websocket)

    async def broadcast_progress(
        self,
        project_name: str,
        update: ProgressUpdate
    ):
        """Broadcast progress update to all clients for a project."""
        if project_name not in self._connections:
            return

        dead_connections = set()

        for websocket in self._connections[project_name]:
            try:
                await websocket.send_json(update.dict())
            except Exception:
                dead_connections.add(websocket)

        # Clean up dead connections
        for conn in dead_connections:
            self._connections[project_name].discard(conn)
```

**Success Criteria:**
- [ ] WebSocket connections managed centrally
- [ ] Broadcasting logic isolated
- [ ] Dead connection cleanup

---

### Phase 2B Exit Criteria

- [ ] All business logic in service layer
- [ ] Services delegate to repositories
- [ ] Services return DTOs (not domain entities)
- [ ] No file I/O or HTTP logic in services
- [ ] Services are testable (mockable dependencies)

---

## Phase 2C: API Layer (Controllers) ⚪

**Goal:** Thin API controllers that delegate to services

### Deliverables
- REST API routers (projects, pipeline, system)
- WebSocket endpoint
- Dependency injection setup
- Input validation with Pydantic

### Tasks

#### Task 2C.1: Set Up Dependency Injection
**File:** `web/api/dependencies.py`

```python
"""FastAPI dependencies for dependency injection."""

from pathlib import Path
import os
from functools import lru_cache

from web.repositories.project_repository import ProjectRepository
from web.repositories.job_repository import JobRepository
from web.services.project_service import ProjectService
from web.services.pipeline_service import PipelineService
from web.services.websocket_service import WebSocketService


# Singleton instances
_project_repo: ProjectRepository = None
_job_repo: JobRepository = None
_project_service: ProjectService = None
_pipeline_service: PipelineService = None
_websocket_service: WebSocketService = None


def get_projects_dir() -> Path:
    """Get projects directory from environment."""
    return Path(os.environ.get("VFX_PROJECTS_DIR", "/workspace/projects"))


def get_project_repository() -> ProjectRepository:
    """Get project repository instance."""
    global _project_repo
    if _project_repo is None:
        _project_repo = ProjectRepository(get_projects_dir())
    return _project_repo


def get_job_repository() -> JobRepository:
    """Get job repository instance."""
    global _job_repo
    if _job_repo is None:
        _job_repo = JobRepository()
    return _job_repo


def get_project_service() -> ProjectService:
    """Get project service instance."""
    global _project_service
    if _project_service is None:
        _project_service = ProjectService(get_project_repository())
    return _project_service


def get_pipeline_service() -> PipelineService:
    """Get pipeline service instance."""
    global _pipeline_service
    if _pipeline_service is None:
        _pipeline_service = PipelineService(
            get_job_repository(),
            get_project_service()
        )
    return _pipeline_service


def get_websocket_service() -> WebSocketService:
    """Get WebSocket service instance."""
    global _websocket_service
    if _websocket_service is None:
        _websocket_service = WebSocketService()
    return _websocket_service
```

**Success Criteria:**
- [ ] Dependency injection configured
- [ ] Singletons for services/repositories
- [ ] Easy to mock for testing

---

#### Task 2C.2: Implement Projects API Router
**File:** `web/api/routers/projects.py`

```python
"""Projects API router - thin controller layer."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional

from web.models.dto import (
    ProjectDTO, ProjectCreateRequest, ProjectListResponse
)
from web.services.project_service import ProjectService
from web.api.dependencies import get_project_service, get_projects_dir


router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    service: ProjectService = Depends(get_project_service)
):
    """List all projects."""
    return service.list_projects()


@router.get("/{name}", response_model=ProjectDTO)
async def get_project(
    name: str,
    service: ProjectService = Depends(get_project_service)
):
    """Get project by name."""
    project = service.get_project(name)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.post("", response_model=ProjectDTO, status_code=201)
async def create_project(
    request: ProjectCreateRequest,
    service: ProjectService = Depends(get_project_service),
    projects_dir = Depends(get_projects_dir)
):
    """Create a new project."""
    try:
        return service.create_project(request, projects_dir)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{name}/upload-video", response_model=ProjectDTO)
async def upload_video(
    name: str,
    video: UploadFile = File(...),
    service: ProjectService = Depends(get_project_service)
):
    """Upload video file to project."""
    try:
        content = await video.read()
        return service.save_uploaded_video(name, video.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{name}", status_code=204)
async def delete_project(
    name: str,
    service: ProjectService = Depends(get_project_service)
):
    """Delete a project."""
    success = service.delete_project(name)

    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
```

**Success Criteria:**
- [ ] Router is thin (no business logic)
- [ ] All logic delegated to service
- [ ] Input validation via Pydantic
- [ ] Proper HTTP status codes

---

#### Task 2C.3: Implement Pipeline API Router
**File:** `web/api/routers/pipeline.py`

```python
"""Pipeline API router - thin controller layer."""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from web.models.dto import JobDTO, JobStartRequest, JobStartResponse
from web.services.pipeline_service import PipelineService
from web.services.websocket_service import WebSocketService
from web.api.dependencies import get_pipeline_service, get_websocket_service


router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.post("/projects/{name}/start", response_model=JobStartResponse)
async def start_job(
    name: str,
    request: JobStartRequest,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
    ws_service: WebSocketService = Depends(get_websocket_service)
):
    """Start a pipeline job."""
    try:
        # Create callback to broadcast progress
        async def progress_callback(update):
            await ws_service.broadcast_progress(name, update)

        return await pipeline_service.start_job(name, request, progress_callback)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/{name}/stop")
async def stop_job(
    name: str,
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """Stop a running job."""
    success = await pipeline_service.stop_job(name)

    if not success:
        raise HTTPException(status_code=404, detail="Job not found or not running")

    return {"status": "stopped"}


@router.get("/projects/{name}/status", response_model=JobDTO)
async def get_job_status(
    name: str,
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """Get job status."""
    job = pipeline_service.get_job(name)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.websocket("/ws/{project_name}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_name: str,
    ws_service: WebSocketService = Depends(get_websocket_service)
):
    """WebSocket endpoint for real-time progress."""
    await ws_service.connect(websocket, project_name)

    try:
        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_service.disconnect(websocket, project_name)
```

**Success Criteria:**
- [ ] Router delegates all logic to service
- [ ] WebSocket managed by service
- [ ] Error handling with proper HTTP codes

---

#### Task 2C.4: Implement System API Router
**File:** `web/api/routers/system.py`

```python
"""System API router - health, shutdown, etc."""

from fastapi import APIRouter, Depends
import os
import signal

from web.repositories.job_repository import JobRepository
from web.api.dependencies import get_job_repository


router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.post("/shutdown")
async def shutdown(
    job_repo: JobRepository = Depends(get_job_repository)
):
    """Graceful shutdown."""
    # Check for active jobs
    active_jobs = job_repo.get_active_jobs()

    if active_jobs:
        return {
            "status": "warning",
            "message": "Active jobs running",
            "jobs": [job.project_name for job in active_jobs],
        }

    # Trigger shutdown
    os.kill(os.getpid(), signal.SIGTERM)

    return {"status": "shutting_down"}
```

**Success Criteria:**
- [ ] System operations exposed via API
- [ ] Health check for monitoring
- [ ] Graceful shutdown with job checks

---

### Phase 2C Exit Criteria

- [ ] All API routers implemented
- [ ] Routers are thin (delegate to services)
- [ ] Dependency injection working
- [ ] Input validation via Pydantic
- [ ] Proper HTTP status codes
- [ ] No business logic in routers

---

## Phase 2D: UI Layer (Presentation) ⚪

**Goal:** Dumb UI that only calls APIs and renders

### Deliverables
- HTML templates (server-side rendering)
- JavaScript API client (abstraction)
- UI-specific JavaScript (no business logic)
- CSS styling

### Tasks

#### Task 2D.1: Create JavaScript API Client
**File:** `web/ui/static/js/api-client.js`

```javascript
/**
 * API Client - Abstraction over fetch API
 * Frontend makes ALL requests through this client
 */

class ApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;

        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({
                detail: response.statusText
            }));
            throw new Error(error.detail || 'Request failed');
        }

        return response.json();
    }

    // Projects API
    async listProjects() {
        return this.request('/api/projects');
    }

    async getProject(name) {
        return this.request(`/api/projects/${name}`);
    }

    async createProject(data) {
        return this.request('/api/projects', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async uploadVideo(projectName, videoFile) {
        const formData = new FormData();
        formData.append('video', videoFile);

        const response = await fetch(
            `${this.baseUrl}/api/projects/${projectName}/upload-video`,
            {
                method: 'POST',
                body: formData,
            }
        );

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        return response.json();
    }

    async deleteProject(name) {
        return this.request(`/api/projects/${name}`, {
            method: 'DELETE',
        });
    }

    // Pipeline API
    async startJob(projectName, stages) {
        return this.request(`/api/pipeline/projects/${projectName}/start`, {
            method: 'POST',
            body: JSON.stringify({ stages }),
        });
    }

    async stopJob(projectName) {
        return this.request(`/api/pipeline/projects/${projectName}/stop`, {
            method: 'POST',
        });
    }

    async getJobStatus(projectName) {
        return this.request(`/api/pipeline/projects/${projectName}/status`);
    }

    // System API
    async shutdown() {
        return this.request('/api/system/shutdown', {
            method: 'POST',
        });
    }

    // WebSocket
    connectWebSocket(projectName, onMessage) {
        const wsUrl = `ws://${window.location.host}/api/pipeline/ws/${projectName}`;
        const ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onMessage(data);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        return ws;
    }
}

// Export singleton instance
const api = new ApiClient();
```

**Success Criteria:**
- [ ] All API calls abstracted
- [ ] No fetch() calls in UI code
- [ ] Type-safe client methods
- [ ] Error handling centralized

---

#### Task 2D.2: Create Dashboard UI Logic
**File:** `web/ui/static/js/dashboard.js`

```javascript
/**
 * Dashboard UI Logic
 * ONLY renders data from API - NO business logic
 */

document.addEventListener('DOMContentLoaded', async () => {
    await loadProjects();
});

async function loadProjects() {
    try {
        const response = await api.listProjects();
        renderProjects(response.projects);
    } catch (error) {
        showError('Failed to load projects: ' + error.message);
    }
}

function renderProjects(projects) {
    const container = document.getElementById('project-grid');

    // Clear existing
    container.innerHTML = '';

    // Render each project
    projects.forEach(project => {
        const card = createProjectCard(project);
        container.appendChild(card);
    });

    // Add "New Project" card
    container.appendChild(createNewProjectCard());
}

function createProjectCard(project) {
    const card = document.createElement('div');
    card.className = 'project-card';
    card.setAttribute('data-status', project.status);

    card.innerHTML = `
        <div class="project-thumbnail">
            <img src="/static/img/placeholder.png" alt="${project.name}">
        </div>
        <h3>${project.name}</h3>
        <p class="status">${project.status}</p>
        <div class="actions">
            <a href="/projects/${project.name}" class="btn">Open</a>
            <button onclick="deleteProject('${project.name}')" class="btn btn-danger">Delete</button>
        </div>
    `;

    return card;
}

function createNewProjectCard() {
    const card = document.createElement('div');
    card.className = 'project-card new-project';

    card.innerHTML = `
        <a href="/projects/new">
            <div class="plus-icon">+</div>
            <p>New Project</p>
        </a>
    `;

    return card;
}

async function deleteProject(name) {
    if (!confirm(`Delete project "${name}"? This cannot be undone.`)) {
        return;
    }

    try {
        await api.deleteProject(name);
        await loadProjects(); // Refresh list
    } catch (error) {
        showError('Failed to delete project: ' + error.message);
    }
}

function showError(message) {
    // Simple error display
    alert(message);
}
```

**Success Criteria:**
- [ ] UI only renders data from API
- [ ] No calculations or business logic
- [ ] All actions delegate to API client
- [ ] Clean separation of concerns

---

#### Task 2D.3: Create Processing UI Logic
**File:** `web/ui/static/js/processing.js`

```javascript
/**
 * Processing UI Logic
 * ONLY renders progress from WebSocket - NO calculations
 */

let websocket = null;
const projectName = document.getElementById('project-name').value;

document.addEventListener('DOMContentLoaded', () => {
    initializeWebSocket();
    setupEventListeners();
});

function initializeWebSocket() {
    websocket = api.connectWebSocket(projectName, handleProgressUpdate);
}

function handleProgressUpdate(data) {
    // JUST RENDER - no logic

    // Update progress bar (data.progress is already 0-1, convert to percentage)
    const progressPercent = `${data.progress * 100}%`;
    document.getElementById('stage-progress').style.width = progressPercent;

    // Update stage name
    if (data.stage) {
        document.getElementById('current-stage').textContent = data.stage;
    }

    // Update message
    if (data.message) {
        document.getElementById('stage-status').textContent = data.message;
        appendToLog(data.message);
    }

    // Update status indicator
    if (data.status === 'complete') {
        showCompletionMessage();
    } else if (data.status === 'failed') {
        showErrorMessage(data.message);
    }
}

function appendToLog(message) {
    const logs = document.getElementById('log-output');
    logs.textContent += message + '\n';
    logs.scrollTop = logs.scrollHeight;
}

function showCompletionMessage() {
    document.getElementById('overall-status').textContent = 'Complete!';
    document.getElementById('overall-status').className = 'status-complete';
}

function showErrorMessage(message) {
    document.getElementById('overall-status').textContent = `Failed: ${message}`;
    document.getElementById('overall-status').className = 'status-error';
}

function setupEventListeners() {
    document.getElementById('stop-btn').addEventListener('click', async () => {
        if (confirm('Stop processing? Progress will be lost.')) {
            try {
                await api.stopJob(projectName);
                window.location.href = `/projects/${projectName}`;
            } catch (error) {
                alert('Failed to stop job: ' + error.message);
            }
        }
    });

    document.getElementById('toggle-logs').addEventListener('click', () => {
        const logs = document.getElementById('log-output');
        logs.style.display = logs.style.display === 'none' ? 'block' : 'none';
    });
}
```

**Success Criteria:**
- [ ] UI just renders WebSocket data
- [ ] No progress calculations in frontend
- [ ] All actions via API client
- [ ] Clean event handling

---

#### Task 2D.4: Create HTML Templates
**File:** `web/ui/templates/processing.html`

```html
{% extends "base.html" %}

{% block content %}
<input type="hidden" id="project-name" value="{{ project.name }}">

<h2>{{ project.name }} - Processing</h2>

<div class="progress-container">
    <div class="overall-progress">
        <h3>Overall Progress</h3>
        <div class="progress-bar">
            <div class="progress-fill" id="overall-progress" style="width: 0%"></div>
        </div>
        <p id="overall-status">Starting...</p>
    </div>

    <div class="stage-progress">
        <h3>Current Stage: <span id="current-stage">-</span></h3>
        <div class="progress-bar">
            <div class="progress-fill" id="stage-progress" style="width: 0%"></div>
        </div>
        <p id="stage-status">-</p>
    </div>
</div>

<div class="actions">
    <button id="stop-btn" class="btn btn-danger">Stop</button>
</div>

<div class="logs">
    <h3>Live Logs <button id="toggle-logs">Show</button></h3>
    <pre id="log-output" style="display: none;"></pre>
</div>
{% endblock %}

{% block extra_js %}
<script src="/static/js/api-client.js"></script>
<script src="/static/js/processing.js"></script>
{% endblock %}
```

**Success Criteria:**
- [ ] Templates are pure HTML
- [ ] No inline JavaScript logic
- [ ] All JS in separate files
- [ ] Clean separation

---

### Phase 2D Exit Criteria

- [ ] API client abstracts all HTTP calls
- [ ] UI code has zero business logic
- [ ] UI only renders data from API
- [ ] JavaScript organized by page/feature
- [ ] No calculations in frontend (done in backend)

---

## Phase 2E: Integration & Testing ⚪

**Goal:** End-to-end validation of layered architecture

### Test Cases

#### Test 2E.1: Architecture Validation
**Verify layer separation:**
- [ ] Frontend imports nothing from services/repositories
- [ ] API routers import only services (not repositories)
- [ ] Services import only repositories (not HTTP/UI)
- [ ] Repositories import only domain models
- [ ] No circular dependencies

#### Test 2E.2: Complete User Flow
1. Start platform
2. Create project via API
3. Upload video
4. Start job
5. Monitor progress via WebSocket
6. Verify completion

**Success Criteria:**
- [ ] Data flows: UI → API → Service → Repository → Storage
- [ ] Updates flow: Storage → Repository → Service → WebSocket → UI
- [ ] No layer violations

#### Test 2E.3: Unit Tests
```python
# tests/test_services.py

def test_project_service_create():
    """Test project service creates project via repository."""
    mock_repo = Mock(ProjectRepository)
    service = ProjectService(mock_repo)

    request = ProjectCreateRequest(name="test", stages=["ingest"])

    service.create_project(request, Path("/workspace"))

    # Verify repository was called
    mock_repo.save.assert_called_once()
```

**Success Criteria:**
- [ ] Services testable without HTTP
- [ ] Repositories testable without filesystem
- [ ] Easy to mock dependencies

---

### Phase 2E Exit Criteria

- [ ] All layers properly separated
- [ ] No cross-layer violations
- [ ] Unit tests for services
- [ ] Integration tests pass
- [ ] Architecture documented

---

## Roadmap 2 Success Criteria

**Ready for production when:**

- [ ] All phases complete
- [ ] Proper layered architecture verified
- [ ] Frontend has zero business logic
- [ ] Services are unit testable
- [ ] API contracts documented (OpenAPI)
- [ ] Performance acceptable
- [ ] User testing successful
- [ ] Documentation complete

**Architecture Quality Checklist:**
- [ ] SOLID principles followed
- [ ] DRY - no duplication across layers
- [ ] Separation of concerns maintained
- [ ] Easy to test (mockable dependencies)
- [ ] Easy to change (swap repositories, etc.)
- [ ] Easy to understand (clear responsibilities)

---

**Previous:** [Roadmap 1: Docker Migration](ROADMAP-1-DOCKER.md)
**Up:** [Atlas Overview](ATLAS.md)

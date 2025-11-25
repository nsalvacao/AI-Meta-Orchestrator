"""REST API data models.

This module provides Pydantic models for API request and response data.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ai_meta_orchestrator.domain.agents.agent_models import AgentRole
from ai_meta_orchestrator.domain.tasks.task_models import TaskPriority, TaskStatus
from ai_meta_orchestrator.domain.templates.template_models import TemplateCategory
from ai_meta_orchestrator.domain.workflows.workflow_models import WorkflowMode, WorkflowStatus


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


# ===== Health Check Models =====


class HealthResponse(BaseModel):
    """Health check response."""

    status: HealthStatus
    version: str
    uptime_seconds: float
    timestamp: datetime = Field(default_factory=datetime.now)


# ===== Agent Models =====


class AgentInfo(BaseModel):
    """Information about an agent."""

    model_config = ConfigDict(from_attributes=True)

    role: AgentRole
    goal: str
    backstory: str
    verbose: bool
    allow_delegation: bool
    memory: bool


class AgentListResponse(BaseModel):
    """Response containing list of agents."""

    agents: list[AgentInfo]
    total: int


# ===== Task Models =====


class TaskCreate(BaseModel):
    """Request to create a task."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    assigned_to: AgentRole
    expected_output: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    max_revisions: int = Field(default=3, ge=0, le=10)


class TaskResponse(BaseModel):
    """Response containing task details."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    assigned_to: AgentRole
    status: TaskStatus
    priority: TaskPriority
    expected_output: str
    revision_count: int
    max_revisions: int
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    """Response containing list of tasks."""

    tasks: list[TaskResponse]
    total: int


# ===== Workflow Models =====


class WorkflowConfigCreate(BaseModel):
    """Configuration for workflow creation."""

    mode: WorkflowMode = WorkflowMode.SEQUENTIAL
    max_iterations: int = Field(default=10, ge=1, le=100)
    enable_evaluation: bool = True
    enable_correction_loop: bool = True
    verbose: bool = True


class WorkflowCreate(BaseModel):
    """Request to create a workflow."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    config: WorkflowConfigCreate = Field(default_factory=WorkflowConfigCreate)
    tasks: list[TaskCreate] = Field(default_factory=list)


class WorkflowResponse(BaseModel):
    """Response containing workflow details."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    status: WorkflowStatus
    current_iteration: int
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    task_count: int
    tasks_completed: int = 0
    tasks_failed: int = 0


class WorkflowListResponse(BaseModel):
    """Response containing list of workflows."""

    workflows: list[WorkflowResponse]
    total: int


class WorkflowResultResponse(BaseModel):
    """Response containing workflow execution result."""

    workflow_id: UUID
    success: bool
    tasks_completed: int
    tasks_failed: int
    total_iterations: int
    duration_seconds: float
    errors: list[str] = Field(default_factory=list)
    outputs: dict[str, Any] = Field(default_factory=dict)


# ===== Template Models =====


class TemplateInfo(BaseModel):
    """Information about a workflow template."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    category: TemplateCategory
    required_params: list[str]
    optional_params: dict[str, str]
    tags: list[str]
    version: str


class TemplateListResponse(BaseModel):
    """Response containing list of templates."""

    templates: list[TemplateInfo]
    total: int


class TemplateInstantiateRequest(BaseModel):
    """Request to instantiate a template."""

    template_name: str
    params: dict[str, str]
    workflow_name: str | None = None
    run_immediately: bool = False


class TemplateInstantiateResponse(BaseModel):
    """Response after instantiating a template."""

    workflow_id: UUID
    workflow_name: str
    task_count: int
    status: WorkflowStatus


# ===== Standard Workflow Models =====


class StandardWorkflowRequest(BaseModel):
    """Request to run a standard development workflow."""

    project_description: str = Field(..., min_length=1)
    name: str = Field(default="Standard Development Workflow", max_length=200)


# ===== Plugin Models =====


class PluginInfo(BaseModel):
    """Information about a plugin."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    version: str
    description: str
    plugin_type: str
    author: str
    status: str
    tags: list[str]


class PluginListResponse(BaseModel):
    """Response containing list of plugins."""

    plugins: list[PluginInfo]
    total: int
    active_count: int


# ===== Error Models =====


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str | None = None
    status_code: int

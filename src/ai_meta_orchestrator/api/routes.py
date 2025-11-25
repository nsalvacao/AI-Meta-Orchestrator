"""REST API routes for the AI Meta Orchestrator.

This module provides the FastAPI router definitions for all API endpoints.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from ai_meta_orchestrator import __version__
from ai_meta_orchestrator.adapters.templates import get_default_template_registry
from ai_meta_orchestrator.api.models import (
    AgentInfo,
    AgentListResponse,
    ErrorResponse,
    HealthResponse,
    HealthStatus,
    PluginInfo,
    PluginListResponse,
    StandardWorkflowRequest,
    TaskListResponse,
    TaskResponse,
    TemplateInfo,
    TemplateInstantiateRequest,
    TemplateInstantiateResponse,
    TemplateListResponse,
    WorkflowCreate,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowResultResponse,
)
from ai_meta_orchestrator.application.services.orchestrator_service import (
    OrchestratorService,
)
from ai_meta_orchestrator.domain.agents.agent_models import (
    DEFAULT_AGENT_CONFIGS,
    AgentRole,
)
from ai_meta_orchestrator.domain.plugins.plugin_models import PluginRegistry
from ai_meta_orchestrator.domain.tasks.task_models import Task, TaskStatus
from ai_meta_orchestrator.domain.workflows.workflow_models import (
    Workflow,
    WorkflowConfig,
    WorkflowStatus,
)

# Store for workflows (in-memory for now, would use database in production)
_workflows: dict[UUID, Workflow] = {}
_workflow_results: dict[UUID, WorkflowResultResponse] = {}

# Singleton instances
_orchestrator: OrchestratorService | None = None
_plugin_registry: PluginRegistry | None = None
_start_time: datetime = datetime.now()


def get_orchestrator() -> OrchestratorService:
    """Get or create the orchestrator service instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorService()
    return _orchestrator


def get_plugin_registry() -> PluginRegistry:
    """Get or create the plugin registry instance."""
    global _plugin_registry
    if _plugin_registry is None:
        _plugin_registry = PluginRegistry()
    return _plugin_registry


# ===== Health Router =====

health_router = APIRouter(prefix="/health", tags=["Health"])


@health_router.get(
    "",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the orchestrator service.",
)
def health_check() -> HealthResponse:
    """Check service health."""
    uptime = (datetime.now() - _start_time).total_seconds()
    return HealthResponse(
        status=HealthStatus.HEALTHY,
        version=__version__,
        uptime_seconds=uptime,
    )


# ===== Agents Router =====

agents_router = APIRouter(prefix="/agents", tags=["Agents"])


@agents_router.get(
    "",
    response_model=AgentListResponse,
    summary="List agents",
    description="Get list of all available agent roles and their configurations.",
)
def list_agents() -> AgentListResponse:
    """List all available agents."""
    agents = []
    for role in AgentRole:
        config = DEFAULT_AGENT_CONFIGS[role]
        agents.append(
            AgentInfo(
                role=role,
                goal=config.goal,
                backstory=config.backstory,
                verbose=config.verbose,
                allow_delegation=config.allow_delegation,
                memory=config.memory,
            )
        )
    return AgentListResponse(agents=agents, total=len(agents))


@agents_router.get(
    "/{role}",
    response_model=AgentInfo,
    summary="Get agent",
    description="Get details of a specific agent role.",
    responses={404: {"model": ErrorResponse}},
)
def get_agent(role: AgentRole) -> AgentInfo:
    """Get a specific agent by role."""
    config = DEFAULT_AGENT_CONFIGS.get(role)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent role '{role}' not found",
        )
    return AgentInfo(
        role=role,
        goal=config.goal,
        backstory=config.backstory,
        verbose=config.verbose,
        allow_delegation=config.allow_delegation,
        memory=config.memory,
    )


# ===== Workflows Router =====

workflows_router = APIRouter(prefix="/workflows", tags=["Workflows"])


@workflows_router.get(
    "",
    response_model=WorkflowListResponse,
    summary="List workflows",
    description="Get list of all workflows.",
)
def list_workflows() -> WorkflowListResponse:
    """List all workflows."""
    workflow_responses = []
    for wf in _workflows.values():
        completed, total = wf.get_progress()
        failed = sum(
            1 for t in wf.tasks
            if t.status == TaskStatus.FAILED
        )
        workflow_responses.append(
            WorkflowResponse(
                id=wf.id,
                name=wf.name,
                description=wf.description,
                status=wf.status,
                current_iteration=wf.current_iteration,
                created_at=wf.created_at,
                started_at=wf.started_at,
                completed_at=wf.completed_at,
                task_count=total,
                tasks_completed=completed,
                tasks_failed=failed,
            )
        )
    return WorkflowListResponse(
        workflows=workflow_responses,
        total=len(workflow_responses),
    )


@workflows_router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create workflow",
    description="Create a new workflow with tasks.",
)
def create_workflow(workflow_data: WorkflowCreate) -> WorkflowResponse:
    """Create a new workflow."""
    config = WorkflowConfig(
        mode=workflow_data.config.mode,
        max_iterations=workflow_data.config.max_iterations,
        enable_evaluation=workflow_data.config.enable_evaluation,
        enable_correction_loop=workflow_data.config.enable_correction_loop,
        verbose=workflow_data.config.verbose,
    )

    workflow = Workflow(
        name=workflow_data.name,
        description=workflow_data.description,
        config=config,
    )

    # Add tasks
    for task_data in workflow_data.tasks:
        task = Task(
            name=task_data.name,
            description=task_data.description,
            assigned_to=task_data.assigned_to,
            expected_output=task_data.expected_output,
            priority=task_data.priority,
            max_revisions=task_data.max_revisions,
        )
        workflow.add_task(task)

    _workflows[workflow.id] = workflow

    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        status=workflow.status,
        current_iteration=workflow.current_iteration,
        created_at=workflow.created_at,
        started_at=workflow.started_at,
        completed_at=workflow.completed_at,
        task_count=len(workflow.tasks),
    )


@workflows_router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Get workflow",
    description="Get details of a specific workflow.",
    responses={404: {"model": ErrorResponse}},
)
def get_workflow(workflow_id: UUID) -> WorkflowResponse:
    """Get a specific workflow."""
    workflow = _workflows.get(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )

    completed, total = workflow.get_progress()
    failed = sum(
        1 for t in workflow.tasks
        if t.status == TaskStatus.FAILED
    )

    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        status=workflow.status,
        current_iteration=workflow.current_iteration,
        created_at=workflow.created_at,
        started_at=workflow.started_at,
        completed_at=workflow.completed_at,
        task_count=total,
        tasks_completed=completed,
        tasks_failed=failed,
    )


@workflows_router.post(
    "/{workflow_id}/run",
    response_model=WorkflowResultResponse,
    summary="Run workflow",
    description="Execute a workflow.",
    responses={404: {"model": ErrorResponse}},
)
def run_workflow(workflow_id: UUID) -> WorkflowResultResponse:
    """Run a workflow."""
    workflow = _workflows.get(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )

    if workflow.status == WorkflowStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow is already running",
        )

    orchestrator = get_orchestrator()
    result = orchestrator.run_workflow(workflow)

    result_response = WorkflowResultResponse(
        workflow_id=workflow.id,
        success=result.success,
        tasks_completed=result.tasks_completed,
        tasks_failed=result.tasks_failed,
        total_iterations=result.total_iterations,
        duration_seconds=result.duration_seconds,
        errors=result.errors,
        outputs=result.outputs,
    )

    _workflow_results[workflow.id] = result_response
    return result_response


@workflows_router.get(
    "/{workflow_id}/tasks",
    response_model=TaskListResponse,
    summary="Get workflow tasks",
    description="Get all tasks in a workflow.",
    responses={404: {"model": ErrorResponse}},
)
def get_workflow_tasks(workflow_id: UUID) -> TaskListResponse:
    """Get tasks in a workflow."""
    workflow = _workflows.get(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found",
        )

    tasks = [
        TaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            assigned_to=task.assigned_to,
            status=task.status,
            priority=task.priority,
            expected_output=task.expected_output,
            revision_count=task.revision_count,
            max_revisions=task.max_revisions,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        for task in workflow.tasks
    ]

    return TaskListResponse(tasks=tasks, total=len(tasks))


@workflows_router.get(
    "/{workflow_id}/result",
    response_model=WorkflowResultResponse,
    summary="Get workflow result",
    description="Get the execution result of a workflow.",
    responses={404: {"model": ErrorResponse}},
)
def get_workflow_result(workflow_id: UUID) -> WorkflowResultResponse:
    """Get workflow execution result."""
    result = _workflow_results.get(workflow_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No result found for workflow '{workflow_id}'",
        )
    return result


@workflows_router.post(
    "/standard",
    response_model=WorkflowResultResponse,
    summary="Run standard workflow",
    description="Create and run a standard development workflow.",
)
def run_standard_workflow(request: StandardWorkflowRequest) -> WorkflowResultResponse:
    """Run a standard development workflow."""
    orchestrator = get_orchestrator()
    workflow = orchestrator.create_standard_workflow(
        project_description=request.project_description,
        name=request.name,
    )

    _workflows[workflow.id] = workflow
    result = orchestrator.run_workflow(workflow)

    result_response = WorkflowResultResponse(
        workflow_id=workflow.id,
        success=result.success,
        tasks_completed=result.tasks_completed,
        tasks_failed=result.tasks_failed,
        total_iterations=result.total_iterations,
        duration_seconds=result.duration_seconds,
        errors=result.errors,
        outputs=result.outputs,
    )

    _workflow_results[workflow.id] = result_response
    return result_response


# ===== Templates Router =====

templates_router = APIRouter(prefix="/templates", tags=["Templates"])


@templates_router.get(
    "",
    response_model=TemplateListResponse,
    summary="List templates",
    description="Get list of all available workflow templates.",
)
def list_templates() -> TemplateListResponse:
    """List all workflow templates."""
    registry = get_default_template_registry()
    templates = registry.list_all()

    template_infos = [
        TemplateInfo(
            id=t.id,
            name=t.name,
            description=t.description,
            category=t.category,
            required_params=t.required_params,
            optional_params=t.optional_params,
            tags=t.tags,
            version=t.version,
        )
        for t in templates
    ]

    return TemplateListResponse(templates=template_infos, total=len(template_infos))


@templates_router.get(
    "/{template_name}",
    response_model=TemplateInfo,
    summary="Get template",
    description="Get details of a specific workflow template.",
    responses={404: {"model": ErrorResponse}},
)
def get_template(template_name: str) -> TemplateInfo:
    """Get a specific template by name."""
    registry = get_default_template_registry()
    template = registry.get(template_name)

    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_name}' not found",
        )

    return TemplateInfo(
        id=template.id,
        name=template.name,
        description=template.description,
        category=template.category,
        required_params=template.required_params,
        optional_params=template.optional_params,
        tags=template.tags,
        version=template.version,
    )


@templates_router.post(
    "/instantiate",
    response_model=TemplateInstantiateResponse,
    summary="Instantiate template",
    description="Create a workflow from a template with the given parameters.",
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
def instantiate_template(
    request: TemplateInstantiateRequest,
) -> TemplateInstantiateResponse:
    """Instantiate a workflow from a template."""
    registry = get_default_template_registry()
    template = registry.get(request.template_name)

    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{request.template_name}' not found",
        )

    try:
        workflow = template.instantiate(
            params=request.params,
            workflow_name=request.workflow_name,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    _workflows[workflow.id] = workflow

    # Run immediately if requested
    if request.run_immediately:
        orchestrator = get_orchestrator()
        result = orchestrator.run_workflow(workflow)
        _workflow_results[workflow.id] = WorkflowResultResponse(
            workflow_id=workflow.id,
            success=result.success,
            tasks_completed=result.tasks_completed,
            tasks_failed=result.tasks_failed,
            total_iterations=result.total_iterations,
            duration_seconds=result.duration_seconds,
            errors=result.errors,
            outputs=result.outputs,
        )

    return TemplateInstantiateResponse(
        workflow_id=workflow.id,
        workflow_name=workflow.name,
        task_count=len(workflow.tasks),
        status=workflow.status,
    )


# ===== Plugins Router =====

plugins_router = APIRouter(prefix="/plugins", tags=["Plugins"])


@plugins_router.get(
    "",
    response_model=PluginListResponse,
    summary="List plugins",
    description="Get list of all registered plugins.",
)
def list_plugins() -> PluginListResponse:
    """List all plugins."""
    registry = get_plugin_registry()
    plugins = registry.list_all()

    plugin_infos = [
        PluginInfo(
            id=p.metadata.id,
            name=p.metadata.name,
            version=p.metadata.version,
            description=p.metadata.description,
            plugin_type=p.metadata.plugin_type.value,
            author=p.metadata.author,
            status=p.status.value,
            tags=p.metadata.tags,
        )
        for p in plugins
    ]

    return PluginListResponse(
        plugins=plugin_infos,
        total=len(plugin_infos),
        active_count=registry.get_active_count(),
    )

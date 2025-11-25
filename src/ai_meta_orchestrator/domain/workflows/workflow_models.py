"""Workflow domain models and orchestration logic."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from ai_meta_orchestrator.domain.tasks.task_models import Task, TaskStatus


class WorkflowStatus(str, Enum):
    """Status of a workflow."""

    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowMode(str, Enum):
    """Execution mode for the workflow."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"


@dataclass
class WorkflowConfig:
    """Configuration for workflow execution.

    Attributes:
        mode: Execution mode (sequential, parallel, hierarchical).
        max_iterations: Maximum number of iterations for correction loops.
        enable_evaluation: Whether to enable task evaluation.
        enable_correction_loop: Whether to enable correction/feedback loop.
        verbose: Whether to enable verbose output.
        memory: Whether to enable workflow memory.
    """

    mode: WorkflowMode = WorkflowMode.SEQUENTIAL
    max_iterations: int = 10
    enable_evaluation: bool = True
    enable_correction_loop: bool = True
    verbose: bool = True
    memory: bool = True


@dataclass
class WorkflowResult:
    """Result of a workflow execution.

    Attributes:
        success: Whether the workflow completed successfully.
        tasks_completed: Number of tasks completed.
        tasks_failed: Number of tasks failed.
        total_iterations: Total iterations used.
        outputs: Outputs from each completed task.
        errors: List of errors encountered.
        duration_seconds: Total duration in seconds.
    """

    success: bool
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_iterations: int = 0
    outputs: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class Workflow:
    """Represents a workflow containing multiple tasks.

    Attributes:
        id: Unique identifier for the workflow.
        name: Human-readable name of the workflow.
        description: Description of the workflow purpose.
        tasks: List of tasks in the workflow.
        config: Workflow configuration.
        status: Current status of the workflow.
        result: Result of workflow execution.
        current_iteration: Current iteration number.
        created_at: Timestamp when the workflow was created.
        started_at: Timestamp when the workflow started.
        completed_at: Timestamp when the workflow completed.
        metadata: Additional workflow metadata.
    """

    name: str
    description: str
    tasks: list[Task] = field(default_factory=list)
    config: WorkflowConfig = field(default_factory=WorkflowConfig)
    id: UUID = field(default_factory=uuid4)
    status: WorkflowStatus = WorkflowStatus.NOT_STARTED
    result: WorkflowResult | None = None
    current_iteration: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_task(self, task: Task) -> None:
        """Add a task to the workflow."""
        self.tasks.append(task)

    def get_task_by_id(self, task_id: UUID) -> Task | None:
        """Get a task by its ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_pending_tasks(self) -> list[Task]:
        """Get all pending tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.PENDING]

    def get_tasks_needing_revision(self) -> list[Task]:
        """Get all tasks that need revision."""
        return [t for t in self.tasks if t.status == TaskStatus.NEEDS_REVISION]

    def start(self) -> None:
        """Start the workflow execution."""
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self, result: WorkflowResult) -> None:
        """Mark the workflow as completed."""
        self.result = result
        self.status = WorkflowStatus.COMPLETED if result.success else WorkflowStatus.FAILED
        self.completed_at = datetime.now()

    def increment_iteration(self) -> bool:
        """Increment the iteration counter.

        Returns:
            True if iteration was incremented, False if max iterations reached.
        """
        if self.current_iteration >= self.config.max_iterations:
            return False
        self.current_iteration += 1
        return True

    def is_complete(self) -> bool:
        """Check if all tasks are completed or failed."""
        return all(
            t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
            for t in self.tasks
        )

    def get_progress(self) -> tuple[int, int]:
        """Get workflow progress as (completed, total) tasks."""
        completed = sum(
            1 for t in self.tasks
            if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
        )
        return completed, len(self.tasks)

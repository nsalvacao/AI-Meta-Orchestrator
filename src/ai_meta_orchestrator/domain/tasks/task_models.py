"""Task domain models and status definitions."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from ai_meta_orchestrator.domain.agents.agent_models import AgentRole


class TaskStatus(str, Enum):
    """Status of a task in the workflow."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVISION = "needs_revision"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """Priority level of a task."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TaskResult:
    """Result of a task execution.

    Attributes:
        success: Whether the task completed successfully.
        output: The output produced by the task.
        error: Error message if the task failed.
        feedback: Feedback for task revision.
        metadata: Additional metadata about the result.
    """

    success: bool
    output: Any = None
    error: str | None = None
    feedback: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result of evaluating a task's output.

    Attributes:
        passed: Whether the evaluation passed.
        score: Numeric score (0-100) of the evaluation.
        feedback: Detailed feedback about the evaluation.
        issues: List of specific issues found.
        suggestions: List of improvement suggestions.
    """

    passed: bool
    score: float = 0.0
    feedback: str = ""
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class Task:
    """Represents a task in the orchestrator workflow.

    Attributes:
        id: Unique identifier for the task.
        name: Human-readable name of the task.
        description: Detailed description of what the task involves.
        assigned_to: The agent role this task is assigned to.
        status: Current status of the task.
        priority: Priority level of the task.
        expected_output: Description of expected output format.
        context_tasks: IDs of tasks that provide context for this task.
        result: Result of task execution if completed.
        evaluation: Evaluation result if evaluated.
        revision_count: Number of times this task has been revised.
        max_revisions: Maximum allowed revisions before escalation.
        created_at: Timestamp when the task was created.
        updated_at: Timestamp of the last update.
        metadata: Additional task metadata.
    """

    name: str
    description: str
    assigned_to: AgentRole
    expected_output: str = ""
    id: UUID = field(default_factory=uuid4)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    context_tasks: list[UUID] = field(default_factory=list)
    result: TaskResult | None = None
    evaluation: EvaluationResult | None = None
    revision_count: int = 0
    max_revisions: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def mark_in_progress(self) -> None:
        """Mark the task as in progress."""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now()

    def complete(self, result: TaskResult) -> None:
        """Mark the task as completed with the given result."""
        self.result = result
        self.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
        self.updated_at = datetime.now()

    def request_revision(self, evaluation: EvaluationResult) -> bool:
        """Request a revision of the task.

        Returns:
            True if revision was requested, False if max revisions reached.
        """
        if self.revision_count >= self.max_revisions:
            return False
        self.evaluation = evaluation
        self.revision_count += 1
        self.status = TaskStatus.NEEDS_REVISION
        self.updated_at = datetime.now()
        return True

    def can_be_revised(self) -> bool:
        """Check if the task can still be revised."""
        return self.revision_count < self.max_revisions

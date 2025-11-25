"""Task port interface - Abstraction for task operations."""

from abc import ABC, abstractmethod
from uuid import UUID

from ai_meta_orchestrator.domain.tasks.task_models import EvaluationResult, Task, TaskResult


class TaskExecutorPort(ABC):
    """Abstract interface for task execution operations."""

    @abstractmethod
    def execute(self, task: Task) -> TaskResult:
        """Execute a task.

        Args:
            task: The task to execute.

        Returns:
            TaskResult containing the output or error.
        """
        pass

    @abstractmethod
    def get_task_status(self, task_id: UUID) -> Task | None:
        """Get the current status of a task.

        Args:
            task_id: The ID of the task.

        Returns:
            The task if found, None otherwise.
        """
        pass


class TaskEvaluatorPort(ABC):
    """Abstract interface for task evaluation operations."""

    @abstractmethod
    def evaluate(self, task: Task, result: TaskResult) -> EvaluationResult:
        """Evaluate the result of a task.

        Args:
            task: The task that was executed.
            result: The result of the task execution.

        Returns:
            EvaluationResult containing the evaluation outcome.
        """
        pass


class TaskDistributorPort(ABC):
    """Abstract interface for task distribution operations."""

    @abstractmethod
    def distribute(self, tasks: list[Task]) -> dict[UUID, UUID]:
        """Distribute tasks to appropriate agents.

        Args:
            tasks: The tasks to distribute.

        Returns:
            Mapping of task IDs to agent IDs.
        """
        pass

    @abstractmethod
    def reassign(self, task: Task, feedback: str) -> bool:
        """Reassign a task based on feedback.

        Args:
            task: The task to reassign.
            feedback: Feedback explaining why reassignment is needed.

        Returns:
            True if reassignment was successful, False otherwise.
        """
        pass

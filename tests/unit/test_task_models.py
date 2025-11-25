"""Unit tests for domain task models."""

from datetime import datetime
from uuid import UUID

from ai_meta_orchestrator.domain.agents.agent_models import AgentRole
from ai_meta_orchestrator.domain.tasks.task_models import (
    EvaluationResult,
    Task,
    TaskPriority,
    TaskResult,
    TaskStatus,
)


class TestTaskStatus:
    """Tests for TaskStatus enumeration."""

    def test_all_statuses_defined(self) -> None:
        """Verify all expected task statuses are defined."""
        expected = {"pending", "in_progress", "completed", "failed", "needs_revision", "blocked"}
        actual = {status.value for status in TaskStatus}
        assert actual == expected


class TestTaskPriority:
    """Tests for TaskPriority enumeration."""

    def test_all_priorities_defined(self) -> None:
        """Verify all expected priorities are defined."""
        expected = {"low", "medium", "high", "critical"}
        actual = {priority.value for priority in TaskPriority}
        assert actual == expected


class TestTaskResult:
    """Tests for TaskResult dataclass."""

    def test_successful_result(self) -> None:
        """Test creating a successful task result."""
        result = TaskResult(success=True, output="Task completed")
        assert result.success is True
        assert result.output == "Task completed"
        assert result.error is None
        assert result.feedback is None

    def test_failed_result(self) -> None:
        """Test creating a failed task result."""
        result = TaskResult(success=False, error="Something went wrong")
        assert result.success is False
        assert result.error == "Something went wrong"


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass."""

    def test_passed_evaluation(self) -> None:
        """Test a passing evaluation."""
        evaluation = EvaluationResult(
            passed=True,
            score=90.0,
            feedback="Great work!",
        )
        assert evaluation.passed is True
        assert evaluation.score == 90.0

    def test_failed_evaluation(self) -> None:
        """Test a failing evaluation."""
        evaluation = EvaluationResult(
            passed=False,
            score=40.0,
            feedback="Needs improvement",
            issues=["Missing error handling", "No tests"],
            suggestions=["Add try/catch", "Write unit tests"],
        )
        assert evaluation.passed is False
        assert len(evaluation.issues) == 2
        assert len(evaluation.suggestions) == 2


class TestTask:
    """Tests for Task dataclass."""

    def test_create_task(self) -> None:
        """Test creating a task."""
        task = Task(
            name="Test Task",
            description="A test task description",
            assigned_to=AgentRole.DEV,
        )
        assert task.name == "Test Task"
        assert task.assigned_to == AgentRole.DEV
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert isinstance(task.id, UUID)
        assert isinstance(task.created_at, datetime)

    def test_mark_in_progress(self) -> None:
        """Test marking a task as in progress."""
        task = Task(
            name="Test",
            description="Test",
            assigned_to=AgentRole.DEV,
        )
        original_updated = task.updated_at
        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.updated_at >= original_updated

    def test_complete_task_success(self) -> None:
        """Test completing a task successfully."""
        task = Task(
            name="Test",
            description="Test",
            assigned_to=AgentRole.DEV,
        )
        result = TaskResult(success=True, output="Done")
        task.complete(result)
        assert task.status == TaskStatus.COMPLETED
        assert task.result == result

    def test_complete_task_failure(self) -> None:
        """Test completing a task with failure."""
        task = Task(
            name="Test",
            description="Test",
            assigned_to=AgentRole.DEV,
        )
        result = TaskResult(success=False, error="Failed")
        task.complete(result)
        assert task.status == TaskStatus.FAILED

    def test_request_revision(self) -> None:
        """Test requesting a task revision."""
        task = Task(
            name="Test",
            description="Test",
            assigned_to=AgentRole.DEV,
        )
        evaluation = EvaluationResult(passed=False, feedback="Needs work")

        result = task.request_revision(evaluation)

        assert result is True
        assert task.status == TaskStatus.NEEDS_REVISION
        assert task.revision_count == 1
        assert task.evaluation == evaluation

    def test_request_revision_max_reached(self) -> None:
        """Test revision when max revisions reached."""
        task = Task(
            name="Test",
            description="Test",
            assigned_to=AgentRole.DEV,
            max_revisions=2,
        )
        evaluation = EvaluationResult(passed=False, feedback="Needs work")

        # Use up revisions
        task.request_revision(evaluation)
        task.request_revision(evaluation)

        # Third revision should fail
        result = task.request_revision(evaluation)
        assert result is False
        assert task.revision_count == 2

    def test_can_be_revised(self) -> None:
        """Test checking if task can be revised."""
        task = Task(
            name="Test",
            description="Test",
            assigned_to=AgentRole.DEV,
            max_revisions=1,
        )
        assert task.can_be_revised() is True

        task.revision_count = 1
        assert task.can_be_revised() is False

"""Unit tests for domain workflow models."""

from uuid import uuid4

from ai_meta_orchestrator.domain.agents.agent_models import AgentRole
from ai_meta_orchestrator.domain.tasks.task_models import Task, TaskStatus
from ai_meta_orchestrator.domain.workflows.workflow_models import (
    Workflow,
    WorkflowConfig,
    WorkflowMode,
    WorkflowResult,
    WorkflowStatus,
)


class TestWorkflowStatus:
    """Tests for WorkflowStatus enumeration."""

    def test_all_statuses_defined(self) -> None:
        """Verify all expected workflow statuses are defined."""
        expected = {"not_started", "running", "paused", "completed", "failed"}
        actual = {status.value for status in WorkflowStatus}
        assert actual == expected


class TestWorkflowMode:
    """Tests for WorkflowMode enumeration."""

    def test_all_modes_defined(self) -> None:
        """Verify all expected workflow modes are defined."""
        expected = {"sequential", "parallel", "hierarchical"}
        actual = {mode.value for mode in WorkflowMode}
        assert actual == expected


class TestWorkflowConfig:
    """Tests for WorkflowConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default workflow configuration."""
        config = WorkflowConfig()
        assert config.mode == WorkflowMode.SEQUENTIAL
        assert config.max_iterations == 10
        assert config.enable_evaluation is True
        assert config.enable_correction_loop is True
        assert config.verbose is True
        assert config.memory is True

    def test_custom_config(self) -> None:
        """Test custom workflow configuration."""
        config = WorkflowConfig(
            mode=WorkflowMode.PARALLEL,
            max_iterations=5,
            enable_evaluation=False,
        )
        assert config.mode == WorkflowMode.PARALLEL
        assert config.max_iterations == 5
        assert config.enable_evaluation is False


class TestWorkflowResult:
    """Tests for WorkflowResult dataclass."""

    def test_successful_result(self) -> None:
        """Test a successful workflow result."""
        result = WorkflowResult(
            success=True,
            tasks_completed=5,
            tasks_failed=0,
            duration_seconds=10.5,
        )
        assert result.success is True
        assert result.tasks_completed == 5
        assert result.tasks_failed == 0

    def test_failed_result(self) -> None:
        """Test a failed workflow result."""
        result = WorkflowResult(
            success=False,
            tasks_completed=3,
            tasks_failed=2,
            errors=["Task A failed", "Task B failed"],
        )
        assert result.success is False
        assert len(result.errors) == 2


class TestWorkflow:
    """Tests for Workflow dataclass."""

    def test_create_workflow(self) -> None:
        """Test creating a workflow."""
        workflow = Workflow(
            name="Test Workflow",
            description="A test workflow",
        )
        assert workflow.name == "Test Workflow"
        assert workflow.status == WorkflowStatus.NOT_STARTED
        assert workflow.tasks == []
        assert workflow.current_iteration == 0

    def test_add_task(self) -> None:
        """Test adding a task to workflow."""
        workflow = Workflow(name="Test", description="Test")
        task = Task(
            name="Task 1",
            description="First task",
            assigned_to=AgentRole.DEV,
        )

        workflow.add_task(task)

        assert len(workflow.tasks) == 1
        assert workflow.tasks[0] == task

    def test_get_task_by_id(self) -> None:
        """Test getting a task by ID."""
        workflow = Workflow(name="Test", description="Test")
        task = Task(
            name="Task 1",
            description="First task",
            assigned_to=AgentRole.DEV,
        )
        workflow.add_task(task)

        found = workflow.get_task_by_id(task.id)

        assert found == task

    def test_get_task_by_id_not_found(self) -> None:
        """Test getting a non-existent task."""
        workflow = Workflow(name="Test", description="Test")

        found = workflow.get_task_by_id(uuid4())

        assert found is None

    def test_get_pending_tasks(self) -> None:
        """Test getting pending tasks."""
        workflow = Workflow(name="Test", description="Test")

        task1 = Task(name="Task 1", description="First", assigned_to=AgentRole.DEV)
        task2 = Task(name="Task 2", description="Second", assigned_to=AgentRole.QA)
        task2.status = TaskStatus.COMPLETED

        workflow.add_task(task1)
        workflow.add_task(task2)

        pending = workflow.get_pending_tasks()

        assert len(pending) == 1
        assert pending[0] == task1

    def test_start_workflow(self) -> None:
        """Test starting a workflow."""
        workflow = Workflow(name="Test", description="Test")

        workflow.start()

        assert workflow.status == WorkflowStatus.RUNNING
        assert workflow.started_at is not None

    def test_complete_workflow(self) -> None:
        """Test completing a workflow."""
        workflow = Workflow(name="Test", description="Test")
        result = WorkflowResult(success=True, tasks_completed=1)

        workflow.complete(result)

        assert workflow.status == WorkflowStatus.COMPLETED
        assert workflow.result == result
        assert workflow.completed_at is not None

    def test_complete_workflow_with_failure(self) -> None:
        """Test completing a workflow with failures."""
        workflow = Workflow(name="Test", description="Test")
        result = WorkflowResult(success=False, tasks_failed=1)

        workflow.complete(result)

        assert workflow.status == WorkflowStatus.FAILED

    def test_increment_iteration(self) -> None:
        """Test incrementing workflow iteration."""
        workflow = Workflow(name="Test", description="Test")
        workflow.config.max_iterations = 3

        assert workflow.increment_iteration() is True
        assert workflow.current_iteration == 1

        assert workflow.increment_iteration() is True
        assert workflow.current_iteration == 2

        assert workflow.increment_iteration() is True
        assert workflow.current_iteration == 3

        # Max reached
        assert workflow.increment_iteration() is False
        assert workflow.current_iteration == 3

    def test_is_complete(self) -> None:
        """Test checking if workflow is complete."""
        workflow = Workflow(name="Test", description="Test")
        task1 = Task(name="Task 1", description="First", assigned_to=AgentRole.DEV)
        task2 = Task(name="Task 2", description="Second", assigned_to=AgentRole.QA)

        workflow.add_task(task1)
        workflow.add_task(task2)

        assert workflow.is_complete() is False

        task1.status = TaskStatus.COMPLETED
        assert workflow.is_complete() is False

        task2.status = TaskStatus.FAILED
        assert workflow.is_complete() is True

    def test_get_progress(self) -> None:
        """Test getting workflow progress."""
        workflow = Workflow(name="Test", description="Test")
        task1 = Task(name="Task 1", description="First", assigned_to=AgentRole.DEV)
        task2 = Task(name="Task 2", description="Second", assigned_to=AgentRole.QA)
        task3 = Task(name="Task 3", description="Third", assigned_to=AgentRole.DOCS)

        workflow.add_task(task1)
        workflow.add_task(task2)
        workflow.add_task(task3)

        completed, total = workflow.get_progress()
        assert completed == 0
        assert total == 3

        task1.status = TaskStatus.COMPLETED
        task2.status = TaskStatus.FAILED

        completed, total = workflow.get_progress()
        assert completed == 2
        assert total == 3

    def test_pause_workflow(self) -> None:
        """Test pausing a running workflow."""
        workflow = Workflow(name="Test", description="Test")
        workflow.start()

        assert workflow.pause() is True
        assert workflow.status == WorkflowStatus.PAUSED

    def test_pause_workflow_not_running(self) -> None:
        """Test pausing a workflow that is not running."""
        workflow = Workflow(name="Test", description="Test")
        # Workflow is NOT_STARTED
        assert workflow.pause() is False
        assert workflow.status == WorkflowStatus.NOT_STARTED

    def test_resume_workflow(self) -> None:
        """Test resuming a paused workflow."""
        workflow = Workflow(name="Test", description="Test")
        workflow.start()
        workflow.pause()

        assert workflow.resume() is True
        assert workflow.status == WorkflowStatus.RUNNING

    def test_resume_workflow_not_paused(self) -> None:
        """Test resuming a workflow that is not paused."""
        workflow = Workflow(name="Test", description="Test")
        workflow.start()
        # Workflow is RUNNING, not PAUSED
        assert workflow.resume() is False
        assert workflow.status == WorkflowStatus.RUNNING

    def test_get_ready_tasks_no_dependencies(self) -> None:
        """Test getting ready tasks when tasks have no dependencies."""
        workflow = Workflow(name="Test", description="Test")
        task1 = Task(name="Task 1", description="First", assigned_to=AgentRole.DEV)
        task2 = Task(name="Task 2", description="Second", assigned_to=AgentRole.QA)

        workflow.add_task(task1)
        workflow.add_task(task2)

        ready = workflow.get_ready_tasks()
        assert len(ready) == 2

    def test_get_ready_tasks_with_dependencies(self) -> None:
        """Test getting ready tasks with dependencies."""
        workflow = Workflow(name="Test", description="Test")
        task1 = Task(name="Task 1", description="First", assigned_to=AgentRole.DEV)
        task2 = Task(
            name="Task 2",
            description="Second",
            assigned_to=AgentRole.QA,
            context_tasks=[task1.id],  # Depends on task1
        )
        task3 = Task(
            name="Task 3",
            description="Third",
            assigned_to=AgentRole.DOCS,
            context_tasks=[task2.id],  # Depends on task2
        )

        workflow.add_task(task1)
        workflow.add_task(task2)
        workflow.add_task(task3)

        # Initially only task1 is ready
        ready = workflow.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0] == task1

        # Complete task1
        task1.status = TaskStatus.COMPLETED
        ready = workflow.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0] == task2

        # Complete task2
        task2.status = TaskStatus.COMPLETED
        ready = workflow.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0] == task3

    def test_get_ready_tasks_all_completed(self) -> None:
        """Test getting ready tasks when all are completed."""
        workflow = Workflow(name="Test", description="Test")
        task1 = Task(name="Task 1", description="First", assigned_to=AgentRole.DEV)
        task1.status = TaskStatus.COMPLETED

        workflow.add_task(task1)

        ready = workflow.get_ready_tasks()
        assert len(ready) == 0

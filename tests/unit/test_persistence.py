"""Tests for persistence adapters."""

import os
import tempfile

import pytest

from ai_meta_orchestrator.adapters.persistence.persistence_adapter import (
    InMemoryPersistence,
    PersistenceConfig,
    SQLitePersistence,
    create_persistence_adapter,
)
from ai_meta_orchestrator.domain.agents.agent_models import AgentRole
from ai_meta_orchestrator.domain.tasks.task_models import Task
from ai_meta_orchestrator.domain.workflows.workflow_models import (
    Workflow,
    WorkflowConfig,
    WorkflowMode,
    WorkflowResult,
    WorkflowStatus,
)


class TestInMemoryPersistence:
    """Tests for InMemoryPersistence."""

    def test_save_and_get_workflow(self) -> None:
        """Test saving and retrieving a workflow."""
        persistence = InMemoryPersistence()
        workflow = Workflow(
            name="Test Workflow",
            description="Test description",
        )

        assert persistence.save_workflow(workflow)
        retrieved = persistence.get_workflow(workflow.id)

        assert retrieved is not None
        assert retrieved.name == "Test Workflow"
        assert retrieved.id == workflow.id

    def test_list_workflows(self) -> None:
        """Test listing workflows."""
        persistence = InMemoryPersistence()
        workflow1 = Workflow(name="Workflow 1", description="Desc 1")
        workflow2 = Workflow(name="Workflow 2", description="Desc 2")

        persistence.save_workflow(workflow1)
        persistence.save_workflow(workflow2)

        workflows = persistence.list_workflows()
        assert len(workflows) == 2

    def test_list_workflows_with_status_filter(self) -> None:
        """Test listing workflows with status filter."""
        persistence = InMemoryPersistence()
        workflow1 = Workflow(name="Workflow 1", description="Desc 1")
        workflow2 = Workflow(name="Workflow 2", description="Desc 2")
        workflow2.start()  # Set to RUNNING

        persistence.save_workflow(workflow1)
        persistence.save_workflow(workflow2)

        running = persistence.list_workflows(status=WorkflowStatus.RUNNING)
        assert len(running) == 1
        assert running[0].status == WorkflowStatus.RUNNING

    def test_delete_workflow(self) -> None:
        """Test deleting a workflow."""
        persistence = InMemoryPersistence()
        workflow = Workflow(name="Test", description="Test")

        persistence.save_workflow(workflow)
        assert persistence.delete_workflow(workflow.id)
        assert persistence.get_workflow(workflow.id) is None

    def test_delete_nonexistent_workflow(self) -> None:
        """Test deleting a workflow that doesn't exist."""
        persistence = InMemoryPersistence()
        workflow = Workflow(name="Test", description="Test")

        assert not persistence.delete_workflow(workflow.id)

    def test_save_and_get_task(self) -> None:
        """Test saving and retrieving a task."""
        persistence = InMemoryPersistence()
        workflow = Workflow(name="Test", description="Test")
        task = Task(
            name="Test Task",
            description="Task description",
            assigned_to=AgentRole.DEV,
        )

        persistence.save_workflow(workflow)
        assert persistence.save_task(task, workflow.id)

        retrieved = persistence.get_task(task.id)
        assert retrieved is not None
        assert retrieved.name == "Test Task"

    def test_update_workflow_result(self) -> None:
        """Test updating workflow result."""
        persistence = InMemoryPersistence()
        workflow = Workflow(name="Test", description="Test")
        persistence.save_workflow(workflow)

        result = WorkflowResult(
            success=True,
            tasks_completed=5,
            tasks_failed=0,
        )

        assert persistence.update_workflow_result(workflow.id, result)
        retrieved = persistence.get_workflow(workflow.id)
        assert retrieved is not None
        assert retrieved.result is not None
        assert retrieved.result.success


class TestSQLitePersistence:
    """Tests for SQLitePersistence."""

    @pytest.fixture
    def temp_db(self) -> str:
        """Create a temporary database file."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)

    def test_save_and_get_workflow(self, temp_db: str) -> None:
        """Test saving and retrieving a workflow."""
        config = PersistenceConfig(database_path=temp_db)
        persistence = SQLitePersistence(config)

        workflow = Workflow(
            name="Test Workflow",
            description="Test description",
            config=WorkflowConfig(mode=WorkflowMode.PARALLEL),
        )

        assert persistence.save_workflow(workflow)
        retrieved = persistence.get_workflow(workflow.id)

        assert retrieved is not None
        assert retrieved.name == "Test Workflow"
        assert retrieved.config.mode == WorkflowMode.PARALLEL

        persistence.close()

    def test_save_workflow_with_tasks(self, temp_db: str) -> None:
        """Test saving a workflow with tasks."""
        config = PersistenceConfig(database_path=temp_db)
        persistence = SQLitePersistence(config)

        workflow = Workflow(name="Test", description="Test")
        task1 = Task(
            name="Task 1",
            description="Task 1 desc",
            assigned_to=AgentRole.PM,
        )
        task2 = Task(
            name="Task 2",
            description="Task 2 desc",
            assigned_to=AgentRole.DEV,
        )
        workflow.add_task(task1)
        workflow.add_task(task2)

        persistence.save_workflow(workflow)
        retrieved = persistence.get_workflow(workflow.id)

        assert retrieved is not None
        assert len(retrieved.tasks) == 2
        assert retrieved.tasks[0].name == "Task 1"
        assert retrieved.tasks[1].name == "Task 2"

        persistence.close()

    def test_list_workflows(self, temp_db: str) -> None:
        """Test listing workflows."""
        config = PersistenceConfig(database_path=temp_db)
        persistence = SQLitePersistence(config)

        workflow1 = Workflow(name="Workflow 1", description="Desc 1")
        workflow2 = Workflow(name="Workflow 2", description="Desc 2")

        persistence.save_workflow(workflow1)
        persistence.save_workflow(workflow2)

        workflows = persistence.list_workflows()
        assert len(workflows) == 2

        persistence.close()

    def test_delete_workflow(self, temp_db: str) -> None:
        """Test deleting a workflow."""
        config = PersistenceConfig(database_path=temp_db)
        persistence = SQLitePersistence(config)

        workflow = Workflow(name="Test", description="Test")
        task = Task(
            name="Task",
            description="Task",
            assigned_to=AgentRole.DEV,
        )
        workflow.add_task(task)

        persistence.save_workflow(workflow)
        assert persistence.delete_workflow(workflow.id)
        assert persistence.get_workflow(workflow.id) is None
        assert persistence.get_task(task.id) is None

        persistence.close()

    def test_update_workflow_result(self, temp_db: str) -> None:
        """Test updating workflow result."""
        config = PersistenceConfig(database_path=temp_db)
        persistence = SQLitePersistence(config)

        workflow = Workflow(name="Test", description="Test")
        persistence.save_workflow(workflow)

        result = WorkflowResult(
            success=True,
            tasks_completed=5,
            tasks_failed=1,
            total_iterations=3,
            duration_seconds=10.5,
            outputs={"key": "value"},
            errors=["error1"],
        )

        assert persistence.update_workflow_result(workflow.id, result)
        retrieved = persistence.get_workflow(workflow.id)

        assert retrieved is not None
        assert retrieved.result is not None
        assert retrieved.result.success
        assert retrieved.result.tasks_completed == 5
        assert retrieved.result.tasks_failed == 1
        assert retrieved.result.outputs == {"key": "value"}
        assert retrieved.result.errors == ["error1"]

        persistence.close()


class TestCreatePersistenceAdapter:
    """Tests for create_persistence_adapter factory."""

    def test_create_memory_adapter(self) -> None:
        """Test creating an in-memory adapter."""
        adapter = create_persistence_adapter("memory")
        assert isinstance(adapter, InMemoryPersistence)

    def test_create_sqlite_adapter(self) -> None:
        """Test creating a SQLite adapter."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            adapter = create_persistence_adapter("sqlite", database_path=f.name)
            assert isinstance(adapter, SQLitePersistence)
            adapter.close()
            os.remove(f.name)

    def test_default_is_memory(self) -> None:
        """Test that default adapter is in-memory."""
        adapter = create_persistence_adapter()
        assert isinstance(adapter, InMemoryPersistence)

    def test_unsupported_backend_raises(self) -> None:
        """Test that unsupported backend raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported persistence backend"):
            create_persistence_adapter("postgresql")

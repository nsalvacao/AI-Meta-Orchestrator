"""Persistence adapters for workflow and task storage.

This module provides persistence implementations:
- InMemoryPersistence: Simple in-memory storage for development/testing
- SQLitePersistence: SQLite-based persistence for production use
"""

import json
import logging
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from ai_meta_orchestrator.domain.agents.agent_models import AgentRole
from ai_meta_orchestrator.domain.tasks.task_models import Task, TaskPriority, TaskStatus
from ai_meta_orchestrator.domain.workflows.workflow_models import (
    Workflow,
    WorkflowConfig,
    WorkflowMode,
    WorkflowResult,
    WorkflowStatus,
)


@dataclass
class PersistenceConfig:
    """Configuration for persistence adapters.

    Attributes:
        database_path: Path to the SQLite database file.
        auto_migrate: Whether to auto-migrate the database schema.
        connection_timeout: Connection timeout in seconds.
    """

    database_path: str = "orchestrator.db"
    auto_migrate: bool = True
    connection_timeout: float = 30.0


class PersistencePort(ABC):
    """Interface for persistence operations.

    This abstract class defines the contract for persistence adapters
    that store and retrieve workflows and tasks.
    """

    @abstractmethod
    def save_workflow(self, workflow: Workflow) -> bool:
        """Save a workflow to persistent storage.

        Args:
            workflow: The workflow to save.

        Returns:
            True if save was successful.
        """
        pass

    @abstractmethod
    def get_workflow(self, workflow_id: UUID) -> Workflow | None:
        """Retrieve a workflow by ID.

        Args:
            workflow_id: The workflow's unique identifier.

        Returns:
            The workflow or None if not found.
        """
        pass

    @abstractmethod
    def list_workflows(
        self,
        status: WorkflowStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Workflow]:
        """List workflows with optional filtering.

        Args:
            status: Optional status filter.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of workflows.
        """
        pass

    @abstractmethod
    def delete_workflow(self, workflow_id: UUID) -> bool:
        """Delete a workflow.

        Args:
            workflow_id: The workflow's unique identifier.

        Returns:
            True if deleted successfully.
        """
        pass

    @abstractmethod
    def save_task(self, task: Task, workflow_id: UUID) -> bool:
        """Save a task associated with a workflow.

        Args:
            task: The task to save.
            workflow_id: The parent workflow's ID.

        Returns:
            True if save was successful.
        """
        pass

    @abstractmethod
    def get_task(self, task_id: UUID) -> Task | None:
        """Retrieve a task by ID.

        Args:
            task_id: The task's unique identifier.

        Returns:
            The task or None if not found.
        """
        pass

    @abstractmethod
    def update_workflow_result(
        self,
        workflow_id: UUID,
        result: WorkflowResult,
    ) -> bool:
        """Update workflow with execution result.

        Args:
            workflow_id: The workflow's unique identifier.
            result: The workflow result to save.

        Returns:
            True if update was successful.
        """
        pass


class InMemoryPersistence(PersistencePort):
    """In-memory persistence adapter for development and testing.

    WARNING: Data is not persisted across application restarts.
    """

    def __init__(self) -> None:
        """Initialize in-memory storage."""
        self._workflows: dict[UUID, Workflow] = {}
        self._tasks: dict[UUID, tuple[Task, UUID]] = {}  # task_id -> (task, workflow_id)
        self._results: dict[UUID, WorkflowResult] = {}
        self._logger = logging.getLogger(__name__)

    def save_workflow(self, workflow: Workflow) -> bool:
        """Save a workflow to memory."""
        self._workflows[workflow.id] = workflow
        # Save all tasks
        for task in workflow.tasks:
            self._tasks[task.id] = (task, workflow.id)
        self._logger.debug(f"Saved workflow {workflow.id} to memory")
        return True

    def get_workflow(self, workflow_id: UUID) -> Workflow | None:
        """Retrieve a workflow from memory."""
        return self._workflows.get(workflow_id)

    def list_workflows(
        self,
        status: WorkflowStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Workflow]:
        """List workflows from memory."""
        workflows = list(self._workflows.values())
        if status:
            workflows = [w for w in workflows if w.status == status]
        return workflows[offset:offset + limit]

    def delete_workflow(self, workflow_id: UUID) -> bool:
        """Delete a workflow from memory."""
        if workflow_id in self._workflows:
            workflow = self._workflows.pop(workflow_id)
            for task in workflow.tasks:
                self._tasks.pop(task.id, None)
            self._results.pop(workflow_id, None)
            return True
        return False

    def save_task(self, task: Task, workflow_id: UUID) -> bool:
        """Save a task to memory."""
        self._tasks[task.id] = (task, workflow_id)
        return True

    def get_task(self, task_id: UUID) -> Task | None:
        """Retrieve a task from memory."""
        result = self._tasks.get(task_id)
        return result[0] if result else None

    def update_workflow_result(
        self,
        workflow_id: UUID,
        result: WorkflowResult,
    ) -> bool:
        """Update workflow result in memory."""
        if workflow_id in self._workflows:
            workflow = self._workflows[workflow_id]
            workflow.result = result
            self._results[workflow_id] = result
            return True
        return False


class SQLitePersistence(PersistencePort):
    """SQLite-based persistence adapter for production use.

    This adapter stores workflows and tasks in a SQLite database,
    providing persistence across application restarts.
    """

    def __init__(self, config: PersistenceConfig | None = None) -> None:
        """Initialize SQLite persistence.

        Args:
            config: Optional persistence configuration.
        """
        self._config = config or PersistenceConfig()
        self._logger = logging.getLogger(__name__)
        self._connection: sqlite3.Connection | None = None

        if self._config.auto_migrate:
            self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create a database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(
                self._config.database_path,
                timeout=self._config.connection_timeout,
            )
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def _init_database(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create workflows table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                mode TEXT NOT NULL,
                max_iterations INTEGER DEFAULT 10,
                enable_evaluation INTEGER DEFAULT 1,
                enable_correction_loop INTEGER DEFAULT 1,
                verbose INTEGER DEFAULT 1,
                memory INTEGER DEFAULT 1,
                current_iteration INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                metadata TEXT
            )
        """)

        # Create tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                assigned_to TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                expected_output TEXT,
                revision_count INTEGER DEFAULT 0,
                max_revisions INTEGER DEFAULT 3,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                context_tasks TEXT,
                metadata TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows (id)
            )
        """)

        # Create workflow_results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_results (
                workflow_id TEXT PRIMARY KEY,
                success INTEGER NOT NULL,
                tasks_completed INTEGER DEFAULT 0,
                tasks_failed INTEGER DEFAULT 0,
                total_iterations INTEGER DEFAULT 0,
                duration_seconds REAL DEFAULT 0.0,
                outputs TEXT,
                errors TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows (id)
            )
        """)

        conn.commit()
        self._logger.info("Database schema initialized")

    def _workflow_to_row(self, workflow: Workflow) -> dict[str, Any]:
        """Convert a workflow to a database row."""
        return {
            "id": str(workflow.id),
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status.value,
            "mode": workflow.config.mode.value,
            "max_iterations": workflow.config.max_iterations,
            "enable_evaluation": 1 if workflow.config.enable_evaluation else 0,
            "enable_correction_loop": 1 if workflow.config.enable_correction_loop else 0,
            "verbose": 1 if workflow.config.verbose else 0,
            "memory": 1 if workflow.config.memory else 0,
            "current_iteration": workflow.current_iteration,
            "created_at": workflow.created_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "metadata": json.dumps(workflow.metadata),
        }

    def _row_to_workflow(self, row: sqlite3.Row) -> Workflow:
        """Convert a database row to a workflow."""
        config = WorkflowConfig(
            mode=WorkflowMode(row["mode"]),
            max_iterations=row["max_iterations"],
            enable_evaluation=bool(row["enable_evaluation"]),
            enable_correction_loop=bool(row["enable_correction_loop"]),
            verbose=bool(row["verbose"]),
            memory=bool(row["memory"]),
        )

        workflow = Workflow(
            id=UUID(row["id"]),
            name=row["name"],
            description=row["description"] or "",
            config=config,
            status=WorkflowStatus(row["status"]),
            current_iteration=row["current_iteration"],
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=(
                datetime.fromisoformat(row["started_at"])
                if row["started_at"]
                else None
            ),
            completed_at=(
                datetime.fromisoformat(row["completed_at"])
                if row["completed_at"]
                else None
            ),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

        # Load tasks for this workflow
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tasks WHERE workflow_id = ?",
            (str(workflow.id),),
        )

        for task_row in cursor.fetchall():
            task = self._row_to_task(task_row)
            workflow.tasks.append(task)

        # Load result if exists
        cursor.execute(
            "SELECT * FROM workflow_results WHERE workflow_id = ?",
            (str(workflow.id),),
        )
        result_row = cursor.fetchone()
        if result_row:
            workflow.result = WorkflowResult(
                success=bool(result_row["success"]),
                tasks_completed=result_row["tasks_completed"],
                tasks_failed=result_row["tasks_failed"],
                total_iterations=result_row["total_iterations"],
                duration_seconds=result_row["duration_seconds"],
                outputs=json.loads(result_row["outputs"]) if result_row["outputs"] else {},
                errors=json.loads(result_row["errors"]) if result_row["errors"] else [],
            )

        return workflow

    def _task_to_row(self, task: Task, workflow_id: UUID) -> dict[str, Any]:
        """Convert a task to a database row."""
        return {
            "id": str(task.id),
            "workflow_id": str(workflow_id),
            "name": task.name,
            "description": task.description,
            "assigned_to": task.assigned_to.value,
            "status": task.status.value,
            "priority": task.priority.value,
            "expected_output": task.expected_output,
            "revision_count": task.revision_count,
            "max_revisions": task.max_revisions,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "context_tasks": json.dumps([str(t) for t in task.context_tasks]),
            "metadata": json.dumps(task.metadata),
        }

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        """Convert a database row to a task."""
        return Task(
            id=UUID(row["id"]),
            name=row["name"],
            description=row["description"] or "",
            assigned_to=AgentRole(row["assigned_to"]),
            status=TaskStatus(row["status"]),
            priority=TaskPriority(row["priority"]),
            expected_output=row["expected_output"] or "",
            revision_count=row["revision_count"],
            max_revisions=row["max_revisions"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            context_tasks=[UUID(t) for t in json.loads(row["context_tasks"] or "[]")],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    def save_workflow(self, workflow: Workflow) -> bool:
        """Save a workflow to the database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            row = self._workflow_to_row(workflow)

            # Insert or replace workflow
            cursor.execute("""
                INSERT OR REPLACE INTO workflows
                (id, name, description, status, mode, max_iterations,
                 enable_evaluation, enable_correction_loop, verbose, memory,
                 current_iteration, created_at, started_at, completed_at, metadata)
                VALUES
                (:id, :name, :description, :status, :mode, :max_iterations,
                 :enable_evaluation, :enable_correction_loop, :verbose, :memory,
                 :current_iteration, :created_at, :started_at, :completed_at, :metadata)
            """, row)

            # Save all tasks
            for task in workflow.tasks:
                self.save_task(task, workflow.id)

            conn.commit()
            self._logger.debug(f"Saved workflow {workflow.id} to database")
            return True
        except Exception as e:
            self._logger.error(f"Failed to save workflow: {e}")
            return False

    def get_workflow(self, workflow_id: UUID) -> Workflow | None:
        """Retrieve a workflow from the database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM workflows WHERE id = ?",
                (str(workflow_id),),
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_workflow(row)
            return None
        except Exception as e:
            self._logger.error(f"Failed to get workflow: {e}")
            return None

    def list_workflows(
        self,
        status: WorkflowStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Workflow]:
        """List workflows from the database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if status:
                cursor.execute(
                    "SELECT * FROM workflows WHERE status = ? LIMIT ? OFFSET ?",
                    (status.value, limit, offset),
                )
            else:
                cursor.execute(
                    "SELECT * FROM workflows LIMIT ? OFFSET ?",
                    (limit, offset),
                )

            return [self._row_to_workflow(row) for row in cursor.fetchall()]
        except Exception as e:
            self._logger.error(f"Failed to list workflows: {e}")
            return []

    def delete_workflow(self, workflow_id: UUID) -> bool:
        """Delete a workflow from the database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Delete tasks first (foreign key constraint)
            cursor.execute(
                "DELETE FROM tasks WHERE workflow_id = ?",
                (str(workflow_id),),
            )

            # Delete result
            cursor.execute(
                "DELETE FROM workflow_results WHERE workflow_id = ?",
                (str(workflow_id),),
            )

            # Delete workflow
            cursor.execute(
                "DELETE FROM workflows WHERE id = ?",
                (str(workflow_id),),
            )

            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self._logger.error(f"Failed to delete workflow: {e}")
            return False

    def save_task(self, task: Task, workflow_id: UUID) -> bool:
        """Save a task to the database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            row = self._task_to_row(task, workflow_id)

            cursor.execute("""
                INSERT OR REPLACE INTO tasks
                (id, workflow_id, name, description, assigned_to, status, priority,
                 expected_output, revision_count, max_revisions, created_at, updated_at,
                 context_tasks, metadata)
                VALUES
                (:id, :workflow_id, :name, :description, :assigned_to, :status, :priority,
                 :expected_output, :revision_count, :max_revisions, :created_at, :updated_at,
                 :context_tasks, :metadata)
            """, row)

            conn.commit()
            return True
        except Exception as e:
            self._logger.error(f"Failed to save task: {e}")
            return False

    def get_task(self, task_id: UUID) -> Task | None:
        """Retrieve a task from the database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (str(task_id),),
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_task(row)
            return None
        except Exception as e:
            self._logger.error(f"Failed to get task: {e}")
            return None

    def update_workflow_result(
        self,
        workflow_id: UUID,
        result: WorkflowResult,
    ) -> bool:
        """Update workflow result in the database."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO workflow_results
                (workflow_id, success, tasks_completed, tasks_failed,
                 total_iterations, duration_seconds, outputs, errors)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(workflow_id),
                1 if result.success else 0,
                result.tasks_completed,
                result.tasks_failed,
                result.total_iterations,
                result.duration_seconds,
                json.dumps(result.outputs),
                json.dumps(result.errors),
            ))

            conn.commit()
            return True
        except Exception as e:
            self._logger.error(f"Failed to update workflow result: {e}")
            return False

    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None


def create_persistence_adapter(
    backend: str = "memory",
    **kwargs: Any,
) -> PersistencePort:
    """Factory function to create a persistence adapter.

    Args:
        backend: The backend to use ("memory" or "sqlite").
        **kwargs: Additional arguments for the adapter.

    Returns:
        A PersistencePort implementation.

    Raises:
        ValueError: If an unsupported backend is specified.
    """
    if backend == "sqlite":
        config = PersistenceConfig(**kwargs) if kwargs else None
        return SQLitePersistence(config)
    elif backend == "memory":
        return InMemoryPersistence()
    else:
        raise ValueError(
            f"Unsupported persistence backend: '{backend}'. "
            f"Supported backends: 'memory', 'sqlite'"
        )

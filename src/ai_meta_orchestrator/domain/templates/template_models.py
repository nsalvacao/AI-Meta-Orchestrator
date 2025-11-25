"""Workflow template domain models.

This module provides models for defining reusable workflow templates
that can be instantiated with specific parameters.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from ai_meta_orchestrator.domain.agents.agent_models import AgentRole
from ai_meta_orchestrator.domain.tasks.task_models import Task, TaskPriority
from ai_meta_orchestrator.domain.workflows.workflow_models import (
    Workflow,
    WorkflowConfig,
    WorkflowMode,
)


class TemplateCategory(str, Enum):
    """Categories for workflow templates."""

    DEVELOPMENT = "development"
    REVIEW = "review"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    CUSTOM = "custom"


@dataclass
class WorkflowTemplateConfig:
    """Configuration for a workflow template.

    Attributes:
        mode: Default execution mode.
        max_iterations: Default maximum iterations.
        enable_evaluation: Default evaluation setting.
        enable_correction_loop: Default correction loop setting.
        verbose: Default verbose setting.
        parameters: Template-specific parameters that can be customized.
    """

    mode: WorkflowMode = WorkflowMode.SEQUENTIAL
    max_iterations: int = 10
    enable_evaluation: bool = True
    enable_correction_loop: bool = True
    verbose: bool = True
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskTemplate:
    """Template for a task that can be instantiated.

    Attributes:
        id: Unique identifier for the task template.
        name_template: Template string for task name (supports {param} substitution).
        description_template: Template string for description.
        assigned_to: The agent role for this task.
        expected_output_template: Template string for expected output.
        priority: Default priority for instantiated tasks.
        depends_on: List of task template IDs that must complete first.
        metadata: Additional metadata for the template.
    """

    name_template: str
    description_template: str
    assigned_to: AgentRole
    expected_output_template: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    id: UUID = field(default_factory=uuid4)
    depends_on: list[UUID] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def instantiate(self, params: dict[str, str]) -> Task:
        """Instantiate a task from this template.

        Args:
            params: Dictionary of parameter values for substitution.

        Returns:
            A Task instance with substituted values.
        """
        return Task(
            name=self.name_template.format(**params),
            description=self.description_template.format(**params),
            assigned_to=self.assigned_to,
            expected_output=self.expected_output_template.format(**params),
            priority=self.priority,
            metadata={"template_id": str(self.id), **self.metadata},
        )


@dataclass
class WorkflowTemplate:
    """A reusable workflow template.

    Attributes:
        id: Unique identifier for the template.
        name: Human-readable name of the template.
        description: Description of what the template does.
        category: Template category.
        task_templates: List of task templates in order.
        config: Default configuration for the workflow.
        required_params: List of required parameter names.
        optional_params: Dictionary of optional parameters with defaults.
        tags: Tags for template discovery.
        version: Template version string.
        metadata: Additional metadata.
    """

    name: str
    description: str
    category: TemplateCategory = TemplateCategory.CUSTOM
    task_templates: list[TaskTemplate] = field(default_factory=list)
    config: WorkflowTemplateConfig = field(default_factory=WorkflowTemplateConfig)
    id: UUID = field(default_factory=uuid4)
    required_params: list[str] = field(default_factory=list)
    optional_params: dict[str, str] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_task_template(self, task_template: TaskTemplate) -> None:
        """Add a task template to this workflow template."""
        self.task_templates.append(task_template)

    def validate_params(self, params: dict[str, str]) -> list[str]:
        """Validate that all required parameters are provided.

        Args:
            params: Dictionary of parameter values.

        Returns:
            List of missing required parameter names.
        """
        missing = []
        for param in self.required_params:
            if param not in params:
                missing.append(param)
        return missing

    def instantiate(
        self,
        params: dict[str, str] | None = None,
        workflow_name: str | None = None,
    ) -> Workflow:
        """Instantiate a workflow from this template.

        Args:
            params: Dictionary of parameter values for substitution.
            workflow_name: Optional custom name for the workflow.

        Returns:
            A Workflow instance with all tasks instantiated.

        Raises:
            ValueError: If required parameters are missing.
        """
        # Merge optional params with provided params
        all_params = {**self.optional_params, **(params or {})}

        # Validate required params
        missing = self.validate_params(all_params)
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

        # Create workflow with configuration
        workflow = Workflow(
            name=workflow_name or self.name.format(**all_params),
            description=self.description.format(**all_params),
            config=WorkflowConfig(
                mode=self.config.mode,
                max_iterations=self.config.max_iterations,
                enable_evaluation=self.config.enable_evaluation,
                enable_correction_loop=self.config.enable_correction_loop,
                verbose=self.config.verbose,
            ),
            metadata={
                "template_id": str(self.id),
                "template_name": self.name,
                "template_version": self.version,
            },
        )

        # Create a mapping of template IDs to instantiated task IDs
        template_to_task: dict[UUID, UUID] = {}

        # Instantiate all tasks
        for task_template in self.task_templates:
            task = task_template.instantiate(all_params)
            template_to_task[task_template.id] = task.id

            # Map dependencies
            for dep_template_id in task_template.depends_on:
                if dep_template_id in template_to_task:
                    task.context_tasks.append(template_to_task[dep_template_id])

            workflow.add_task(task)

        return workflow


class WorkflowTemplateRegistry:
    """Registry for managing workflow templates.

    This class provides a central registry for discovering and retrieving
    workflow templates by name, category, or tags.
    """

    def __init__(self) -> None:
        """Initialize the template registry."""
        self._templates: dict[str, WorkflowTemplate] = {}
        self._by_category: dict[TemplateCategory, list[str]] = {
            cat: [] for cat in TemplateCategory
        }

    def register(self, template: WorkflowTemplate) -> None:
        """Register a workflow template.

        Args:
            template: The template to register.

        Raises:
            ValueError: If a template with the same name already exists.
        """
        if template.name in self._templates:
            raise ValueError(f"Template '{template.name}' already registered")

        self._templates[template.name] = template
        self._by_category[template.category].append(template.name)

    def get(self, name: str) -> WorkflowTemplate | None:
        """Get a template by name.

        Args:
            name: The template name.

        Returns:
            The template or None if not found.
        """
        return self._templates.get(name)

    def get_by_category(self, category: TemplateCategory) -> list[WorkflowTemplate]:
        """Get all templates in a category.

        Args:
            category: The category to filter by.

        Returns:
            List of templates in the category.
        """
        return [self._templates[name] for name in self._by_category.get(category, [])]

    def search_by_tags(self, tags: list[str]) -> list[WorkflowTemplate]:
        """Search templates by tags.

        Args:
            tags: List of tags to search for.

        Returns:
            List of templates matching any of the tags.
        """
        matching = []
        for template in self._templates.values():
            if any(tag in template.tags for tag in tags):
                matching.append(template)
        return matching

    def list_all(self) -> list[WorkflowTemplate]:
        """Get all registered templates.

        Returns:
            List of all templates.
        """
        return list(self._templates.values())

    def unregister(self, name: str) -> bool:
        """Unregister a template by name.

        Args:
            name: The template name.

        Returns:
            True if removed, False if not found.
        """
        if name in self._templates:
            template = self._templates.pop(name)
            self._by_category[template.category].remove(name)
            return True
        return False

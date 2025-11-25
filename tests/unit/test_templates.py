"""Unit tests for workflow templates."""

import pytest

from ai_meta_orchestrator.adapters.templates import (
    create_full_development_template,
    get_default_template_registry,
)
from ai_meta_orchestrator.domain.agents.agent_models import AgentRole
from ai_meta_orchestrator.domain.templates.template_models import (
    TaskTemplate,
    TemplateCategory,
    WorkflowTemplate,
    WorkflowTemplateRegistry,
)


class TestTaskTemplate:
    """Tests for TaskTemplate."""

    def test_create_task_template(self) -> None:
        """Test creating a task template."""
        template = TaskTemplate(
            name_template="Task: {project_name}",
            description_template="Implement {project_name}",
            assigned_to=AgentRole.DEV,
            expected_output_template="Completed {project_name}",
        )
        assert template.name_template == "Task: {project_name}"
        assert template.assigned_to == AgentRole.DEV

    def test_instantiate_task_template(self) -> None:
        """Test instantiating a task from template."""
        template = TaskTemplate(
            name_template="Task: {project_name}",
            description_template="Implement {project_name}",
            assigned_to=AgentRole.DEV,
            expected_output_template="Completed {project_name}",
        )

        task = template.instantiate({"project_name": "MyProject"})

        assert task.name == "Task: MyProject"
        assert task.description == "Implement MyProject"
        assert task.expected_output == "Completed MyProject"
        assert task.assigned_to == AgentRole.DEV


class TestWorkflowTemplate:
    """Tests for WorkflowTemplate."""

    def test_create_workflow_template(self) -> None:
        """Test creating a workflow template."""
        template = WorkflowTemplate(
            name="Test Template",
            description="A test template for {project}",
            category=TemplateCategory.DEVELOPMENT,
            required_params=["project"],
        )

        assert template.name == "Test Template"
        assert template.category == TemplateCategory.DEVELOPMENT
        assert "project" in template.required_params

    def test_validate_params(self) -> None:
        """Test parameter validation."""
        template = WorkflowTemplate(
            name="Test",
            description="Test",
            required_params=["a", "b", "c"],
        )

        missing = template.validate_params({"a": "1", "b": "2"})
        assert missing == ["c"]

        missing = template.validate_params({"a": "1", "b": "2", "c": "3"})
        assert missing == []

    def test_instantiate_workflow(self) -> None:
        """Test instantiating a workflow from template."""
        template = WorkflowTemplate(
            name="Template: {project}",
            description="Build {project}",
            required_params=["project"],
            optional_params={"version": "1.0"},
        )

        task_template = TaskTemplate(
            name_template="Build {project} v{version}",
            description_template="Build project {project}",
            assigned_to=AgentRole.DEV,
        )
        template.add_task_template(task_template)

        workflow = template.instantiate({"project": "MyApp"})

        assert workflow.name == "Template: MyApp"
        assert workflow.description == "Build MyApp"
        assert len(workflow.tasks) == 1
        assert workflow.tasks[0].name == "Build MyApp v1.0"

    def test_instantiate_missing_params_raises(self) -> None:
        """Test that missing params raises ValueError."""
        template = WorkflowTemplate(
            name="Test",
            description="Test",
            required_params=["required_param"],
        )

        with pytest.raises(ValueError) as excinfo:
            template.instantiate({})
        assert "required_param" in str(excinfo.value)


class TestWorkflowTemplateRegistry:
    """Tests for WorkflowTemplateRegistry."""

    def test_register_template(self) -> None:
        """Test registering a template."""
        registry = WorkflowTemplateRegistry()
        template = WorkflowTemplate(
            name="My Template",
            description="Test",
            category=TemplateCategory.DEVELOPMENT,
        )

        registry.register(template)

        assert registry.get("My Template") == template

    def test_register_duplicate_raises(self) -> None:
        """Test that registering duplicate name raises."""
        registry = WorkflowTemplateRegistry()
        template = WorkflowTemplate(name="Test", description="Test")

        registry.register(template)

        with pytest.raises(ValueError):
            registry.register(template)

    def test_get_by_category(self) -> None:
        """Test getting templates by category."""
        registry = WorkflowTemplateRegistry()
        dev_template = WorkflowTemplate(
            name="Dev",
            description="Dev",
            category=TemplateCategory.DEVELOPMENT,
        )
        doc_template = WorkflowTemplate(
            name="Doc",
            description="Doc",
            category=TemplateCategory.DOCUMENTATION,
        )

        registry.register(dev_template)
        registry.register(doc_template)

        dev_templates = registry.get_by_category(TemplateCategory.DEVELOPMENT)
        assert len(dev_templates) == 1
        assert dev_templates[0].name == "Dev"

    def test_search_by_tags(self) -> None:
        """Test searching templates by tags."""
        registry = WorkflowTemplateRegistry()
        template1 = WorkflowTemplate(
            name="Template 1",
            description="First",
            tags=["python", "api"],
        )
        template2 = WorkflowTemplate(
            name="Template 2",
            description="Second",
            tags=["javascript", "frontend"],
        )

        registry.register(template1)
        registry.register(template2)

        results = registry.search_by_tags(["python"])
        assert len(results) == 1
        assert results[0].name == "Template 1"

    def test_unregister(self) -> None:
        """Test unregistering a template."""
        registry = WorkflowTemplateRegistry()
        template = WorkflowTemplate(name="Test", description="Test")
        registry.register(template)

        result = registry.unregister("Test")

        assert result is True
        assert registry.get("Test") is None


class TestBuiltinTemplates:
    """Tests for built-in templates."""

    def test_full_development_template(self) -> None:
        """Test the full development template."""
        template = create_full_development_template()

        assert template.name == "Full Development Workflow"
        assert template.category == TemplateCategory.DEVELOPMENT
        assert len(template.task_templates) == 5
        assert "project_name" in template.required_params
        assert "project_description" in template.required_params

    def test_default_registry_has_templates(self) -> None:
        """Test that default registry has built-in templates."""
        registry = get_default_template_registry()
        templates = registry.list_all()

        assert len(templates) >= 5
        assert any(t.name == "Full Development Workflow" for t in templates)
        assert any(t.name == "Quick Implementation" for t in templates)
        assert any(t.name == "Code Review Workflow" for t in templates)

    def test_full_development_instantiation(self) -> None:
        """Test instantiating the full development template."""
        template = create_full_development_template()
        workflow = template.instantiate({
            "project_name": "TestProject",
            "project_description": "A test project description",
        })

        assert len(workflow.tasks) == 5
        # Check tasks are assigned to correct agents
        agents = [t.assigned_to for t in workflow.tasks]
        assert AgentRole.PM in agents
        assert AgentRole.DEV in agents
        assert AgentRole.QA in agents
        assert AgentRole.SECURITY in agents
        assert AgentRole.DOCS in agents

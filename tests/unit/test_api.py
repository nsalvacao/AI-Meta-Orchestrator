"""Unit tests for the REST API."""

import pytest
from fastapi.testclient import TestClient

from ai_meta_orchestrator import __version__
from ai_meta_orchestrator.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == __version__
        assert "uptime_seconds" in data


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_returns_info(self, client: TestClient) -> None:
        """Test root endpoint returns API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AI Meta Orchestrator API"
        assert data["version"] == __version__
        assert data["docs"] == "/docs"


class TestAgentsEndpoints:
    """Tests for agents endpoints."""

    def test_list_agents(self, client: TestClient) -> None:
        """Test listing all agents."""
        response = client.get("/agents")

        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert data["total"] == 5  # PM, DEV, QA, SECURITY, DOCS

    def test_get_agent(self, client: TestClient) -> None:
        """Test getting a specific agent."""
        response = client.get("/agents/developer")

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "developer"
        assert "goal" in data
        assert "backstory" in data

    def test_get_agent_not_found(self, client: TestClient) -> None:
        """Test getting non-existent agent."""
        response = client.get("/agents/nonexistent")

        assert response.status_code == 422  # Invalid enum value


class TestWorkflowsEndpoints:
    """Tests for workflows endpoints."""

    def test_list_workflows_empty(self, client: TestClient) -> None:
        """Test listing workflows when empty."""
        response = client.get("/workflows")

        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert isinstance(data["workflows"], list)

    def test_create_workflow(self, client: TestClient) -> None:
        """Test creating a workflow."""
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow",
            "tasks": [
                {
                    "name": "Test Task",
                    "description": "A test task",
                    "assigned_to": "developer",
                }
            ],
        }

        response = client.post("/workflows", json=workflow_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Workflow"
        assert data["task_count"] == 1
        assert data["status"] == "not_started"

    def test_get_workflow(self, client: TestClient) -> None:
        """Test getting a workflow."""
        # First create a workflow
        workflow_data = {
            "name": "Get Test",
            "description": "Test",
        }
        create_response = client.post("/workflows", json=workflow_data)
        workflow_id = create_response.json()["id"]

        # Then get it
        response = client.get(f"/workflows/{workflow_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Get Test"

    def test_get_workflow_tasks(self, client: TestClient) -> None:
        """Test getting workflow tasks."""
        # Create workflow with task
        workflow_data = {
            "name": "Task Test",
            "description": "Test",
            "tasks": [
                {
                    "name": "Task 1",
                    "description": "First task",
                    "assigned_to": "developer",
                }
            ],
        }
        create_response = client.post("/workflows", json=workflow_data)
        workflow_id = create_response.json()["id"]

        response = client.get(f"/workflows/{workflow_id}/tasks")

        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["name"] == "Task 1"


class TestTemplatesEndpoints:
    """Tests for templates endpoints."""

    def test_list_templates(self, client: TestClient) -> None:
        """Test listing all templates."""
        response = client.get("/templates")

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert data["total"] >= 5  # At least the built-in templates

    def test_get_template(self, client: TestClient) -> None:
        """Test getting a specific template."""
        response = client.get("/templates/Full Development Workflow")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Full Development Workflow"
        assert "required_params" in data
        assert "project_name" in data["required_params"]

    def test_get_template_not_found(self, client: TestClient) -> None:
        """Test getting non-existent template."""
        response = client.get("/templates/NonExistent Template")

        assert response.status_code == 404

    def test_instantiate_template(self, client: TestClient) -> None:
        """Test instantiating a template."""
        request_data = {
            "template_name": "Full Development Workflow",
            "params": {
                "project_name": "Test Project",
                "project_description": "A test project",
            },
        }

        response = client.post("/templates/instantiate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["task_count"] == 5
        assert data["status"] == "not_started"

    def test_instantiate_template_missing_params(self, client: TestClient) -> None:
        """Test instantiating template with missing params."""
        request_data = {
            "template_name": "Full Development Workflow",
            "params": {
                "project_name": "Test",
                # Missing project_description
            },
        }

        response = client.post("/templates/instantiate", json=request_data)

        assert response.status_code == 400


class TestPluginsEndpoints:
    """Tests for plugins endpoints."""

    def test_list_plugins(self, client: TestClient) -> None:
        """Test listing plugins."""
        response = client.get("/plugins")

        assert response.status_code == 200
        data = response.json()
        assert "plugins" in data
        assert "total" in data
        assert "active_count" in data

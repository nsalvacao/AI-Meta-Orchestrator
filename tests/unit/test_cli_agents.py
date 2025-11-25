"""Unit tests for external CLI agents."""

from unittest.mock import patch

import pytest

from ai_meta_orchestrator.adapters.external_cli.cli_adapters import (
    BaseCLIAdapter,
    CLIConfig,
)
from ai_meta_orchestrator.adapters.external_cli.cli_agents import (
    CodexAgent,
    CopilotAgent,
    ExternalCLIAgent,
    GeminiAgent,
    create_cli_agent,
)
from ai_meta_orchestrator.domain.agents.agent_models import AgentConfig, AgentRole
from ai_meta_orchestrator.domain.tasks.task_models import Task
from ai_meta_orchestrator.ports.external_ports.external_port import ExternalCLIType


class TestExternalCLIAgent:
    """Tests for ExternalCLIAgent base class."""

    def test_creates_default_config(self) -> None:
        """Test agent creates default config if none provided."""
        config = CLIConfig(executable="test")
        adapter = BaseCLIAdapter(ExternalCLIType.CUSTOM, config)
        agent = ExternalCLIAgent(adapter, AgentRole.DEV)

        assert agent.role == AgentRole.DEV
        assert agent.config.role == AgentRole.DEV
        assert "custom" in agent.config.goal.lower()

    def test_uses_provided_config(self) -> None:
        """Test agent uses provided config."""
        config = CLIConfig(executable="test")
        adapter = BaseCLIAdapter(ExternalCLIType.CUSTOM, config)

        custom_config = AgentConfig(
            role=AgentRole.QA,
            goal="Custom goal",
            backstory="Custom backstory",
        )
        agent = ExternalCLIAgent(adapter, AgentRole.QA, config=custom_config)

        assert agent.config.goal == "Custom goal"
        assert agent.config.backstory == "Custom backstory"

    def test_is_available_checks_adapter(self) -> None:
        """Test is_available delegates to adapter."""
        config = CLIConfig(executable="test")
        adapter = BaseCLIAdapter(ExternalCLIType.CUSTOM, config)

        with (
            patch.object(adapter, "is_available", return_value=True),
            patch.object(adapter, "is_authenticated", return_value=True),
        ):
            agent = ExternalCLIAgent(adapter, AgentRole.DEV)
            assert agent.is_available() is True

        with (
            patch.object(adapter, "is_available", return_value=False),
            patch.object(adapter, "is_authenticated", return_value=True),
        ):
            agent = ExternalCLIAgent(adapter, AgentRole.DEV)
            assert agent.is_available() is False

    def test_format_task_as_prompt(self) -> None:
        """Test task is formatted correctly as prompt."""
        config = CLIConfig(executable="test")
        adapter = BaseCLIAdapter(ExternalCLIType.CUSTOM, config)
        agent = ExternalCLIAgent(adapter, AgentRole.DEV)

        task = Task(
            name="Test Task",
            description="Do something",
            expected_output="Result",
            assigned_to=AgentRole.DEV,
        )

        prompt = agent._format_task_as_prompt(task)
        assert "Test Task" in prompt
        assert "Do something" in prompt
        assert "Result" in prompt

    def test_can_handle_checks_role(self) -> None:
        """Test can_handle checks role assignment."""
        config = CLIConfig(executable="test")
        adapter = BaseCLIAdapter(ExternalCLIType.CUSTOM, config)

        with (
            patch.object(adapter, "is_available", return_value=True),
            patch.object(adapter, "is_authenticated", return_value=True),
        ):
            agent = ExternalCLIAgent(adapter, AgentRole.DEV)

            dev_task = Task(
                name="Dev Task",
                description="Code something",
                assigned_to=AgentRole.DEV,
            )
            qa_task = Task(
                name="QA Task",
                description="Test something",
                assigned_to=AgentRole.QA,
            )

            assert agent.can_handle(dev_task) is True
            assert agent.can_handle(qa_task) is False

    def test_execute_task_when_unavailable(self) -> None:
        """Test execute_task returns error when CLI unavailable."""
        config = CLIConfig(executable="test")
        adapter = BaseCLIAdapter(ExternalCLIType.CUSTOM, config)

        with patch.object(adapter, "is_available", return_value=False):
            agent = ExternalCLIAgent(adapter, AgentRole.DEV)

            task = Task(
                name="Test Task",
                description="Do something",
                assigned_to=AgentRole.DEV,
            )

            result = agent.execute_task(task)
            assert result.success is False
            assert "not available" in result.error

    def test_execute_task_when_not_authenticated(self) -> None:
        """Test execute_task returns error when not authenticated."""
        config = CLIConfig(executable="test")
        adapter = BaseCLIAdapter(ExternalCLIType.CUSTOM, config)

        with (
            patch.object(adapter, "is_available", return_value=True),
            patch.object(adapter, "is_authenticated", return_value=False),
        ):
            agent = ExternalCLIAgent(adapter, AgentRole.DEV)

            task = Task(
                name="Test Task",
                description="Do something",
                assigned_to=AgentRole.DEV,
            )

            result = agent.execute_task(task)
            assert result.success is False
            assert "authentication required" in result.error.lower()


class TestGeminiAgent:
    """Tests for GeminiAgent."""

    def test_initialization(self) -> None:
        """Test GeminiAgent initializes correctly."""
        agent = GeminiAgent()
        assert agent.role == AgentRole.DEV
        assert agent.cli_type == ExternalCLIType.GEMINI

    def test_custom_role(self) -> None:
        """Test GeminiAgent with custom role."""
        agent = GeminiAgent(role=AgentRole.QA)
        assert agent.role == AgentRole.QA

    def test_default_config_mentions_gemini(self) -> None:
        """Test default config mentions Gemini."""
        agent = GeminiAgent()
        assert "gemini" in agent.config.backstory.lower()


class TestCodexAgent:
    """Tests for CodexAgent."""

    def test_initialization(self) -> None:
        """Test CodexAgent initializes correctly."""
        agent = CodexAgent()
        assert agent.role == AgentRole.DEV
        assert agent.cli_type == ExternalCLIType.CODEX

    def test_custom_role(self) -> None:
        """Test CodexAgent with custom role."""
        agent = CodexAgent(role=AgentRole.DOCS)
        assert agent.role == AgentRole.DOCS

    def test_default_config_mentions_openai(self) -> None:
        """Test default config mentions OpenAI."""
        agent = CodexAgent()
        assert "openai" in agent.config.backstory.lower()


class TestCopilotAgent:
    """Tests for CopilotAgent."""

    def test_initialization(self) -> None:
        """Test CopilotAgent initializes correctly."""
        agent = CopilotAgent()
        assert agent.role == AgentRole.DEV
        assert agent.cli_type == ExternalCLIType.COPILOT

    def test_custom_role(self) -> None:
        """Test CopilotAgent with custom role."""
        agent = CopilotAgent(role=AgentRole.PM)
        assert agent.role == AgentRole.PM

    def test_default_config_mentions_copilot(self) -> None:
        """Test default config mentions Copilot."""
        agent = CopilotAgent()
        assert "copilot" in agent.config.backstory.lower()


class TestCreateCliAgent:
    """Tests for create_cli_agent factory function."""

    def test_create_gemini_agent(self) -> None:
        """Test creating Gemini agent."""
        agent = create_cli_agent(ExternalCLIType.GEMINI)
        assert isinstance(agent, GeminiAgent)

    def test_create_codex_agent(self) -> None:
        """Test creating Codex agent."""
        agent = create_cli_agent(ExternalCLIType.CODEX)
        assert isinstance(agent, CodexAgent)

    def test_create_copilot_agent(self) -> None:
        """Test creating Copilot agent."""
        agent = create_cli_agent(ExternalCLIType.COPILOT)
        assert isinstance(agent, CopilotAgent)

    def test_create_with_custom_role(self) -> None:
        """Test creating agent with custom role."""
        agent = create_cli_agent(ExternalCLIType.GEMINI, role=AgentRole.SECURITY)
        assert agent.role == AgentRole.SECURITY

    def test_create_unsupported_raises(self) -> None:
        """Test creating agent with unsupported type raises."""
        with pytest.raises(ValueError) as exc_info:
            create_cli_agent(ExternalCLIType.CUSTOM)
        assert "unsupported" in str(exc_info.value).lower()

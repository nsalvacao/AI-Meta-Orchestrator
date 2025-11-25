"""External CLI agent wrappers.

This module provides agent wrappers for external CLI tools,
allowing them to be used as agents in the orchestrator system.

Each CLI agent implements the AgentPort interface and delegates
task execution to the underlying CLI adapter.
"""

from ai_meta_orchestrator.adapters.external_cli.cli_adapters import (
    BaseCLIAdapter,
    CodexCLIAdapter,
    CopilotCLIAdapter,
    GeminiCLIAdapter,
)
from ai_meta_orchestrator.domain.agents.agent_models import AgentConfig, AgentRole
from ai_meta_orchestrator.domain.tasks.task_models import Task, TaskResult
from ai_meta_orchestrator.ports.agent_ports.agent_port import AgentPort
from ai_meta_orchestrator.ports.external_ports.external_port import ExternalCLIType


class ExternalCLIAgent(AgentPort):
    """Base agent wrapper for external CLI tools.

    This adapter wraps an external CLI adapter to implement the AgentPort
    interface, allowing CLI tools to be used as agents in workflows.
    """

    def __init__(
        self,
        cli_adapter: BaseCLIAdapter,
        role: AgentRole,
        config: AgentConfig | None = None,
    ) -> None:
        """Initialize the CLI agent.

        Args:
            cli_adapter: The CLI adapter to wrap.
            role: The agent role to assume.
            config: Optional agent configuration override.
        """
        self._cli_adapter = cli_adapter
        self._role = role
        self._config = config or self._create_default_config()

    def _create_default_config(self) -> AgentConfig:
        """Create a default configuration based on CLI type.

        Returns:
            Default agent configuration.
        """
        cli_type = self._cli_adapter.cli_type
        return AgentConfig(
            role=self._role,
            goal=f"Execute tasks using {cli_type.value} CLI capabilities",
            backstory=(
                f"You are an AI agent powered by {cli_type.value} CLI. "
                "You execute tasks by leveraging the CLI's AI capabilities."
            ),
            verbose=True,
            allow_delegation=False,
        )

    @property
    def role(self) -> AgentRole:
        """Get the role of this agent."""
        return self._role

    @property
    def config(self) -> AgentConfig:
        """Get the configuration of this agent."""
        return self._config

    @property
    def cli_type(self) -> ExternalCLIType:
        """Get the CLI type of the underlying adapter."""
        return self._cli_adapter.cli_type

    def is_available(self) -> bool:
        """Check if the underlying CLI is available.

        Returns:
            True if the CLI is available and authenticated.
        """
        return (
            self._cli_adapter.is_available()
            and self._cli_adapter.is_authenticated()
        )

    def _format_task_as_prompt(self, task: Task) -> str:
        """Format a task as a prompt for the CLI.

        Args:
            task: The task to format.

        Returns:
            Formatted prompt string.
        """
        parts = [
            f"Task: {task.name}",
            f"Description: {task.description}",
        ]

        if task.expected_output:
            parts.append(f"Expected Output: {task.expected_output}")

        if task.metadata:
            context = task.metadata.get("context")
            if context:
                parts.append(f"Context: {context}")

        return "\n\n".join(parts)

    def execute_task(self, task: Task) -> TaskResult:
        """Execute a task using the CLI.

        Args:
            task: The task to execute.

        Returns:
            TaskResult containing the output or error.
        """
        if not self._cli_adapter.is_available():
            return TaskResult(
                success=False,
                error=f"{self._cli_adapter.cli_type.value} CLI is not available",
                metadata={"task_id": str(task.id), "cli_type": self._cli_adapter.cli_type.value},
            )

        if not self._cli_adapter.is_authenticated():
            return TaskResult(
                success=False,
                error=f"Authentication required for {self._cli_adapter.cli_type.value} CLI",
                metadata={"task_id": str(task.id), "cli_type": self._cli_adapter.cli_type.value},
            )

        prompt = self._format_task_as_prompt(task)
        result = self._cli_adapter.execute(prompt)

        return TaskResult(
            success=result.success,
            output=result.output if result.success else "",
            error=result.error if not result.success else "",
            metadata={
                "task_id": str(task.id),
                "cli_type": self._cli_adapter.cli_type.value,
                "exit_code": result.exit_code,
            },
        )

    def can_handle(self, task: Task) -> bool:
        """Check if this agent can handle the given task.

        Args:
            task: The task to check.

        Returns:
            True if the task is assigned to this agent's role and CLI is available.
        """
        return task.assigned_to == self._role and self.is_available()


class GeminiAgent(ExternalCLIAgent):
    """Agent wrapper for Gemini CLI.

    This agent uses Google's Gemini CLI for task execution,
    particularly suited for:
    - Code generation and review
    - Documentation writing
    - Analysis tasks
    """

    def __init__(
        self,
        role: AgentRole = AgentRole.DEV,
        config: AgentConfig | None = None,
        **cli_kwargs,
    ) -> None:
        """Initialize the Gemini agent.

        Args:
            role: The agent role to assume (default: DEV).
            config: Optional agent configuration override.
            **cli_kwargs: Additional arguments for GeminiCLIAdapter.
        """
        adapter = GeminiCLIAdapter(**cli_kwargs)
        super().__init__(adapter, role, config)

    def _create_default_config(self) -> AgentConfig:
        """Create Gemini-specific default configuration."""
        return AgentConfig(
            role=self._role,
            goal="Execute development tasks using Google Gemini AI",
            backstory=(
                "You are a highly capable AI agent powered by Google's Gemini. "
                "You excel at code generation, analysis, documentation, and "
                "problem-solving across multiple domains and programming languages."
            ),
            verbose=True,
            allow_delegation=False,
        )

    def execute_task(self, task: Task) -> TaskResult:
        """Execute a task using Gemini CLI.

        Uses the generate method for better prompt handling.

        Args:
            task: The task to execute.

        Returns:
            TaskResult containing the output or error.
        """
        if not self.is_available():
            return TaskResult(
                success=False,
                error="Gemini CLI is not available or not authenticated",
                metadata={"task_id": str(task.id), "cli_type": "gemini"},
            )

        prompt = self._format_task_as_prompt(task)
        adapter = self._cli_adapter
        if isinstance(adapter, GeminiCLIAdapter):
            result = adapter.generate(prompt)
        else:
            result = adapter.execute(prompt)

        return TaskResult(
            success=result.success,
            output=result.output if result.success else "",
            error=result.error if not result.success else "",
            metadata={
                "task_id": str(task.id),
                "cli_type": "gemini",
                "exit_code": result.exit_code,
            },
        )


class CodexAgent(ExternalCLIAgent):
    """Agent wrapper for OpenAI Codex CLI.

    This agent uses OpenAI's Codex/GPT models for task execution,
    particularly suited for:
    - Code completion
    - Natural language to code translation
    - Code explanation and documentation
    """

    def __init__(
        self,
        role: AgentRole = AgentRole.DEV,
        config: AgentConfig | None = None,
        **cli_kwargs,
    ) -> None:
        """Initialize the Codex agent.

        Args:
            role: The agent role to assume (default: DEV).
            config: Optional agent configuration override.
            **cli_kwargs: Additional arguments for CodexCLIAdapter.
        """
        adapter = CodexCLIAdapter(**cli_kwargs)
        super().__init__(adapter, role, config)

    def _create_default_config(self) -> AgentConfig:
        """Create Codex-specific default configuration."""
        return AgentConfig(
            role=self._role,
            goal="Execute development tasks using OpenAI's code models",
            backstory=(
                "You are an AI agent powered by OpenAI's advanced code models. "
                "You specialize in code generation, completion, and translation "
                "from natural language to code."
            ),
            verbose=True,
            allow_delegation=False,
        )

    def execute_task(self, task: Task) -> TaskResult:
        """Execute a task using Codex CLI.

        Uses the chat method for conversational interaction.

        Args:
            task: The task to execute.

        Returns:
            TaskResult containing the output or error.
        """
        if not self.is_available():
            return TaskResult(
                success=False,
                error="Codex/OpenAI CLI is not available or not authenticated",
                metadata={"task_id": str(task.id), "cli_type": "codex"},
            )

        prompt = self._format_task_as_prompt(task)
        adapter = self._cli_adapter
        if isinstance(adapter, CodexCLIAdapter):
            result = adapter.chat(prompt)
        else:
            result = adapter.execute(prompt)

        return TaskResult(
            success=result.success,
            output=result.output if result.success else "",
            error=result.error if not result.success else "",
            metadata={
                "task_id": str(task.id),
                "cli_type": "codex",
                "exit_code": result.exit_code,
            },
        )


class CopilotAgent(ExternalCLIAgent):
    """Agent wrapper for GitHub Copilot CLI.

    This agent uses GitHub Copilot CLI for task execution,
    particularly suited for:
    - Command suggestions
    - Git workflow assistance
    - Shell command generation
    """

    def __init__(
        self,
        role: AgentRole = AgentRole.DEV,
        config: AgentConfig | None = None,
        **cli_kwargs,
    ) -> None:
        """Initialize the Copilot agent.

        Args:
            role: The agent role to assume (default: DEV).
            config: Optional agent configuration override.
            **cli_kwargs: Additional arguments for CopilotCLIAdapter.
        """
        adapter = CopilotCLIAdapter(**cli_kwargs)
        super().__init__(adapter, role, config)

    def _create_default_config(self) -> AgentConfig:
        """Create Copilot-specific default configuration."""
        return AgentConfig(
            role=self._role,
            goal="Execute tasks using GitHub Copilot CLI",
            backstory=(
                "You are an AI agent powered by GitHub Copilot. "
                "You excel at generating shell commands, explaining code, "
                "and assisting with Git workflows."
            ),
            verbose=True,
            allow_delegation=False,
        )

    def execute_task(self, task: Task) -> TaskResult:
        """Execute a task using Copilot CLI.

        Uses the suggest method to get command suggestions.

        Args:
            task: The task to execute.

        Returns:
            TaskResult containing the output or error.
        """
        if not self.is_available():
            return TaskResult(
                success=False,
                error="GitHub Copilot CLI is not available or not authenticated",
                metadata={"task_id": str(task.id), "cli_type": "copilot"},
            )

        prompt = self._format_task_as_prompt(task)
        adapter = self._cli_adapter
        if isinstance(adapter, CopilotCLIAdapter):
            result = adapter.suggest(prompt)
        else:
            result = adapter.execute(prompt)

        return TaskResult(
            success=result.success,
            output=result.output if result.success else "",
            error=result.error if not result.success else "",
            metadata={
                "task_id": str(task.id),
                "cli_type": "copilot",
                "exit_code": result.exit_code,
            },
        )


def create_cli_agent(
    cli_type: ExternalCLIType,
    role: AgentRole = AgentRole.DEV,
    config: AgentConfig | None = None,
    **cli_kwargs,
) -> ExternalCLIAgent:
    """Factory function to create a CLI agent.

    Args:
        cli_type: The type of CLI to use.
        role: The agent role to assume.
        config: Optional agent configuration.
        **cli_kwargs: Additional arguments for the CLI adapter.

    Returns:
        An ExternalCLIAgent implementation.

    Raises:
        ValueError: If cli_type is not supported.
    """
    if cli_type == ExternalCLIType.GEMINI:
        return GeminiAgent(role=role, config=config, **cli_kwargs)
    elif cli_type == ExternalCLIType.CODEX:
        return CodexAgent(role=role, config=config, **cli_kwargs)
    elif cli_type == ExternalCLIType.COPILOT:
        return CopilotAgent(role=role, config=config, **cli_kwargs)
    else:
        raise ValueError(f"Unsupported CLI type for agent: {cli_type}")

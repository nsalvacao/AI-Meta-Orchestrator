"""Agent port interface - Abstraction for agent operations."""

from abc import ABC, abstractmethod

from ai_meta_orchestrator.domain.agents.agent_models import AgentConfig, AgentRole
from ai_meta_orchestrator.domain.tasks.task_models import Task, TaskResult


class AgentPort(ABC):
    """Abstract interface for agent operations.

    This port defines the contract that any agent implementation must fulfill,
    whether it's an internal CrewAI agent or an external CLI-based agent.
    """

    @property
    @abstractmethod
    def role(self) -> AgentRole:
        """Get the role of this agent."""
        pass

    @property
    @abstractmethod
    def config(self) -> AgentConfig:
        """Get the configuration of this agent."""
        pass

    @abstractmethod
    def execute_task(self, task: Task) -> TaskResult:
        """Execute a task and return the result.

        Args:
            task: The task to execute.

        Returns:
            TaskResult containing the output or error.
        """
        pass

    @abstractmethod
    def can_handle(self, task: Task) -> bool:
        """Check if this agent can handle the given task.

        Args:
            task: The task to check.

        Returns:
            True if this agent can handle the task, False otherwise.
        """
        pass


class AgentFactoryPort(ABC):
    """Abstract factory interface for creating agents."""

    @abstractmethod
    def create_agent(self, role: AgentRole, config: AgentConfig | None = None) -> AgentPort:
        """Create an agent with the specified role.

        Args:
            role: The role of the agent to create.
            config: Optional custom configuration for the agent.

        Returns:
            An agent instance implementing AgentPort.
        """
        pass

    @abstractmethod
    def get_available_roles(self) -> list[AgentRole]:
        """Get all available agent roles.

        Returns:
            List of available agent roles.
        """
        pass

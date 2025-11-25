"""CrewAI-based agent implementation."""

from crewai import Agent
from crewai import Task as CrewAITask

from ai_meta_orchestrator.domain.agents.agent_models import (
    DEFAULT_AGENT_CONFIGS,
    AgentConfig,
    AgentRole,
)
from ai_meta_orchestrator.domain.tasks.task_models import Task, TaskResult
from ai_meta_orchestrator.ports.agent_ports.agent_port import AgentFactoryPort, AgentPort


class CrewAIAgent(AgentPort):
    """CrewAI-based agent implementation.

    This adapter wraps CrewAI's Agent class to implement the AgentPort interface.
    """

    def __init__(self, agent_config: AgentConfig) -> None:
        """Initialize the CrewAI agent.

        Args:
            agent_config: Configuration for the agent.
        """
        self._config = agent_config
        self._agent = self._create_crewai_agent()

    def _create_crewai_agent(self) -> Agent:
        """Create the underlying CrewAI agent."""
        return Agent(
            role=self._config.role.value,
            goal=self._config.goal,
            backstory=self._config.backstory,
            verbose=self._config.verbose,
            allow_delegation=self._config.allow_delegation,
            tools=self._config.tools,
            memory=self._config.memory,
        )

    @property
    def role(self) -> AgentRole:
        """Get the role of this agent."""
        return self._config.role

    @property
    def config(self) -> AgentConfig:
        """Get the configuration of this agent."""
        return self._config

    @property
    def crewai_agent(self) -> Agent:
        """Get the underlying CrewAI agent for use in Crews."""
        return self._agent

    def execute_task(self, task: Task) -> TaskResult:
        """Execute a task and return the result.

        Args:
            task: The task to execute.

        Returns:
            TaskResult containing the output or error.
        """
        try:
            # Create a CrewAI task from our domain task
            crewai_task = CrewAITask(
                description=task.description,
                expected_output=task.expected_output or "Complete the task successfully",
                agent=self._agent,
            )

            # Execute the task
            result = crewai_task.execute_sync()

            return TaskResult(
                success=True,
                output=result,
                metadata={"task_id": str(task.id), "agent_role": self._config.role.value},
            )
        except Exception as e:
            return TaskResult(
                success=False,
                error=str(e),
                metadata={"task_id": str(task.id), "agent_role": self._config.role.value},
            )

    def can_handle(self, task: Task) -> bool:
        """Check if this agent can handle the given task.

        Args:
            task: The task to check.

        Returns:
            True if this agent can handle the task.
        """
        return task.assigned_to == self._config.role


class CrewAIAgentFactory(AgentFactoryPort):
    """Factory for creating CrewAI-based agents."""

    def __init__(self) -> None:
        """Initialize the factory with default configurations."""
        self._agents: dict[AgentRole, CrewAIAgent] = {}

    def create_agent(
        self, role: AgentRole, config: AgentConfig | None = None
    ) -> CrewAIAgent:
        """Create an agent with the specified role.

        Args:
            role: The role of the agent to create.
            config: Optional custom configuration for the agent.

        Returns:
            A CrewAIAgent instance.
        """
        if role in self._agents:
            return self._agents[role]

        agent_config = config or DEFAULT_AGENT_CONFIGS.get(role)
        if agent_config is None:
            raise ValueError(f"No configuration found for role: {role}")

        agent = CrewAIAgent(agent_config)
        self._agents[role] = agent
        return agent

    def get_available_roles(self) -> list[AgentRole]:
        """Get all available agent roles.

        Returns:
            List of available agent roles.
        """
        return list(AgentRole)

    def get_all_agents(self) -> dict[AgentRole, CrewAIAgent]:
        """Get all created agents.

        Returns:
            Dictionary mapping roles to agents.
        """
        return self._agents.copy()

    def create_all_agents(self) -> dict[AgentRole, CrewAIAgent]:
        """Create agents for all available roles.

        Returns:
            Dictionary mapping roles to created agents.
        """
        for role in AgentRole:
            self.create_agent(role)
        return self.get_all_agents()

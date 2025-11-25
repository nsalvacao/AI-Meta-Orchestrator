"""Unit tests for domain agent models."""

from ai_meta_orchestrator.domain.agents.agent_models import (
    DEFAULT_AGENT_CONFIGS,
    AgentConfig,
    AgentRole,
)


class TestAgentRole:
    """Tests for AgentRole enumeration."""

    def test_all_roles_defined(self) -> None:
        """Verify all expected agent roles are defined."""
        expected_roles = {
            "project_manager", "developer", "quality_assurance", "security", "documentation"
        }
        actual_roles = {role.value for role in AgentRole}
        assert actual_roles == expected_roles

    def test_role_values_are_strings(self) -> None:
        """Verify role values are strings."""
        for role in AgentRole:
            assert isinstance(role.value, str)


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_create_config(self) -> None:
        """Test creating an agent configuration."""
        config = AgentConfig(
            role=AgentRole.DEV,
            goal="Write code",
            backstory="A skilled developer",
        )
        assert config.role == AgentRole.DEV
        assert config.goal == "Write code"
        assert config.backstory == "A skilled developer"
        assert config.verbose is True  # default
        assert config.allow_delegation is False  # default
        assert config.tools == []  # default
        assert config.memory is True  # default

    def test_config_with_custom_values(self) -> None:
        """Test configuration with custom values."""
        config = AgentConfig(
            role=AgentRole.PM,
            goal="Manage projects",
            backstory="An experienced PM",
            verbose=False,
            allow_delegation=True,
            memory=False,
        )
        assert config.verbose is False
        assert config.allow_delegation is True
        assert config.memory is False


class TestDefaultAgentConfigs:
    """Tests for default agent configurations."""

    def test_all_roles_have_defaults(self) -> None:
        """Verify all roles have default configurations."""
        for role in AgentRole:
            assert role in DEFAULT_AGENT_CONFIGS

    def test_pm_allows_delegation(self) -> None:
        """Verify PM agent can delegate tasks."""
        pm_config = DEFAULT_AGENT_CONFIGS[AgentRole.PM]
        assert pm_config.allow_delegation is True

    def test_other_agents_no_delegation(self) -> None:
        """Verify other agents cannot delegate by default."""
        for role in AgentRole:
            if role != AgentRole.PM:
                config = DEFAULT_AGENT_CONFIGS[role]
                assert config.allow_delegation is False

    def test_all_configs_have_required_fields(self) -> None:
        """Verify all configs have required fields."""
        for role, config in DEFAULT_AGENT_CONFIGS.items():
            assert config.role == role
            assert config.goal
            assert config.backstory

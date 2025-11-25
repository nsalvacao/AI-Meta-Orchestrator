"""Unit tests for plugin system."""

from typing import Any

from ai_meta_orchestrator.domain.agents.agent_models import AgentConfig, AgentRole
from ai_meta_orchestrator.domain.plugins.plugin_models import (
    AgentPlugin,
    HookPlugin,
    HookPoint,
    PluginInterface,
    PluginMetadata,
    PluginRegistry,
    PluginStatus,
    PluginType,
    ToolPlugin,
)
from ai_meta_orchestrator.domain.tasks.task_models import Task, TaskResult


class MockPlugin(PluginInterface):
    """Mock plugin for testing."""

    def __init__(self, name: str = "mock") -> None:
        """Initialize the mock plugin."""
        self._name = name
        self._initialized = False
        self._shutdown = False

    @property
    def metadata(self) -> PluginMetadata:
        """Get mock plugin metadata."""
        return PluginMetadata(
            name=self._name,
            version="1.0.0",
            description="A mock plugin",
            plugin_type=PluginType.TOOL,
            author="Test",
            tags=["test", "mock"],
        )

    def initialize(self, config: dict[str, Any]) -> bool:
        """Initialize the mock plugin."""
        self._initialized = True
        return True

    def shutdown(self) -> None:
        """Shutdown the mock plugin."""
        self._shutdown = True


class MockAgentPlugin(AgentPlugin):
    """Mock agent plugin for testing."""

    @property
    def metadata(self) -> PluginMetadata:
        """Get agent plugin metadata."""
        return PluginMetadata(
            name="mock_agent",
            version="1.0.0",
            description="A mock agent plugin",
            plugin_type=PluginType.AGENT,
        )

    @property
    def agent_role(self) -> str:
        """Get the agent role name."""
        return "mock_role"

    @property
    def agent_config(self) -> AgentConfig:
        """Get agent configuration."""
        return AgentConfig(
            role=AgentRole.DEV,
            goal="Mock goal",
            backstory="Mock backstory",
        )

    def initialize(self, config: dict[str, Any]) -> bool:
        """Initialize the agent plugin."""
        return True

    def shutdown(self) -> None:
        """Shutdown the agent plugin."""
        pass

    def execute_task(self, task: Task) -> TaskResult:
        """Execute a task."""
        return TaskResult(success=True, output="mock output")

    def can_handle(self, task: Task) -> bool:
        """Check if can handle task."""
        return True


class MockToolPlugin(ToolPlugin):
    """Mock tool plugin for testing."""

    @property
    def metadata(self) -> PluginMetadata:
        """Get tool plugin metadata."""
        return PluginMetadata(
            name="mock_tool",
            version="1.0.0",
            description="A mock tool plugin",
            plugin_type=PluginType.TOOL,
        )

    @property
    def tool_name(self) -> str:
        """Get tool name."""
        return "mock_tool"

    @property
    def tool_description(self) -> str:
        """Get tool description."""
        return "A mock tool for testing"

    def initialize(self, config: dict[str, Any]) -> bool:
        """Initialize the tool plugin."""
        return True

    def shutdown(self) -> None:
        """Shutdown the tool plugin."""
        pass

    def execute(self, **kwargs: Any) -> Any:
        """Execute the tool."""
        return "executed"


class MockHookPlugin(HookPlugin):
    """Mock hook plugin for testing."""

    def __init__(self) -> None:
        """Initialize the mock hook plugin."""
        self.hooks_called: list[tuple[HookPoint, dict[str, Any]]] = []

    @property
    def metadata(self) -> PluginMetadata:
        """Get hook plugin metadata."""
        return PluginMetadata(
            name="mock_hook",
            version="1.0.0",
            description="A mock hook plugin",
            plugin_type=PluginType.HOOK,
        )

    @property
    def hook_points(self) -> list[HookPoint]:
        """Get hook points."""
        return [HookPoint.BEFORE_TASK_EXECUTE, HookPoint.AFTER_TASK_EXECUTE]

    def initialize(self, config: dict[str, Any]) -> bool:
        """Initialize the hook plugin."""
        return True

    def shutdown(self) -> None:
        """Shutdown the hook plugin."""
        pass

    def on_hook(
        self,
        hook_point: HookPoint,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle a hook event."""
        self.hooks_called.append((hook_point, context.copy()))
        context["hook_triggered"] = True
        return context


class TestPluginMetadata:
    """Tests for PluginMetadata."""

    def test_create_metadata(self) -> None:
        """Test creating plugin metadata."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="A test plugin",
            plugin_type=PluginType.TOOL,
            author="Test Author",
            tags=["test", "example"],
        )

        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.plugin_type == PluginType.TOOL
        assert "test" in metadata.tags


class TestPluginRegistry:
    """Tests for PluginRegistry."""

    def test_register_plugin(self) -> None:
        """Test registering a plugin."""
        registry = PluginRegistry()
        plugin = MockPlugin("test")

        result = registry.register(plugin)

        assert result is True
        loaded = registry.get("test")
        assert loaded is not None
        assert loaded.status == PluginStatus.ACTIVE

    def test_register_duplicate_returns_false(self) -> None:
        """Test that registering duplicate returns False."""
        registry = PluginRegistry()
        plugin = MockPlugin("test")

        registry.register(plugin)
        result = registry.register(MockPlugin("test"))

        assert result is False

    def test_unregister_plugin(self) -> None:
        """Test unregistering a plugin."""
        registry = PluginRegistry()
        plugin = MockPlugin("test")
        registry.register(plugin)

        result = registry.unregister("test")

        assert result is True
        assert registry.get("test") is None
        assert plugin._shutdown is True

    def test_unregister_nonexistent(self) -> None:
        """Test unregistering non-existent plugin."""
        registry = PluginRegistry()

        result = registry.unregister("nonexistent")

        assert result is False

    def test_get_by_type(self) -> None:
        """Test getting plugins by type."""
        registry = PluginRegistry()
        tool_plugin = MockToolPlugin()
        agent_plugin = MockAgentPlugin()

        registry.register(tool_plugin)
        registry.register(agent_plugin)

        tools = registry.get_by_type(PluginType.TOOL)
        agents = registry.get_by_type(PluginType.AGENT)

        assert len(tools) == 1
        assert len(agents) == 1

    def test_get_agent_plugins(self) -> None:
        """Test getting agent plugins."""
        registry = PluginRegistry()
        agent_plugin = MockAgentPlugin()
        tool_plugin = MockToolPlugin()

        registry.register(agent_plugin)
        registry.register(tool_plugin)

        agents = registry.get_agent_plugins()

        assert len(agents) == 1
        assert isinstance(agents[0], AgentPlugin)

    def test_get_tool_plugins(self) -> None:
        """Test getting tool plugins."""
        registry = PluginRegistry()
        tool_plugin = MockToolPlugin()

        registry.register(tool_plugin)

        tools = registry.get_tool_plugins()

        assert len(tools) == 1
        assert isinstance(tools[0], ToolPlugin)

    def test_trigger_hook(self) -> None:
        """Test triggering hooks."""
        registry = PluginRegistry()
        hook_plugin = MockHookPlugin()
        registry.register(hook_plugin)

        context = {"test": "value"}
        result = registry.trigger_hook(HookPoint.BEFORE_TASK_EXECUTE, context)

        assert result.get("hook_triggered") is True
        assert len(hook_plugin.hooks_called) == 1
        assert hook_plugin.hooks_called[0][0] == HookPoint.BEFORE_TASK_EXECUTE

    def test_list_all(self) -> None:
        """Test listing all plugins."""
        registry = PluginRegistry()
        registry.register(MockPlugin("a"))
        registry.register(MockPlugin("b"))

        all_plugins = registry.list_all()

        assert len(all_plugins) == 2

    def test_get_active_count(self) -> None:
        """Test counting active plugins."""
        registry = PluginRegistry()
        registry.register(MockPlugin("a"))
        registry.register(MockPlugin("b"))

        count = registry.get_active_count()

        assert count == 2


class TestPluginTypes:
    """Tests for different plugin types."""

    def test_plugin_type_values(self) -> None:
        """Test plugin type enum values."""
        assert PluginType.AGENT.value == "agent"
        assert PluginType.TOOL.value == "tool"
        assert PluginType.EVALUATOR.value == "evaluator"
        assert PluginType.HOOK.value == "hook"
        assert PluginType.ADAPTER.value == "adapter"

    def test_plugin_status_values(self) -> None:
        """Test plugin status enum values."""
        assert PluginStatus.ACTIVE.value == "active"
        assert PluginStatus.INACTIVE.value == "inactive"
        assert PluginStatus.ERROR.value == "error"
        assert PluginStatus.LOADING.value == "loading"

    def test_hook_point_values(self) -> None:
        """Test hook point enum values."""
        assert HookPoint.BEFORE_WORKFLOW_START.value == "before_workflow_start"
        assert HookPoint.AFTER_WORKFLOW_COMPLETE.value == "after_workflow_complete"
        assert HookPoint.BEFORE_TASK_EXECUTE.value == "before_task_execute"
        assert HookPoint.AFTER_TASK_EXECUTE.value == "after_task_execute"

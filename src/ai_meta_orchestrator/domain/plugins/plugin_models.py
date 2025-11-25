"""Plugin system domain models.

This module provides the core models and interfaces for the plugin system,
allowing custom agents and extensions to be dynamically loaded and integrated.
"""

import contextlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from ai_meta_orchestrator.domain.agents.agent_models import AgentConfig
from ai_meta_orchestrator.domain.tasks.task_models import Task, TaskResult


class PluginType(str, Enum):
    """Types of plugins supported."""

    AGENT = "agent"
    TOOL = "tool"
    EVALUATOR = "evaluator"
    HOOK = "hook"
    ADAPTER = "adapter"


class PluginStatus(str, Enum):
    """Status of a loaded plugin."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    LOADING = "loading"


class HookPoint(str, Enum):
    """Available hook points in the orchestrator lifecycle."""

    BEFORE_WORKFLOW_START = "before_workflow_start"
    AFTER_WORKFLOW_COMPLETE = "after_workflow_complete"
    BEFORE_TASK_EXECUTE = "before_task_execute"
    AFTER_TASK_EXECUTE = "after_task_execute"
    ON_TASK_FAILURE = "on_task_failure"
    ON_EVALUATION_COMPLETE = "on_evaluation_complete"
    ON_REVISION_REQUEST = "on_revision_request"


@dataclass
class PluginMetadata:
    """Metadata describing a plugin.

    Attributes:
        id: Unique identifier for the plugin.
        name: Human-readable name of the plugin.
        version: Plugin version string.
        description: Description of what the plugin does.
        author: Plugin author name or organization.
        plugin_type: Type of plugin.
        dependencies: List of other plugin names this depends on.
        tags: Tags for plugin discovery.
        config_schema: JSON Schema for plugin configuration.
        created_at: When the plugin was registered.
    """

    name: str
    version: str
    description: str
    plugin_type: PluginType
    author: str = ""
    id: UUID = field(default_factory=uuid4)
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class PluginInterface(ABC):
    """Base interface for all plugins."""

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Get the plugin metadata."""
        pass

    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> bool:
        """Initialize the plugin with configuration.

        Args:
            config: Plugin-specific configuration.

        Returns:
            True if initialization successful.
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Clean up plugin resources."""
        pass


class AgentPlugin(PluginInterface):
    """Interface for agent plugins.

    Agent plugins provide custom AI agent implementations that can be
    integrated into the orchestrator workflow.
    """

    @property
    @abstractmethod
    def agent_role(self) -> str:
        """Get the role name for this agent plugin.

        Returns:
            A unique role name for this agent.
        """
        pass

    @property
    @abstractmethod
    def agent_config(self) -> AgentConfig:
        """Get the agent configuration.

        Returns:
            AgentConfig for this plugin agent.
        """
        pass

    @abstractmethod
    def execute_task(self, task: Task) -> TaskResult:
        """Execute a task.

        Args:
            task: The task to execute.

        Returns:
            TaskResult with the execution result.
        """
        pass

    @abstractmethod
    def can_handle(self, task: Task) -> bool:
        """Check if this agent can handle the given task.

        Args:
            task: The task to check.

        Returns:
            True if this agent can handle the task.
        """
        pass


class ToolPlugin(PluginInterface):
    """Interface for tool plugins.

    Tool plugins provide additional tools that can be used by agents
    during task execution.
    """

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Get the tool name."""
        pass

    @property
    @abstractmethod
    def tool_description(self) -> str:
        """Get the tool description for agent use."""
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """Execute the tool.

        Args:
            **kwargs: Tool-specific arguments.

        Returns:
            Tool execution result.
        """
        pass


class HookPlugin(PluginInterface):
    """Interface for hook plugins.

    Hook plugins can intercept and modify workflow execution at
    defined hook points.
    """

    @property
    @abstractmethod
    def hook_points(self) -> list[HookPoint]:
        """Get the hook points this plugin handles.

        Returns:
            List of HookPoint values.
        """
        pass

    @abstractmethod
    def on_hook(
        self,
        hook_point: HookPoint,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle a hook event.

        Args:
            hook_point: The hook point being triggered.
            context: Context data for the hook.

        Returns:
            Modified context (or original if no changes).
        """
        pass


@dataclass
class LoadedPlugin:
    """Represents a loaded and initialized plugin.

    Attributes:
        plugin: The plugin instance.
        metadata: Plugin metadata.
        status: Current status of the plugin.
        config: Configuration used to initialize.
        loaded_at: When the plugin was loaded.
        error_message: Error message if status is ERROR.
    """

    plugin: PluginInterface
    metadata: PluginMetadata
    status: PluginStatus = PluginStatus.LOADING
    config: dict[str, Any] = field(default_factory=dict)
    loaded_at: datetime = field(default_factory=datetime.now)
    error_message: str | None = None


class PluginRegistry:
    """Registry for managing loaded plugins.

    This class provides a central registry for discovering, loading,
    and managing plugins.
    """

    def __init__(self) -> None:
        """Initialize the plugin registry."""
        self._plugins: dict[str, LoadedPlugin] = {}
        self._by_type: dict[PluginType, list[str]] = {pt: [] for pt in PluginType}
        self._hooks: dict[HookPoint, list[str]] = {hp: [] for hp in HookPoint}

    def register(
        self,
        plugin: PluginInterface,
        config: dict[str, Any] | None = None,
    ) -> bool:
        """Register and initialize a plugin.

        Args:
            plugin: The plugin to register.
            config: Optional configuration for the plugin.

        Returns:
            True if registration successful.
        """
        metadata = plugin.metadata
        name = metadata.name

        if name in self._plugins:
            return False

        loaded = LoadedPlugin(
            plugin=plugin,
            metadata=metadata,
            config=config or {},
        )

        try:
            if plugin.initialize(config or {}):
                loaded.status = PluginStatus.ACTIVE
                self._plugins[name] = loaded
                self._by_type[metadata.plugin_type].append(name)

                # Register hooks if it's a hook plugin
                if isinstance(plugin, HookPlugin):
                    for hook_point in plugin.hook_points:
                        self._hooks[hook_point].append(name)

                return True
            else:
                loaded.status = PluginStatus.ERROR
                loaded.error_message = "Initialization returned False"
                self._plugins[name] = loaded
                return False
        except Exception as e:
            loaded.status = PluginStatus.ERROR
            loaded.error_message = str(e)
            self._plugins[name] = loaded
            return False

    def unregister(self, name: str) -> bool:
        """Unregister a plugin.

        Args:
            name: The plugin name.

        Returns:
            True if unregistered successfully.
        """
        if name not in self._plugins:
            return False

        loaded = self._plugins[name]
        plugin = loaded.plugin
        metadata = loaded.metadata

        with contextlib.suppress(Exception):
            plugin.shutdown()

        # Remove from type index
        if name in self._by_type[metadata.plugin_type]:
            self._by_type[metadata.plugin_type].remove(name)

        # Remove from hooks
        if isinstance(plugin, HookPlugin):
            for hook_point in plugin.hook_points:
                if name in self._hooks[hook_point]:
                    self._hooks[hook_point].remove(name)

        del self._plugins[name]
        return True

    def get(self, name: str) -> LoadedPlugin | None:
        """Get a loaded plugin by name.

        Args:
            name: The plugin name.

        Returns:
            LoadedPlugin or None if not found.
        """
        return self._plugins.get(name)

    def get_by_type(self, plugin_type: PluginType) -> list[LoadedPlugin]:
        """Get all plugins of a specific type.

        Args:
            plugin_type: The plugin type.

        Returns:
            List of loaded plugins.
        """
        return [self._plugins[name] for name in self._by_type.get(plugin_type, [])]

    def get_agent_plugins(self) -> list[AgentPlugin]:
        """Get all active agent plugins.

        Returns:
            List of AgentPlugin instances.
        """
        plugins = []
        for loaded in self.get_by_type(PluginType.AGENT):
            if (
                loaded.status == PluginStatus.ACTIVE
                and isinstance(loaded.plugin, AgentPlugin)
            ):
                plugins.append(loaded.plugin)
        return plugins

    def get_tool_plugins(self) -> list[ToolPlugin]:
        """Get all active tool plugins.

        Returns:
            List of ToolPlugin instances.
        """
        plugins = []
        for loaded in self.get_by_type(PluginType.TOOL):
            if (
                loaded.status == PluginStatus.ACTIVE
                and isinstance(loaded.plugin, ToolPlugin)
            ):
                plugins.append(loaded.plugin)
        return plugins

    def trigger_hook(
        self,
        hook_point: HookPoint,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Trigger a hook point and run all registered handlers.

        Args:
            hook_point: The hook point to trigger.
            context: Context data to pass to handlers.

        Returns:
            Modified context after all handlers.
        """
        for name in self._hooks.get(hook_point, []):
            loaded = self._plugins.get(name)
            if loaded and loaded.status == PluginStatus.ACTIVE:
                plugin = loaded.plugin
                if isinstance(plugin, HookPlugin):
                    with contextlib.suppress(Exception):
                        context = plugin.on_hook(hook_point, context)
        return context

    def list_all(self) -> list[LoadedPlugin]:
        """Get all registered plugins.

        Returns:
            List of all loaded plugins.
        """
        return list(self._plugins.values())

    def get_active_count(self) -> int:
        """Get count of active plugins.

        Returns:
            Number of active plugins.
        """
        return sum(
            1 for p in self._plugins.values()
            if p.status == PluginStatus.ACTIVE
        )

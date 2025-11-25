"""Platform detection and cross-OS utilities.

This module provides Linux-first, cross-OS aware utilities for
detecting and adapting to different operating system environments.
"""

import os
import platform
import shutil
from dataclasses import dataclass
from enum import Enum


class Platform(str, Enum):
    """Supported platforms."""

    LINUX = "linux"
    WINDOWS = "windows"
    MACOS = "macos"
    WSL = "wsl"
    UNKNOWN = "unknown"


@dataclass
class PlatformInfo:
    """Information about the current platform.

    Attributes:
        platform: The detected platform.
        system: The OS name (e.g., "Linux", "Windows").
        release: The OS release version.
        machine: The machine type (e.g., "x86_64", "arm64").
        python_version: The Python version string.
        is_wsl: Whether running in WSL.
        shell: The default shell path.
        home_dir: The user's home directory.
    """

    platform: Platform
    system: str
    release: str
    machine: str
    python_version: str
    is_wsl: bool
    shell: str | None
    home_dir: str


def detect_wsl() -> bool:
    """Detect if running in Windows Subsystem for Linux.

    Returns:
        True if running in WSL, False otherwise.
    """
    # Check for WSL-specific indicators
    if platform.system() != "Linux":
        return False

    # Check /proc/version for Microsoft/WSL
    try:
        with open("/proc/version") as f:
            version_info = f.read().lower()
            return "microsoft" in version_info or "wsl" in version_info
    except (FileNotFoundError, PermissionError):
        pass

    # Check for WSL environment variable
    if os.environ.get("WSL_DISTRO_NAME"):
        return True

    # Check for WSL interop
    return os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop")


def detect_platform() -> Platform:
    """Detect the current platform.

    Returns:
        The detected Platform enum value.
    """
    system = platform.system()

    if system == "Linux":
        if detect_wsl():
            return Platform.WSL
        return Platform.LINUX
    elif system == "Windows":
        return Platform.WINDOWS
    elif system == "Darwin":
        return Platform.MACOS
    else:
        return Platform.UNKNOWN


def get_default_shell() -> str | None:
    """Get the default shell for the current platform.

    Returns:
        Path to the default shell or None if not found.
    """
    # Check SHELL environment variable
    shell = os.environ.get("SHELL")
    if shell and shutil.which(shell):
        return shell

    # Platform-specific defaults
    detected_platform = detect_platform()

    if detected_platform in (Platform.LINUX, Platform.WSL, Platform.MACOS):
        # Try common shells
        for shell_path in ["/bin/bash", "/bin/sh", "/bin/zsh"]:
            if os.path.exists(shell_path):
                return shell_path
    elif detected_platform == Platform.WINDOWS:
        # Windows shells
        for shell_name in ["pwsh", "powershell", "cmd"]:
            found_shell = shutil.which(shell_name)
            if found_shell:
                return found_shell

    return None


def get_platform_info() -> PlatformInfo:
    """Get comprehensive information about the current platform.

    Returns:
        PlatformInfo instance with platform details.
    """
    detected_platform = detect_platform()
    is_wsl = detected_platform == Platform.WSL

    return PlatformInfo(
        platform=detected_platform,
        system=platform.system(),
        release=platform.release(),
        machine=platform.machine(),
        python_version=platform.python_version(),
        is_wsl=is_wsl,
        shell=get_default_shell(),
        home_dir=os.path.expanduser("~"),
    )


def get_path_separator() -> str:
    """Get the path separator for the current platform.

    Returns:
        The path separator character.
    """
    return os.sep


def normalize_path(path: str) -> str:
    """Normalize a path for the current platform.

    Args:
        path: The path to normalize.

    Returns:
        The normalized path.
    """
    return os.path.normpath(os.path.expanduser(path))


def is_executable(path: str) -> bool:
    """Check if a path points to an executable file.

    Args:
        path: The path to check.

    Returns:
        True if the path is an executable file.
    """
    return os.path.isfile(path) and os.access(path, os.X_OK)


def find_executable(name: str) -> str | None:
    """Find an executable by name.

    Args:
        name: The executable name.

    Returns:
        The full path to the executable or None if not found.
    """
    return shutil.which(name)

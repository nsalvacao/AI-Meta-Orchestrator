"""Unit tests for platform detection utilities."""

import os
import platform
from unittest.mock import mock_open, patch

from ai_meta_orchestrator.infrastructure.platform import (
    Platform,
    PlatformInfo,
    detect_platform,
    detect_wsl,
    get_platform_info,
    normalize_path,
)


class TestDetectWSL:
    """Tests for WSL detection."""

    def test_not_linux_returns_false(self) -> None:
        """Test that non-Linux systems return False."""
        with patch("platform.system", return_value="Windows"):
            assert detect_wsl() is False

    def test_linux_without_wsl_indicators(self) -> None:
        """Test Linux without WSL indicators."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", mock_open(read_data="Linux version 5.4.0")),
            patch.dict(os.environ, {}, clear=True),
            patch("os.path.exists", return_value=False),
        ):
            assert detect_wsl() is False

    def test_linux_with_microsoft_in_proc_version(self) -> None:
        """Test Linux with Microsoft in /proc/version."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", mock_open(read_data="Linux version 5.4.0-microsoft-standard")),
        ):
            assert detect_wsl() is True

    def test_linux_with_wsl_env_var(self) -> None:
        """Test Linux with WSL_DISTRO_NAME environment variable."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=FileNotFoundError),
            patch.dict(os.environ, {"WSL_DISTRO_NAME": "Ubuntu"}, clear=True),
        ):
            assert detect_wsl() is True


class TestDetectPlatform:
    """Tests for platform detection."""

    def test_detect_windows(self) -> None:
        """Test detecting Windows platform."""
        with patch("platform.system", return_value="Windows"):
            assert detect_platform() == Platform.WINDOWS

    def test_detect_macos(self) -> None:
        """Test detecting macOS platform."""
        with patch("platform.system", return_value="Darwin"):
            assert detect_platform() == Platform.MACOS

    def test_detect_linux(self) -> None:
        """Test detecting Linux platform."""
        with (
            patch("platform.system", return_value="Linux"),
            patch(
                "ai_meta_orchestrator.infrastructure.platform.detect_wsl",
                return_value=False,
            ),
        ):
            assert detect_platform() == Platform.LINUX

    def test_detect_wsl_platform(self) -> None:
        """Test detecting WSL platform."""
        with (
            patch("platform.system", return_value="Linux"),
            patch(
                "ai_meta_orchestrator.infrastructure.platform.detect_wsl",
                return_value=True,
            ),
        ):
            assert detect_platform() == Platform.WSL

    def test_detect_unknown(self) -> None:
        """Test detecting unknown platform."""
        with patch("platform.system", return_value="SomeOS"):
            assert detect_platform() == Platform.UNKNOWN


class TestGetPlatformInfo:
    """Tests for getting platform information."""

    def test_returns_platform_info(self) -> None:
        """Test that get_platform_info returns PlatformInfo."""
        info = get_platform_info()
        assert isinstance(info, PlatformInfo)
        assert info.system == platform.system()
        assert info.python_version == platform.python_version()
        assert info.machine == platform.machine()

    def test_home_dir_set(self) -> None:
        """Test that home directory is set."""
        info = get_platform_info()
        assert info.home_dir == os.path.expanduser("~")


class TestNormalizePath:
    """Tests for path normalization."""

    def test_normalize_home_path(self) -> None:
        """Test normalizing path with home directory."""
        normalized = normalize_path("~/test")
        assert not normalized.startswith("~")
        assert normalized.startswith(os.path.expanduser("~"))

    def test_normalize_relative_path(self) -> None:
        """Test normalizing relative path."""
        normalized = normalize_path("./test/../other")
        assert ".." not in normalized

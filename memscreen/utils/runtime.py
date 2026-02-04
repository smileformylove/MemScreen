"""
Runtime path utilities for MemScreen.

Handles resource path resolution for both development and PyInstaller-bundled environments.
When bundled with PyInstaller, resources are extracted to a temporary folder (sys._MEIPASS).
This module provides a unified interface for accessing resources in both environments.
"""

import sys
import os
from pathlib import Path
from typing import Union


def get_base_path() -> str:
    """
    Get the base path for the application.

    Returns:
        str: Base path (sys._MEIPASS for PyInstaller bundle, current directory otherwise)
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Not running from PyInstaller bundle - use current directory
        base_path = os.path.abspath(".")
    return base_path


def get_resource_path(relative_path: Union[str, Path]) -> str:
    """
    Get absolute path to resource, works for both development and PyInstaller.

    This function should be used whenever accessing files that are bundled
    with the application (e.g., assets, data files, configuration files).

    Args:
        relative_path: Relative path to the resource from the base directory

    Returns:
        str: Absolute path to the resource

    Examples:
        >>> # Load an asset image
        >>> icon_path = get_resource_path("assets/logo.png")
        >>> img = PIL.Image.open(icon_path)

        >>> # Load configuration file
        >>> config_path = get_resource_path("config.yaml")
        >>> with open(config_path, 'r') as f:
        ...     config = yaml.safe_load(f)
    """
    base_path = get_base_path()
    return os.path.join(base_path, str(relative_path))


def get_asset_path(asset_name: str) -> str:
    """
    Get absolute path to an asset file.

    Convenience function for accessing files in the assets directory.

    Args:
        asset_name: Name of the asset file (relative to assets/ directory)

    Returns:
        str: Absolute path to the asset

    Examples:
        >>> logo_path = get_asset_path("logo.png")
        >>> icon_path = get_asset_path("icons/app_icon.ico")
    """
    return get_resource_path(os.path.join("assets", asset_name))


def get_data_path(data_name: str) -> str:
    """
    Get absolute path to a data file.

    Convenience function for accessing data files.

    Args:
        data_name: Name of the data file (relative to data/ directory or base)

    Returns:
        str: Absolute path to the data file
    """
    return get_resource_path(os.path.join("data", data_name))


def get_user_data_dir() -> str:
    """
    Get the user data directory for storing application data.

    This directory is used for storing user-specific data like databases,
    cache files, and user preferences. It's located in the platform's
    standard user data directory.

    Returns:
        str: Path to the user data directory

    Platform-specific locations:
        macOS: ~/Library/Application Support/MemScreen
        Windows: %APPDATA%/MemScreen
        Linux: ~/.local/share/MemScreen
    """
    system = sys.platform

    if system == "darwin":
        # macOS
        path = os.path.expanduser("~/Library/Application Support/MemScreen")
    elif system == "win32":
        # Windows
        path = os.path.join(os.environ.get("APPDATA", "."), "MemScreen")
    else:
        # Linux and others
        path = os.path.expanduser("~/.local/share/MemScreen")

    # Create directory if it doesn't exist
    os.makedirs(path, exist_ok=True)

    return path


def get_user_config_dir() -> str:
    """
    Get the user config directory for storing configuration files.

    Returns:
        str: Path to the user config directory

    Platform-specific locations:
        macOS: ~/Library/Preferences/MemScreen
        Windows: %APPDATA%/MemScreen
        Linux: ~/.config/MemScreen
    """
    system = sys.platform

    if system == "darwin":
        # macOS
        path = os.path.expanduser("~/Library/Preferences/MemScreen")
    elif system == "win32":
        # Windows
        path = os.path.join(os.environ.get("APPDATA", "."), "MemScreen")
    else:
        # Linux and others
        path = os.path.expanduser("~/.config/MemScreen")

    # Create directory if it doesn't exist
    os.makedirs(path, exist_ok=True)

    return path


def get_user_cache_dir() -> str:
    """
    Get the user cache directory for storing temporary files.

    Returns:
        str: Path to the user cache directory

    Platform-specific locations:
        macOS: ~/Library/Caches/MemScreen
        Windows: %LOCALAPPDATA%/MemScreen/Cache
        Linux: ~/.cache/MemScreen
    """
    system = sys.platform

    if system == "darwin":
        # macOS
        path = os.path.expanduser("~/Library/Caches/MemScreen")
    elif system == "win32":
        # Windows
        local_appdata = os.environ.get("LOCALAPPDATA",
                                       os.path.join(os.environ.get("APPDATA", "."), "Local"))
        path = os.path.join(local_appdata, "MemScreen", "Cache")
    else:
        # Linux and others
        path = os.path.expanduser("~/.cache/MemScreen")

    # Create directory if it doesn't exist
    os.makedirs(path, exist_ok=True)

    return path


def is_bundled() -> bool:
    """
    Check if the application is running from a PyInstaller bundle.

    Returns:
        bool: True if running from PyInstaller bundle, False otherwise
    """
    return hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS')


def get_executable_dir() -> str:
    """
    Get the directory containing the executable.

    Returns:
        str: Directory path of the executable
    """
    if is_bundled():
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

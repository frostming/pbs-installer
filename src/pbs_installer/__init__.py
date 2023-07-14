"""
Installer for Python Build Standalone

Author: frostming
License: MIT
"""

from ._install import download, get_download_link, install, install_file
from ._utils import PythonVersion

__all__ = ["install", "download", "get_download_link", "install_file", "PythonVersion"]

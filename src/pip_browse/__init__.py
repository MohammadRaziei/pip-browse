"""pip-browse - A Python package for browsing PyPI packages and analyzing dependencies."""

from .__about__ import __version__
from .core import PyPIBrowser, PackageInfo, WheelFile, Dependency

__all__ = [
    "__version__",
    "PyPIBrowser", 
    "PackageInfo",
    "WheelFile",
    "Dependency",
]

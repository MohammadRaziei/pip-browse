"""Tests for core functionality including dependency extraction."""

import pytest
from pip_browse.core import (
    PyPIBrowser,
    PackageInfo,
    WheelFile,
    Dependency,
    PackageTag,
)


class TestDependency:
    """Test Dependency class."""

    def test_dependency_without_condition(self):
        """Test dependency without condition."""
        dep = Dependency("requests")
        assert dep.package == "requests"
        assert dep.condition is None
        assert str(dep) == "requests"

    def test_dependency_with_condition(self):
        """Test dependency with condition."""
        dep = Dependency("requests", ">=2.25.0")
        assert dep.package == "requests"
        assert dep.condition == ">=2.25.0"
        assert str(dep) == "requests >=2.25.0"

    def test_dependency_repr(self):
        """Test dependency string representation."""
        dep1 = Dependency("pytest")
        assert repr(dep1) == "pytest"
        
        dep2 = Dependency("pytest", ">=6.0")
        assert repr(dep2) == "pytest >=6.0"


class TestWheelFile:
    """Test WheelFile class."""

    def test_wheel_file_creation(self):
        """Test wheel file creation."""
        wheel = WheelFile(
            "https://example.com/package.whl",
            "package-1.0.0-py3-none-any.whl",
            "2.5 KiB"
        )
        assert wheel.url == "https://example.com/package.whl"
        assert wheel.name == "package-1.0.0-py3-none-any.whl"
        assert wheel.raw_size == "2.5 KiB"

    def test_size_conversion_bytes(self):
        """Test size conversion for bytes."""
        wheel = WheelFile("", "", "951 bytes")
        assert wheel.size == 951

    def test_size_conversion_kib(self):
        """Test size conversion for KiB."""
        wheel = WheelFile("", "", "2.2 KiB")
        assert wheel.size == 2252  # 2.2 * 1024

    def test_size_conversion_mib(self):
        """Test size conversion for MiB."""
        wheel = WheelFile("", "", "1.5 MiB")
        assert wheel.size == 1572864  # 1.5 * 1024 * 1024

    def test_size_conversion_gib(self):
        """Test size conversion for GiB."""
        wheel = WheelFile("", "", "0.5 GiB")
        assert wheel.size == 536870912  # 0.5 * 1024 * 1024 * 1024


class TestPackageTag:
    """Test PackageTag class."""

    def test_package_tag_creation(self):
        """Test package tag creation."""
        wheels = [
            {"name": "package-1.0.0-py3-none-any.whl", "url": "https://example.com/1"},
            {"name": "package-1.0.0.tar.gz", "url": "https://example.com/2"},
        ]
        tag = PackageTag("Python 3", wheels)
        assert tag.tag == "Python 3"
        assert tag.wheels == wheels


class TestPackageInfo:
    """Test PackageInfo class."""

    def test_package_info_creation(self):
        """Test package info creation."""
        dependency = Dependency("requests", ">=2.25.0")
        wheel = WheelFile("https://example.com/package.whl", "package.whl", "2.5 KiB")
        tag = PackageTag("Python 3", [{"name": "package.whl", "url": "https://example.com/"}])
        
        package_info = PackageInfo(
            name="test-package",
            tags=[tag],
            metadata={"Version": "1.0.0"},
            dependencies=[dependency],
            optional_dependencies={"test": [dependency]},
            wheel_files=[wheel]
        )
        
        assert package_info.name == "test-package"
        assert len(package_info.tags) == 1
        assert package_info.metadata["Version"] == "1.0.0"
        assert len(package_info.dependencies) == 1
        assert len(package_info.optional_dependencies["test"]) == 1
        assert len(package_info.wheel_files) == 1


class TestPyPIBrowser:
    """Test PyPIBrowser class."""

    def test_browser_initialization(self):
        """Test browser initialization."""
        browser = PyPIBrowser()
        assert browser.base_url == "https://pypi-browser.org/package/"
        assert browser.timeout == 15

    def test_browser_with_custom_url(self):
        """Test browser with custom URL."""
        browser = PyPIBrowser(base_url="https://custom-pypi.org/", timeout=30)
        assert browser.base_url == "https://custom-pypi.org/"
        assert browser.timeout == 30

    def test_extract_dependencies_basic(self):
        """Test basic dependency extraction."""
        browser = PyPIBrowser()
        metadata = {
            "Requires-Dist": [
                "requests",
                "pytest; extra == 'test'",
                "coverage; extra == 'test'",
            ]
        }
        
        dependencies, optional_dependencies = browser.extract_dependencies(metadata)
        
        assert len(dependencies) == 1
        assert dependencies[0].package == "requests"
        assert dependencies[0].condition is None
        
        assert "test" in optional_dependencies
        assert len(optional_dependencies["test"]) == 2
        assert optional_dependencies["test"][0].package == "pytest"
        assert optional_dependencies["test"][1].package == "coverage"

    def test_extract_dependencies_with_conditions(self):
        """Test dependency extraction with version conditions."""
        browser = PyPIBrowser()
        metadata = {
            "Requires-Dist": [
                "requests>=2.25.0",
                "pytest>=6.0; extra == 'test'",
                "coverage>=5.0; python_version >= '3.8'",
            ]
        }
        
        dependencies, optional_dependencies = browser.extract_dependencies(metadata)
        
        assert len(dependencies) == 2
        assert dependencies[0].package == "requests"
        assert dependencies[0].condition == ">=2.25.0"
        assert dependencies[1].package == "coverage"
        assert dependencies[1].condition == ">=5.0; python_version >= '3.8'"
        
        assert "test" in optional_dependencies
        assert optional_dependencies["test"][0].package == "pytest"
        assert optional_dependencies["test"][0].condition == ">=6.0"

    def test_extract_dependencies_multiple_extras(self):
        """Test dependency extraction with multiple extras."""
        browser = PyPIBrowser()
        metadata = {
            "Requires-Dist": [
                "requests; extra == 'online'",
                "pytest; extra == 'test'",
                "coverage; extra == 'test'",
                "mypy; extra == 'dev'",
            ]
        }
        
        dependencies, optional_dependencies = browser.extract_dependencies(metadata)
        
        assert len(dependencies) == 0
        assert "online" in optional_dependencies
        assert "test" in optional_dependencies
        assert "dev" in optional_dependencies
        assert len(optional_dependencies["test"]) == 2
        assert len(optional_dependencies["dev"]) == 1

    def test_extract_dependencies_complex_conditions(self):
        """Test dependency extraction with complex conditions."""
        browser = PyPIBrowser()
        metadata = {
            "Requires-Dist": [
                "examplepkg >=1.0; python_version >= '3.8' and sys_platform != 'win32'",
                "anotherpkg; extra == 'test' and python_version < '3.10'",
            ]
        }
        
        dependencies, optional_dependencies = browser.extract_dependencies(metadata)
        
        assert len(dependencies) == 1
        assert dependencies[0].package == "examplepkg"
        assert dependencies[0].condition == ">=1.0; python_version >= '3.8' and sys_platform != 'win32'"
        
        assert "test" in optional_dependencies
        assert optional_dependencies["test"][0].package == "anotherpkg"
        assert optional_dependencies["test"][0].condition == "and python_version < '3.10'"

    def test_extract_dependencies_single_string(self):
        """Test dependency extraction when Requires-Dist is a single string."""
        browser = PyPIBrowser()
        metadata = {
            "Requires-Dist": "requests>=2.25.0"
        }
        
        dependencies, optional_dependencies = browser.extract_dependencies(metadata)
        
        assert len(dependencies) == 1
        assert dependencies[0].package == "requests"
        assert dependencies[0].condition == ">=2.25.0"

    def test_extract_dependencies_empty(self):
        """Test dependency extraction with empty Requires-Dist."""
        browser = PyPIBrowser()
        metadata = {
            "Requires-Dist": []
        }
        
        dependencies, optional_dependencies = browser.extract_dependencies(metadata)
        
        assert len(dependencies) == 0
        assert len(optional_dependencies) == 0

    def test_extract_dependencies_no_requires_dist(self):
        """Test dependency extraction when Requires-Dist is not present."""
        browser = PyPIBrowser()
        metadata = {}
        
        dependencies, optional_dependencies = browser.extract_dependencies(metadata)
        
        assert len(dependencies) == 0
        assert len(optional_dependencies) == 0


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_dependency_extraction_from_real_metadata(self):
        """Test dependency extraction from real METADATA format."""
        browser = PyPIBrowser()
        
        # Simulate parsed metadata from a real package
        metadata = {
            "Name": "test-package",
            "Version": "1.0.0",
            "Requires-Dist": [
                "filelock",
                "pytest-xdist; extra == 'test'",
                "requests; extra == 'test'",
                "requests; extra == 'online'",
                "examplepkg >=1.0; python_version >= '3.8' and sys_platform != 'win32'",
            ]
        }
        
        dependencies, optional_dependencies = browser.extract_dependencies(metadata)
        
        # Check main dependencies
        assert len(dependencies) == 2
        assert dependencies[0].package == "filelock"
        assert dependencies[1].package == "examplepkg"
        assert dependencies[1].condition == ">=1.0; python_version >= '3.8' and sys_platform != 'win32'"
        
        # Check optional dependencies
        assert "test" in optional_dependencies
        assert "online" in optional_dependencies
        assert len(optional_dependencies["test"]) == 2
        assert len(optional_dependencies["online"]) == 1
        
        # Verify specific packages in extras
        test_packages = [dep.package for dep in optional_dependencies["test"]]
        assert "pytest-xdist" in test_packages
        assert "requests" in test_packages
        
        online_packages = [dep.package for dep in optional_dependencies["online"]]
        assert "requests" in online_packages

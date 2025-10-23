"""Tests for metadata parser functionality."""

import pytest
from pip_browse.metadata_parser import (
    parse_metadata,
    extract_required_python_version,
    extract_license_info,
    extract_project_urls,
)


class TestParseMetadata:
    """Test parse_metadata function with various METADATA formats."""

    def test_basic_metadata_parsing(self):
        """Test parsing basic METADATA fields."""
        metadata_text = """Metadata-Version: 2.1
Name: test-package
Version: 1.0.0
Summary: A test package
Author: Test Author
Author-email: test@example.com
License: MIT
Classifier: Development Status :: 4 - Beta
Classifier: Programming Language :: Python :: 3
Classifier: Programming Language :: Python :: 3.7
Classifier: Programming Language :: Python :: 3.8

This is a test package description.
It spans multiple lines.
"""
        result = parse_metadata(metadata_text)

        assert result["Metadata-Version"] == "2.1"
        assert result["Name"] == "test-package"
        assert result["Version"] == "1.0.0"
        assert result["Summary"] == "A test package"
        assert result["Author"] == "Test Author"
        assert result["Author-email"] == "test@example.com"
        assert result["License"] == "MIT"
        assert result["Classifier"] == [
            "Development Status :: 4 - Beta",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
        ]
        assert result["Description"] == "This is a test package description.\nIt spans multiple lines."

    def test_continuation_lines(self):
        """Test parsing continuation lines."""
        metadata_text = """Name: test-package
Description: This is a long description
    that continues on the next line
    and another line.
Version: 1.0.0
"""
        result = parse_metadata(metadata_text)

        assert result["Name"] == "test-package"
        assert result["Version"] == "1.0.0"
        assert result["Description"] == "This is a long description that continues on the next line and another line."

    def test_multiple_values_for_same_key(self):
        """Test handling multiple values for fields that can repeat."""
        metadata_text = """Name: test-package
Requires-Dist: requests
Requires-Dist: pytest; extra == 'test'
Requires-Dist: coverage; extra == 'test'
Classifier: Development Status :: 4 - Beta
Classifier: License :: OSI Approved :: MIT License
"""
        result = parse_metadata(metadata_text)

        assert result["Name"] == "test-package"
        assert result["Requires-Dist"] == [
            "requests",
            "pytest; extra == 'test'",
            "coverage; extra == 'test'",
        ]
        assert result["Classifier"] == [
            "Development Status :: 4 - Beta",
            "License :: OSI Approved :: MIT License",
        ]

    def test_empty_description(self):
        """Test parsing metadata with empty description."""
        metadata_text = """Name: test-package
Version: 1.0.0

"""
        result = parse_metadata(metadata_text)

        assert result["Name"] == "test-package"
        assert result["Version"] == "1.0.0"
        assert "Description" not in result

    def test_project_urls_parsing(self):
        """Test parsing Project-URL fields."""
        metadata_text = """Name: test-package
Project-URL: Homepage, https://example.com
Project-URL: Documentation, https://docs.example.com
Project-URL: Source, https://github.com/example/test-package
"""
        result = parse_metadata(metadata_text)

        assert result["Name"] == "test-package"
        assert result["Project-URL"] == [
            "Homepage, https://example.com",
            "Documentation, https://docs.example.com",
            "Source, https://github.com/example/test-package",
        ]

    def test_real_world_metadata_example(self):
        """Test parsing a real-world METADATA example."""
        metadata_text = """Metadata-Version: 2.1
Name: requests
Version: 2.28.2
Summary: Python HTTP for Humans.
Home-page: https://requests.readthedocs.io
Author: Kenneth Reitz
Author-email: me@kennethreitz.org
License: Apache 2.0
Project-URL: Documentation, https://requests.readthedocs.io
Project-URL: Source, https://github.com/psf/requests
Requires-Python: >=3.7, <4
Requires-Dist: certifi>=2017.4.17
Requires-Dist: charset-normalizer~=2.0.0
Requires-Dist: idna<4,>=2.5
Requires-Dist: urllib3<1.27,>=1.21.1
Classifier: Development Status :: 5 - Production/Stable
Classifier: Intended Audience :: Developers
Classifier: License :: OSI Approved :: Apache Software License
Classifier: Natural Language :: English
Classifier: Programming Language :: Python :: 3
Classifier: Programming Language :: Python :: 3.7
Classifier: Programming Language :: Python :: 3.8
Classifier: Programming Language :: Python :: 3.9
Classifier: Programming Language :: Python :: 3.10
Classifier: Programming Language :: Python :: 3.11

Requests is an elegant and simple HTTP library for Python, built for
human beings.
"""
        result = parse_metadata(metadata_text)

        assert result["Name"] == "requests"
        assert result["Version"] == "2.28.2"
        assert result["Summary"] == "Python HTTP for Humans."
        assert result["Requires-Python"] == ">=3.7, <4"
        assert len(result["Requires-Dist"]) == 4
        assert len(result["Classifier"]) == 10
        assert "Requests is an elegant and simple HTTP library" in result["Description"]


class TestExtractRequiredPythonVersion:
    """Test extract_required_python_version function."""

    def test_extract_from_classifiers(self):
        """Test extracting Python version from classifiers."""
        metadata = {
            "Classifier": [
                "Development Status :: 5 - Production/Stable",
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
            ]
        }
        version = extract_required_python_version(metadata)
        assert version == "3.8"  # Should return the first specific version

    def test_no_python_version_in_classifiers(self):
        """Test when no Python version is specified in classifiers."""
        metadata = {
            "Classifier": [
                "Development Status :: 5 - Production/Stable",
                "License :: OSI Approved :: MIT License",
            ]
        }
        version = extract_required_python_version(metadata)
        assert version == ""

    def test_with_requires_python_field(self):
        """Test when Requires-Python field is present."""
        metadata = {
            "Requires-Python": ">=3.7",
            "Classifier": [
                "Programming Language :: Python :: 3.8",
            ]
        }
        # Note: Our current implementation only checks classifiers
        version = extract_required_python_version(metadata)
        assert version == "3.8"


class TestExtractLicenseInfo:
    """Test extract_license_info function."""

    def test_extract_from_license_field(self):
        """Test extracting license from License field."""
        metadata = {"License": "MIT License"}
        license_info = extract_license_info(metadata)
        assert license_info == "MIT License"

    def test_extract_from_classifiers(self):
        """Test extracting license from classifiers."""
        metadata = {
            "Classifier": [
                "Development Status :: 5 - Production/Stable",
                "License :: OSI Approved :: MIT License",
            ]
        }
        license_info = extract_license_info(metadata)
        assert license_info == "MIT License"

    def test_no_license_info(self):
        """Test when no license information is available."""
        metadata = {
            "Classifier": [
                "Development Status :: 5 - Production/Stable",
            ]
        }
        license_info = extract_license_info(metadata)
        assert license_info == ""


class TestExtractProjectUrls:
    """Test extract_project_urls function."""

    def test_extract_project_urls(self):
        """Test extracting project URLs."""
        metadata = {
            "Project-URL": [
                "Homepage, https://example.com",
                "Documentation, https://docs.example.com",
                "Source, https://github.com/example/test-package",
            ]
        }
        urls = extract_project_urls(metadata)
        assert urls == {
            "Homepage": "https://example.com",
            "Documentation": "https://docs.example.com",
            "Source": "https://github.com/example/test-package",
        }

    def test_no_project_urls(self):
        """Test when no project URLs are available."""
        metadata = {}
        urls = extract_project_urls(metadata)
        assert urls == {}

    def test_single_project_url(self):
        """Test with single project URL."""
        metadata = {
            "Project-URL": "Homepage, https://example.com"
        }
        urls = extract_project_urls(metadata)
        assert urls == {"Homepage": "https://example.com"}

#!/usr/bin/env python3
"""Demo script showing how to use pip-browse."""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pip_browse import PyPIBrowser, PackageInfo


def demo_basic_usage():
    """Demonstrate basic usage of pip-browse."""
    print("pip-browse Demo")
    print("=" * 50)
    
    # Create a browser instance
    browser = PyPIBrowser()
    print("✓ Created PyPIBrowser instance")
    
    # Test with a simple package (we'll use mock data for demo)
    print("\nTesting with mock data...")
    
    # Create a mock package info for demonstration
    from pip_browse.core import Dependency, WheelFile, PackageTag
    
    dependency = Dependency("requests", ">=2.25.0")
    wheel = WheelFile("https://example.com/package.whl", "package-1.0.0-py3-none-any.whl", "2.5 KiB")
    tag = PackageTag("Python 3", [{"name": "package.whl", "url": "https://example.com/"}])
    
    package_info = PackageInfo(
        name="demo-package",
        tags=[tag],
        metadata={
            "Version": "1.0.0",
            "Summary": "A demo package",
            "Author": "Demo Author",
            "License": "MIT",
            "Requires-Dist": ["requests>=2.25.0", "pytest; extra == 'test'"]
        },
        dependencies=[dependency],
        optional_dependencies={"test": [Dependency("pytest")]},
        wheel_files=[wheel]
    )
    
    print(f"✓ Created PackageInfo for: {package_info.name}")
    print(f"  - Version: {package_info.metadata.get('Version', 'N/A')}")
    print(f"  - Dependencies: {len(package_info.dependencies)}")
    print(f"  - Optional dependencies: {len(package_info.optional_dependencies)}")
    print(f"  - Wheel files: {len(package_info.wheel_files)}")
    
    # Show dependency extraction
    print("\nDependency Extraction Demo:")
    print("-" * 30)
    
    test_metadata = {
        "Requires-Dist": [
            "requests>=2.25.0",
            "pytest; extra == 'test'",
            "coverage; extra == 'test'",
            "mypy; extra == 'dev'",
        ]
    }
    
    dependencies, optional_dependencies = browser.extract_dependencies(test_metadata)
    
    print("Main dependencies:")
    for dep in dependencies:
        print(f"  • {dep}")
    
    print("\nOptional dependencies:")
    for extra, deps in optional_dependencies.items():
        print(f"  [{extra}]:")
        for dep in deps:
            print(f"    • {dep}")


def demo_cli_usage():
    """Demonstrate CLI usage."""
    print("\nCLI Usage Demo:")
    print("=" * 50)
    print("""
The pip-browse package provides a command-line interface with the following commands:

1. Get comprehensive package info:
   $ python -m pip_browse info requests

2. Show only dependencies:
   $ python -m pip_browse dependencies requests --include-optional

3. Show package files:
   $ python -m pip_browse files requests

4. Show package metadata:
   $ python -m pip_browse metadata requests

5. Output in JSON format:
   $ python -m pip_browse info requests --output-format json

All commands support:
  --base-url: Custom PyPI browser URL
  --timeout: Request timeout in seconds
""")


if __name__ == "__main__":
    demo_basic_usage()
    demo_cli_usage()
    print("\n🎉 pip-browse is ready to use!")

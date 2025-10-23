"""Command-line interface for pip-browse using Click."""

import json
import sys
from typing import Optional

import click

from . import PyPIBrowser, PackageInfo
from .utils import validate_package_name, normalize_package_name, format_file_size


@click.group()
@click.version_option()
def cli():
    """pip-browse - Browse PyPI packages and analyze dependencies."""
    pass


@cli.group()
def list():
    """List package information."""
    pass


@list.command()
@click.argument('package_name')
@click.option('--timeout', default=15, help='Request timeout in seconds')
def tags(package_name: str, timeout: int):
    """Show package tags."""
    if not validate_package_name(package_name):
        click.echo(f"Error: '{package_name}' is not a valid package name.", err=True)
        sys.exit(1)
    
    package_name = normalize_package_name(package_name)
    
    try:
        browser = PyPIBrowser(timeout=timeout)
        tags = browser.get_package_tags(package_name)
        
        if not tags:
            click.echo(f"No tags found for package: {package_name}")
            return
        
        click.echo(f"Tags for {package_name}:")
        click.echo("=" * 50)
        
        for tag in tags:
            click.echo(f"• {tag.tag} ({len(tag.wheels)} wheels)")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
def wheel():
    """Wheel file operations."""
    pass


@wheel.command()
@click.argument('package_spec')
@click.option('--timeout', default=15, help='Request timeout in seconds')
def wheels(package_spec: str, timeout: int):
    """Show wheels for a package."""
    # Parse package spec (could be package name or package==version)
    if '==' in package_spec:
        package_name, version = package_spec.split('==', 1)
    else:
        package_name = package_spec
        version = None
    
    if not validate_package_name(package_name):
        click.echo(f"Error: '{package_name}' is not a valid package name.", err=True)
        sys.exit(1)
    
    package_name = normalize_package_name(package_name)
    
    try:
        browser = PyPIBrowser(timeout=timeout)
        tags = browser.get_package_tags(package_name)
        
        if not tags:
            click.echo(f"No wheels found for package: {package_name}")
            return
        
        click.echo(f"Wheels for {package_spec}:")
        click.echo("=" * 50)
        
        for tag in tags:
            click.echo(f"\n{tag.tag}:")
            for wheel in tag.wheels:
                click.echo(f"  • {wheel['name']}")
                
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@wheel.command()
@click.argument('wheel_url')
@click.option('--timeout', default=15, help='Request timeout in seconds')
def metadata(wheel_url: str, timeout: int):
    """Get metadata for a specific wheel."""
    try:
        browser = PyPIBrowser(timeout=timeout)
        metadata = browser.get_package_metadata(wheel_url)
        
        if not metadata:
            click.echo(f"No metadata found for wheel: {wheel_url}")
            return
        
        # Output as JSON
        click.echo(json.dumps(metadata, indent=2))
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@wheel.command()
@click.argument('wheel_url')
@click.option('--timeout', default=15, help='Request timeout in seconds')
@click.option('--main', 'deps_type', flag_value='main', help='Show only main dependencies')
@click.option('--optional', 'deps_type', flag_value='optional', help='Show only optional dependencies')
@click.option('--optional-items', 'deps_type', flag_value='optional_items', help='Show only optional dependency items')
def requirements(wheel_url: str, timeout: int, deps_type: Optional[str]):
    """Get requirements for a specific wheel."""
    try:
        browser = PyPIBrowser(timeout=timeout)
        metadata = browser.get_package_metadata(wheel_url)
        
        if not metadata:
            click.echo(f"No metadata found for wheel: {wheel_url}")
            return
        
        dependencies, optional_dependencies = browser.extract_dependencies(metadata)
        
        if deps_type == 'main':
            # Show only main dependencies
            result = [
                {
                    "package": dep.package,
                    "condition": dep.condition
                }
                for dep in dependencies
            ]
            click.echo(json.dumps(result, indent=2))
            
        elif deps_type == 'optional':
            # Show only optional dependencies as JSON
            result = {
                extra: [
                    {
                        "package": dep.package,
                        "condition": dep.condition
                    }
                    for dep in deps
                ]
                for extra, deps in optional_dependencies.items()
            }
            click.echo(json.dumps(result, indent=2))
            
        elif deps_type == 'optional_items':
            # Show only optional dependency items (keys)
            result = list(optional_dependencies.keys())
            click.echo(json.dumps(result, indent=2))
            
        else:
            # Show both main and optional dependencies
            result = {
                "main": [
                    {
                        "package": dep.package,
                        "condition": dep.condition
                    }
                    for dep in dependencies
                ],
                "optional": {
                    extra: [
                        {
                            "package": dep.package,
                            "condition": dep.condition
                        }
                        for dep in deps
                    ]
                    for extra, deps in optional_dependencies.items()
                }
            }
            click.echo(json.dumps(result, indent=2))
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@wheel.command()
@click.argument('wheel_url')
@click.option('--timeout', default=15, help='Request timeout in seconds')
@click.option('-h', '--human-readable', is_flag=True, help='Show sizes in human-readable format')
def list(wheel_url: str, timeout: int, human_readable: bool):
    """List files in a wheel with their sizes."""
    try:
        browser = PyPIBrowser(timeout=timeout)
        wheel_files = browser.get_wheel_files(wheel_url)
        
        if not wheel_files:
            click.echo(f"No files found for wheel: {wheel_url}")
            return
        
        result = []
        for wheel_file in wheel_files:
            file_info = {
                "name": wheel_file.name,
                "url": wheel_file.url,
                "size_bytes": wheel_file.size
            }
            
            if human_readable:
                file_info["size_human"] = format_file_size(wheel_file.size)
            
            result.append(file_info)
        
        click.echo(json.dumps(result, indent=2))
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()

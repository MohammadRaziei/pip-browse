"""Command-line interface for pip-browse using Click."""

import json
import sys
from typing import Optional

import click

from . import PyPIBrowser, PackageInfo
from .utils import validate_package_name, normalize_package_name


@click.group()
@click.version_option()
def cli():
    """pip-browse - Browse PyPI packages and analyze dependencies."""
    pass


@cli.command()
@click.argument('package_name')
@click.option('--timeout', default=15, help='Request timeout in seconds')
@click.option('--output-format', type=click.Choice(['json', 'text']), default='text',
              help='Output format')
def info(package_name: str, timeout: int, output_format: str):
    """Get comprehensive information about a package."""
    if not validate_package_name(package_name):
        click.echo(f"Error: '{package_name}' is not a valid package name.", err=True)
        sys.exit(1)
    
    package_name = normalize_package_name(package_name)
    
    try:
        browser = PyPIBrowser(timeout=timeout)
        package_info = browser.get_package_info(package_name)
        
        if output_format == 'json':
            output_json(package_info)
        else:
            output_text(package_info)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('package_name')
@click.option('--timeout', default=15, help='Request timeout in seconds')
@click.option('--include-optional', is_flag=True, help='Include optional dependencies')
def dependencies(package_name: str, timeout: int, include_optional: bool):
    """Show package dependencies."""
    if not validate_package_name(package_name):
        click.echo(f"Error: '{package_name}' is not a valid package name.", err=True)
        sys.exit(1)
    
    package_name = normalize_package_name(package_name)
    
    try:
        browser = PyPIBrowser(timeout=timeout)
        package_info = browser.get_package_info(package_name)
        
        click.echo(f"Dependencies for {package_info.name}:")
        click.echo("=" * 50)
        
        if package_info.dependencies:
            click.echo("\nRequired dependencies:")
            for dep in package_info.dependencies:
                click.echo(f"  • {dep}")
        else:
            click.echo("\nNo required dependencies.")
        
        if include_optional and package_info.optional_dependencies:
            click.echo("\nOptional dependencies:")
            for extra, deps in package_info.optional_dependencies.items():
                click.echo(f"  [{extra}]:")
                for dep in deps:
                    click.echo(f"    • {dep}")
        elif include_optional:
            click.echo("\nNo optional dependencies.")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('package_name')
@click.option('--timeout', default=15, help='Request timeout in seconds')
def files(package_name: str, timeout: int):
    """Show package files and sizes."""
    if not validate_package_name(package_name):
        click.echo(f"Error: '{package_name}' is not a valid package name.", err=True)
        sys.exit(1)
    
    package_name = normalize_package_name(package_name)
    
    try:
        browser = PyPIBrowser(timeout=timeout)
        package_info = browser.get_package_info(package_name)
        
        click.echo(f"Files for {package_info.name}:")
        click.echo("=" * 50)
        
        if package_info.wheel_files:
            for wheel in package_info.wheel_files:
                click.echo(f"  • {wheel.name} ({wheel.raw_size})")
        else:
            click.echo("No files found.")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('package_name')
@click.option('--timeout', default=15, help='Request timeout in seconds')
def metadata(package_name: str, timeout: int):
    """Show package metadata."""
    if not validate_package_name(package_name):
        click.echo(f"Error: '{package_name}' is not a valid package name.", err=True)
        sys.exit(1)
    
    package_name = normalize_package_name(package_name)
    
    try:
        browser = PyPIBrowser(timeout=timeout)
        package_info = browser.get_package_info(package_name)
        
        click.echo(f"Metadata for {package_info.name}:")
        click.echo("=" * 50)
        
        for key, value in package_info.metadata.items():
            if isinstance(value, list):
                click.echo(f"{key}:")
                for item in value:
                    click.echo(f"  • {item}")
            else:
                click.echo(f"{key}: {value}")
                
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def output_json(package_info: PackageInfo):
    """Output package information in JSON format."""
    output = {
        "name": package_info.name,
        "tags": [
            {
                "tag": tag.tag,
                "wheels": tag.wheels
            }
            for tag in package_info.tags
        ],
        "metadata": package_info.metadata,
        "dependencies": [
            {
                "package": dep.package,
                "condition": dep.condition
            }
            for dep in package_info.dependencies
        ],
        "optional_dependencies": {
            extra: [
                {
                    "package": dep.package,
                    "condition": dep.condition
                }
                for dep in deps
            ]
            for extra, deps in package_info.optional_dependencies.items()
        },
        "wheel_files": [
            {
                "url": wheel.url,
                "name": wheel.name,
                "raw_size": wheel.raw_size,
                "size_bytes": wheel.size
            }
            for wheel in package_info.wheel_files
        ]
    }
    
    click.echo(json.dumps(output, indent=2))


def output_text(package_info: PackageInfo):
    """Output package information in human-readable text format."""
    click.echo(f"Package: {package_info.name}")
    click.echo("=" * 50)
    
    # Basic info from metadata
    if "Version" in package_info.metadata:
        click.echo(f"Version: {package_info.metadata['Version']}")
    if "Summary" in package_info.metadata:
        click.echo(f"Summary: {package_info.metadata['Summary']}")
    if "Author" in package_info.metadata:
        click.echo(f"Author: {package_info.metadata['Author']}")
    
    # Tags
    if package_info.tags:
        click.echo(f"\nTags ({len(package_info.tags)}):")
        for tag in package_info.tags:
            click.echo(f"  • {tag.tag} ({len(tag.wheels)} wheels)")
    
    # Dependencies
    if package_info.dependencies:
        click.echo(f"\nDependencies ({len(package_info.dependencies)}):")
        for dep in package_info.dependencies:
            click.echo(f"  • {dep}")
    
    # Optional dependencies
    if package_info.optional_dependencies:
        click.echo(f"\nOptional Dependencies:")
        for extra, deps in package_info.optional_dependencies.items():
            click.echo(f"  [{extra}] ({len(deps)}):")
            for dep in deps:
                click.echo(f"    • {dep}")
    
    # Wheel files
    if package_info.wheel_files:
        click.echo(f"\nFiles ({len(package_info.wheel_files)}):")
        for wheel in package_info.wheel_files:
            click.echo(f"  • {wheel.name} ({wheel.raw_size})")


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()

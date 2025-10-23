"""Command-line interface for pip-browse using Click."""

import json
import sys

import click

from . import PyPIBrowser
from .utils import validate_package_name, normalize_package_name


@click.group()
@click.version_option()
def cli():
    """pip-browse - Browse PyPI packages and analyze dependencies."""
    pass


@cli.command()
@click.argument('package_name')
@click.option('--timeout', default=15, help='Request timeout in seconds')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def tags(package_name: str, timeout: int, output_json: bool):
    """Show package tags."""
    if not validate_package_name(package_name):
        click.echo(f"Error: '{package_name}' is not a valid package name.", err=True)
        sys.exit(1)
    
    package_name = normalize_package_name(package_name)
    
    try:
        browser = PyPIBrowser(timeout=timeout)
        tags = browser.get_package_tags(package_name)
        
        if not tags:
            if output_json:
                click.echo(json.dumps({"error": f"No tags found for package: {package_name}"}))
            else:
                click.echo(f"No tags found for package: {package_name}")
            return
        
        if output_json:
            result = {
                "package": package_name,
                "tags": [tag.tag for tag in tags]
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Tags for {package_name}:")
            click.echo("=" * 50)
            
            for tag in tags:
                click.echo(f"• {tag.tag} ({len(tag.wheels)} wheels)")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('package_spec')
@click.option('--timeout', default=15, help='Request timeout in seconds')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def wheels(package_spec: str, timeout: int, output_json: bool):
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
            if output_json:
                click.echo(json.dumps({"error": f"No wheels found for package: {package_name}"}))
            else:
                click.echo(f"No wheels found for package: {package_name}")
            return
        
        if output_json:
            result = {
                "package": package_name,
                "package_spec": package_spec,
                "tags": [
                    {
                        "tag": tag.tag,
                        "wheels": [
                            {
                                "name": wheel["name"],
                                "url": wheel.get("pypi_url", "")
                            }
                            for wheel in tag.wheels
                        ]
                    }
                    for tag in tags
                ]
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Wheels for {package_spec}:")
            click.echo("=" * 50)
            
            for tag in tags:
                click.echo(f"\n{tag.tag}:")
                for wheel in tag.wheels:
                    click.echo(f"  • {wheel['name']}")
                
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('package_spec')
@click.option('--timeout', default=15, help='Request timeout in seconds')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def info(package_spec: str, timeout: int, output_json: bool):
    """Show comprehensive package information."""
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
        
        # Use the comprehensive data method from core
        result = browser.get_comprehensive_data(package_name)
        result["package_spec"] = package_spec
        
        if output_json:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"Comprehensive information for {package_spec}:")
            click.echo("=" * 60)
            click.echo(f"Package: {result['package']}")
            click.echo(f"Latest version: {result['tags'][0]['tag'] if result['tags'] else 'N/A'}")
            click.echo(f"Wheel count: {sum(len(tag['wheels']) for tag in result['tags'])}")
            click.echo(f"Dependencies: {len(result['info']['dependencies'])}")
            click.echo(f"Optional dependencies: {len(result['info']['optional_dependencies'])}")
            click.echo(f"Wheel files: {len(result['info']['wheel_files'])}")
                
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()

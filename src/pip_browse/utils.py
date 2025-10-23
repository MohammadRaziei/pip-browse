"""Utility functions for pip-browse package."""

import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

from curl_cffi import requests as creq


def validate_package_name(package_name: str) -> bool:
    """
    Validate if a string is a valid Python package name.
    
    Args:
        package_name: Package name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not package_name or not isinstance(package_name, str):
        return False
    
    # Basic package name validation (simplified)
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$'
    return bool(re.match(pattern, package_name))


def normalize_package_name(package_name: str) -> str:
    """
    Normalize package name to lowercase and remove extra spaces.
    
    Args:
        package_name: Package name to normalize
        
    Returns:
        Normalized package name
    """
    return package_name.strip().lower()


def is_valid_url(url: str) -> bool:
    """
    Check if a string is a valid URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable size string
    """
    if size_bytes == 0:
        return "0 bytes"
    
    size_names = ["bytes", "KiB", "MiB", "GiB", "TiB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024
        i += 1
    
    if i == 0:
        return f"{int(size)} {size_names[i]}"
    else:
        return f"{size:.1f} {size_names[i]}"


def fetch_content_simple(url: str, timeout: int = 10) -> Optional[str]:
    """
    Simple content fetcher using curl_cffi with Chrome impersonation.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        Content as string, or None if failed
    """
    try:
        resp = creq.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            impersonate="chrome",
        )
        
        if resp.status_code == 200:
            return resp.text
        return None
    except Exception:
        return None


def extract_version_from_filename(filename: str) -> Optional[str]:
    """
    Extract version from package filename.
    
    Args:
        filename: Package filename
        
    Returns:
        Version string if found, None otherwise
    """
    # Common patterns for version extraction
    patterns = [
        r'-(\d+\.\d+(?:\.\d+)*)',
        r'_(\d+\.\d+(?:\.\d+)*)',
        r'(\d+\.\d+(?:\.\d+)*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
    
    return None


def filter_wheels_by_platform(wheels: List[Dict[str, Any]], platform: str = "any") -> List[Dict[str, Any]]:
    """
    Filter wheels by platform compatibility.
    
    Args:
        wheels: List of wheel dictionaries
        platform: Platform to filter for ("any", "linux", "win", "macos")
        
    Returns:
        Filtered list of wheels
    """
    if platform == "any":
        return wheels
    
    platform_patterns = {
        "linux": r"linux",
        "win": r"win|windows",
        "macos": r"macosx|darwin",
    }
    
    pattern = platform_patterns.get(platform)
    if not pattern:
        return wheels
    
    filtered = []
    for wheel in wheels:
        wheel_name = wheel.get("name", "").lower()
        if re.search(pattern, wheel_name):
            filtered.append(wheel)
    
    return filtered


def get_python_version_compatibility(wheel_name: str) -> List[str]:
    """
    Extract Python version compatibility from wheel name.
    
    Args:
        wheel_name: Wheel filename
        
    Returns:
        List of compatible Python versions
    """
    # Patterns for Python version in wheel names
    patterns = [
        r'cp(\d+)(\d*)',  # cp38, cp310
        r'py(\d+)',       # py3, py2
        r'py(\d+\.\d+)',  # py3.8, py3.10
    ]
    
    versions = []
    for pattern in patterns:
        matches = re.findall(pattern, wheel_name)
        for match in matches:
            if len(match) == 1:
                version = match[0]
                if version == "2":
                    versions.append("2.7")
                elif version == "3":
                    versions.append("3.x")
                else:
                    versions.append(f"3.{version}")
            elif len(match) == 2:
                major, minor = match
                if minor:
                    versions.append(f"{major}.{minor}")
                else:
                    versions.append(f"{major}.x")
    
    return list(set(versions))  # Remove duplicates

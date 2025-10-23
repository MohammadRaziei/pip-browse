"""Metadata parser for Python package METADATA files."""

import re
from typing import Dict, List, Union, Any


def parse_metadata(metadata_text: str) -> Dict[str, Union[str, List[str]]]:
    """
    Parse a Python package METADATA file into a structured dictionary.
    
    Stops header parsing at the first blank line (start of description).

    Args:
        metadata_text: Raw METADATA file content as string

    Returns:
        Dictionary with parsed metadata fields
    """
    result: Dict[str, Union[str, List[str]]] = {}
    lines = metadata_text.strip().splitlines()
    header_lines = []
    description_lines = []
    in_description = False

    # Separate header and description parts
    for line in lines:
        if not in_description:
            if line.strip() == "":
                in_description = True
                continue
            header_lines.append(line)
        else:
            description_lines.append(line)

    # Parse metadata headers
    key = None
    for line in header_lines:
        # Continuation line (starts with space)
        if line.startswith(' ') and key:
            value = line.strip()
            if isinstance(result[key], list):
                result[key][-1] += ' ' + value
            elif isinstance(result[key], str):
                result[key] += ' ' + value
            continue

        # Match key-value
        match = re.match(r'^([A-Za-z0-9-]+):\s*(.*)$', line)
        if match:
            key, value = match.groups()
            key, value = key.strip(), value.strip()
            multi_fields = {
                "Classifier", "Requires-Dist", "Provides-Extra",
                "Project-URL", "License-File"
            }

            if key in result:
                if not isinstance(result[key], list):
                    result[key] = [result[key]]
                result[key].append(value)
            else:
                result[key] = [value] if key in multi_fields else value

    # Add description if present
    if description_lines:
        result["Description"] = "\n".join(description_lines).strip()

    return result


def extract_required_python_version(metadata: Dict[str, Any]) -> str:
    """
    Extract required Python version from metadata.
    
    Args:
        metadata: Parsed metadata dictionary
        
    Returns:
        Required Python version string, or empty string if not specified
    """
    classifiers = metadata.get("Classifier", [])
    if isinstance(classifiers, str):
        classifiers = [classifiers]
    
    # Look for specific versions first (like 3.8, 3.9)
    specific_versions = []
    for classifier in classifiers:
        if classifier.startswith("Programming Language :: Python ::"):
            version = classifier.split("::")[-1].strip()
            if version and version != "Implementation" and "." in version:
                specific_versions.append(version)
    
    # Return the first specific version found
    if specific_versions:
        return specific_versions[0]
    
    # Fallback to generic version (like "3")
    for classifier in classifiers:
        if classifier.startswith("Programming Language :: Python ::"):
            version = classifier.split("::")[-1].strip()
            if version and version != "Implementation":
                return version
    
    return ""


def extract_license_info(metadata: Dict[str, Any]) -> str:
    """
    Extract license information from metadata.
    
    Args:
        metadata: Parsed metadata dictionary
        
    Returns:
        License information string
    """
    license_info = metadata.get("License", "")
    if license_info:
        return license_info
    
    classifiers = metadata.get("Classifier", [])
    if isinstance(classifiers, str):
        classifiers = [classifiers]
    
    for classifier in classifiers:
        if classifier.startswith("License :: "):
            return classifier.split("::")[-1].strip()
    
    return ""


def extract_project_urls(metadata: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract project URLs from metadata.
    
    Args:
        metadata: Parsed metadata dictionary
        
    Returns:
        Dictionary mapping URL types to URLs
    """
    urls = {}
    project_urls = metadata.get("Project-URL", [])
    if isinstance(project_urls, str):
        project_urls = [project_urls]
    
    for url_entry in project_urls:
        if "," in url_entry:
            parts = url_entry.split(",", 1)
            if len(parts) == 2:
                url_type, url = parts
                urls[url_type.strip()] = url.strip()
    
    return urls

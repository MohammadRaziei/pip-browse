import re
from typing import Dict, List, Union

def parse_metadata(metadata_text: str) -> Dict[str, Union[str, List[str]]]:
    """
    Parse a Python package METADATA file into a structured dictionary.
    
    Handles repeated fields like 'Classifier', 'Requires-Dist', 'Project-URL', etc.
    """
    result: Dict[str, Union[str, List[str]]] = {}
    lines = metadata_text.strip().splitlines()
    key = None

    for line in lines:
        # Continuation line (starts with space)
        if line.startswith(' ') and key:
            result[key][-1] += ' ' + line.strip()
            continue

        # Match key-value pairs (standard metadata line)
        match = re.match(r'^([^:]+):\s*(.*)$', line)
        if match:
            key, value = match.groups()

            # Normalize capitalization (exact field names from spec)
            key = key.strip()

            # Store multiple values as a list
            if key in result:
                if isinstance(result[key], list):
                    result[key].append(value.strip())
                else:
                    result[key] = [result[key], value.strip()]
            else:
                # Some fields can repeat
                if key in (
                    "Classifier", "Requires-Dist", "Provides-Extra",
                    "Project-URL", "License-File"
                ):
                    result[key] = [value.strip()]
                else:
                    result[key] = value.strip()
        elif line.strip():  # description part (after blank line)
            result.setdefault("Description", "")
            result["Description"] += line + "\n"

    # Cleanup trailing newlines in description
    if "Description" in result:
        result["Description"] = result["Description"].strip()

    return result


"""Core classes for pip-browse package."""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any, Union
from urllib.parse import urljoin

from curl_cffi import requests as creq
from selectolax.parser import HTMLParser

from .metadata_parser import parse_metadata


@dataclass
class Dependency:
    """Represents a package dependency."""
    
    package: str
    condition: Optional[str] = None
    
    def __repr__(self) -> str:
        """String representation of the dependency."""
        return self.package + ("" if self.condition is None else f" {self.condition}")


@dataclass
class WheelFile:
    """Represents a wheel file with its properties."""
    
    url: str
    name: str
    raw_size: str
    
    @property
    def size(self) -> int:
        """Convert human-readable size to bytes."""
        return self._size_to_bytes(self.raw_size)
    
    @staticmethod
    def _size_to_bytes(size_str: str) -> int:
        """
        Convert human-readable size string to bytes.
        
        Args:
            size_str: Size string like '2.2 KiB', '951 bytes'
            
        Returns:
            Size in bytes as integer
        """
        size_str = size_str.strip().lower()
        
        if size_str.endswith("bytes") or size_str.endswith("byte"):
            return int(float(size_str.split()[0]))
        
        units = {
            "kib": 1024,
            "mib": 1024**2,
            "gib": 1024**3,
            "tib": 1024**4,
        }
        
        num_str, unit = size_str.split()
        num = float(num_str)
        multiplier = units.get(unit, 1)
        
        return int(num * multiplier)


@dataclass
class PackageTag:
    """Represents a package tag with its wheels."""
    
    tag: str
    wheels: List[Dict[str, str]]


@dataclass
class PackageInfo:
    """Represents comprehensive package information."""
    
    name: str
    tags: List[PackageTag]
    metadata: Dict[str, Union[str, List[str]]]
    dependencies: List[Dependency]
    optional_dependencies: Dict[str, List[Dependency]]
    wheel_files: List[WheelFile]
    
    @classmethod
    def from_package_name(cls, package_name: str, browser: 'PyPIBrowser') -> 'PackageInfo':
        """
        Create PackageInfo from package name using a PyPIBrowser instance.
        
        Args:
            package_name: Name of the package
            browser: PyPIBrowser instance to fetch data
            
        Returns:
            PackageInfo instance with all package data
        """
        tags = browser.get_package_tags(package_name)
        if not tags:
            raise ValueError(f"No package tags found for {package_name}")
        
        # Get metadata from first wheel
        first_wheel = tags[0].wheels[0]
        metadata = browser.get_package_metadata(first_wheel["url"])
        
        # Extract dependencies
        dependencies, optional_dependencies = browser.extract_dependencies(metadata)
        
        # Get wheel files
        wheel_files = browser.get_wheel_files(first_wheel["url"])
        
        return cls(
            name=package_name,
            tags=tags,
            metadata=metadata,
            dependencies=dependencies,
            optional_dependencies=optional_dependencies,
            wheel_files=wheel_files
        )


class PyPIBrowser:
    """Main class for browsing PyPI packages and analyzing dependencies."""
    
    def __init__(self, base_url: str = "https://pypi-browser.org/package/", timeout: int = 15):
        """
        Initialize the PyPI browser.
        
        Args:
            base_url: Base URL for PyPI browser
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/') + '/'
        self.timeout = timeout
    
    def fetch_content(self, url: str) -> Optional[str]:
        """
        Fetch content from a URL using TLS/HTTP2 + Chrome impersonation.
        
        Args:
            url: URL to fetch content from
            
        Returns:
            HTML content as string, or None if unsuccessful
        """
        try:
            resp = creq.get(
                url,
                timeout=self.timeout,
                allow_redirects=True,
                impersonate="chrome",
            )
            
            if resp.status_code != 200:
                return None
            
            ctype = resp.headers.get("content-type", "").lower()
            if "text/html" not in ctype:
                return None
            
            text = resp.text
            # Heuristic: avoid bot/challenge splash
            if "Client Challenge" in text or "/_fs-ch-" in text:
                return None
            return text
        except Exception:
            return None
    
    def get_package_tags(self, package_name: str) -> List[PackageTag]:
        """
        Get package tags and wheels from PyPI browser.
        
        Args:
            package_name: Name of the package
            
        Returns:
            List of PackageTag objects
        """
        url = f"{self.base_url}{package_name}/"
        content = self.fetch_content(url)
        
        if not content:
            return []
        
        tree = HTMLParser(content)
        cards = tree.css(".card")
        
        package_tags = []
        for card in cards:
            card_header = card.css_first(".card-header")
            if not card_header:
                continue
                
            tag = card_header.text().strip()
            wheels = []
            
            list_group = card.css_first(".list-group")
            if list_group:
                for a in list_group.css("a"):
                    span = a.css_first("span")
                    if span:
                        wheel_name = span.text().strip()
                        browser_url = a.attributes["href"]
                        # Convert browser URL to PyPI URL
                        pypi_url = self._convert_to_pypi_url(wheel_name)
                        wheels.append({
                            "name": wheel_name,
                            "browser_url": browser_url,
                            "pypi_url": pypi_url,
                        })
            
            package_tags.append(PackageTag(tag=tag, wheels=wheels))
        
        return package_tags
    
    def _convert_to_pypi_url(self, wheel_name: str) -> str:
        """
        Convert wheel name to PyPI repository URL.
        
        Args:
            wheel_name: Name of the wheel file
            
        Returns:
            PyPI repository URL
        """
        # Extract package name from wheel name
        # Format: package_name-version-py3-none-any.whl
        parts = wheel_name.split('-')
        if len(parts) >= 2:
            package_name = parts[0]
            version = parts[1]
            return f"https://pypi.org/project/{package_name}/{version}/"
        return f"https://pypi.org/project/{wheel_name}/"
    
    def get_wheel_files(self, wheel_url: str) -> List[WheelFile]:
        """
        Get wheel files from a wheel URL.
        
        Args:
            wheel_url: URL to the wheel page
            
        Returns:
            List of WheelFile objects
        """
        content = self.fetch_content(wheel_url)
        if not content:
            return []
        
        tree = HTMLParser(content)
        wheel_files = []
        
        for a in tree.css("a.list-group-item"):
            href = a.attributes.get("href", "")
            text = a.text().strip()
            
            # Parse the text to extract name and size
            parts = re.sub(r"\s{2,}", ";", text).split(";")
            if len(parts) >= 2:
                name = parts[0]
                raw_size = parts[1]
                full_url = urljoin(wheel_url, href)
                wheel_files.append(WheelFile(url=full_url, name=name, raw_size=raw_size))
        
        return wheel_files
    
    def get_package_metadata(self, wheel_url: str) -> Dict[str, Union[str, List[str]]]:
        """
        Get package metadata from a wheel URL.
        
        Args:
            wheel_url: URL to the wheel page
            
        Returns:
            Parsed metadata dictionary
        """
        # Extract dist-info from wheel name
        wheel_name = wheel_url.split('/')[-2] if wheel_url.endswith('/') else wheel_url.split('/')[-1]
        dist_info = "-".join(wheel_name.split("-")[:2]) + ".dist-info"
        metadata_url = f"{wheel_url}/{dist_info}/METADATA"
        
        content = self.fetch_content(metadata_url)
        if not content:
            return {}
        
        tree = HTMLParser(content)
        metadata_element = tree.css_first("pre")
        if not metadata_element:
            return {}
        
        metadata_str = metadata_element.text()
        return parse_metadata(metadata_str)
    
    def extract_dependencies(self, metadata: Dict[str, Any]) -> Tuple[List[Dependency], Dict[str, List[Dependency]]]:
        """
        Extract dependencies from package metadata.
        
        Args:
            metadata: Parsed metadata dictionary
            
        Returns:
            Tuple of (dependencies, optional_dependencies)
        """
        dependencies: List[Dependency] = []
        optional_dependencies: Dict[str, List[Dependency]] = {}
        
        # Match: semicolon + optional spaces + extra == "something"
        _EXTRA_RE = re.compile(r';\s*extra\s*==\s*[\'"]([^\'"]+)[\'"]', re.IGNORECASE)
        
        requires_dist = metadata.get("Requires-Dist", [])
        if isinstance(requires_dist, str):
            requires_dist = [requires_dist]
        
        for req in requires_dist:
            req = req.strip()
            if not req:
                continue
            
            # Detect extras (and remove the entire "; extra == ..." part)
            extras = _EXTRA_RE.findall(req)
            req_clean = _EXTRA_RE.sub("", req).strip()
            
            # Split package name and condition
            match = re.match(r"^([A-Za-z0-9_.\-]+)\s*(.*)$", req_clean)
            if not match:
                continue
            
            pkg, rest = match.groups()
            condition = rest.strip() or None
            
            dep = Dependency(pkg, condition)
            
            if extras:
                for extra in extras:
                    optional_dependencies.setdefault(extra, []).append(dep)
            else:
                dependencies.append(dep)
        
        return dependencies, optional_dependencies
    
    def get_package_info(self, package_name: str) -> PackageInfo:
        """
        Get comprehensive package information.
        
        Args:
            package_name: Name of the package
            
        Returns:
            PackageInfo object with all package data
        """
        return PackageInfo.from_package_name(package_name, self)

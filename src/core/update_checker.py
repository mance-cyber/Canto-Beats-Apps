"""
Update Checker for Canto-beats
Checks for updates from GitHub Releases.
"""

import requests
import webbrowser
from dataclasses import dataclass
from typing import Optional, Tuple
from packaging import version as pkg_version

from utils.logger import setup_logger

logger = setup_logger()

# GitHub repository info
GITHUB_OWNER = "mance-cyber"
GITHUB_REPO = "Canto-Beats-Apps"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

# Current app version
CURRENT_VERSION = "1.0.0"


@dataclass
class UpdateInfo:
    """Update information from GitHub."""
    version: str
    download_url: str
    changelog: str
    release_date: str
    html_url: str  # GitHub release page
    required: bool = False


class UpdateChecker:
    """Check for application updates from GitHub Releases."""
    
    def __init__(self):
        self.current_version = CURRENT_VERSION
        self.api_url = GITHUB_API_URL
    
    def check_for_update(self) -> Tuple[bool, Optional[UpdateInfo]]:
        """
        Check if a new version is available on GitHub.
        
        Returns:
            Tuple of (update_available, update_info)
        """
        try:
            logger.info(f"Checking for updates at GitHub...")
            
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Canto-beats-Updater"
            }
            
            response = requests.get(
                self.api_url,
                headers=headers,
                timeout=10,
                verify=True
            )
            
            if response.status_code == 404:
                logger.info("No releases found on GitHub")
                return False, None
            
            if response.status_code != 200:
                logger.warning(f"Update check failed: HTTP {response.status_code}")
                return False, None
            
            data = response.json()
            
            # Parse version from tag (remove 'v' prefix if present)
            tag_name = data.get("tag_name", "0.0.0")
            server_version = tag_name.lstrip("v")
            
            # Find EXE download URL from assets
            download_url = ""
            for asset in data.get("assets", []):
                if asset.get("name", "").endswith(".exe"):
                    download_url = asset.get("browser_download_url", "")
                    break
            
            # If no EXE found, use release page
            if not download_url:
                download_url = data.get("html_url", "")
            
            # Compare versions
            if pkg_version.parse(server_version) > pkg_version.parse(self.current_version):
                update_info = UpdateInfo(
                    version=server_version,
                    download_url=download_url,
                    changelog=data.get("body", ""),
                    release_date=data.get("published_at", "")[:10],  # YYYY-MM-DD
                    html_url=data.get("html_url", "")
                )
                logger.info(f"New version available: {server_version}")
                return True, update_info
            else:
                logger.info(f"No update available. Current: {self.current_version}, Latest: {server_version}")
                return False, None
                
        except requests.Timeout:
            logger.warning("Update check timed out")
            return False, None
        except requests.RequestException as e:
            logger.warning(f"Update check failed: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Update check error: {e}")
            return False, None
    
    def open_download_page(self, url: str):
        """Open download URL in browser."""
        try:
            webbrowser.open(url)
            logger.info(f"Opened download page: {url}")
        except Exception as e:
            logger.error(f"Failed to open download page: {e}")


def check_update_sync() -> Tuple[bool, Optional[UpdateInfo]]:
    """
    Synchronous update check helper.
    
    Returns:
        Tuple of (update_available, update_info)
    """
    checker = UpdateChecker()
    return checker.check_for_update()

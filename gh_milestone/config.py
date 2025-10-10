"""
Configuration module for GitHub Milestone CLI.
"""

import os
import subprocess
import re
from pathlib import Path
from typing import Optional


class Config:
    """Configuration constants and settings."""
    
    DEFAULT_SCHEMA_FILE = "schema.json"
    DEFAULT_HOST = "localhost"
    DEFAULT_MCP_PORT = 8080
    DEFAULT_HTTP_SERVER_PORT = 8000
    DEFAULT_LIST_FORMAT = "tree"
    DEFAULT_STATUS_FORMAT = "summary"
    DEFAULT_MCP_TRANSPORT = "stdio"
    DEFAULT_TASK_LABEL = "task"
    DEFAULT_MAIN_TRACKING_LABELS = ["epic", "roadmap"]
    DEFAULT_TASK_PREFIX = "Task: "
    DEFAULT_ROADMAP_FILE = "roadmap.json"
    
    @staticmethod
    def get_repo_name(explicit_repo: Optional[str] = None, roadmap_file: Optional[str] = None) -> str:
        """
        Get repository name with auto-detection.
        
        Priority order:
        1. Explicit repo parameter (from --repo option)
        2. GH_REPO environment variable
        3. Auto-detect from roadmap file's git directory
        
        Args:
            explicit_repo: Explicit repository name from command line
            roadmap_file: Path to roadmap file to use for git directory detection
            
        Returns:
            Repository name in 'owner/repo' format or empty string if not found
        """
        # Priority 1: Explicit repo parameter
        if explicit_repo:
            return explicit_repo
            
        # Priority 2: GH_REPO environment variable
        env_repo = os.environ.get("GH_REPO", "")
        if env_repo:
            return env_repo
            
        # Priority 3: Auto-detect from roadmap file's git directory
        return Config._detect_repo_from_git(roadmap_file)
    
    @staticmethod
    def _detect_repo_from_git(roadmap_file: Optional[str] = None) -> str:
        """
        Auto-detect repository name from roadmap file's git directory.
        
        Args:
            roadmap_file: Path to roadmap file to determine git directory
            
        Returns:
            Repository name in 'owner/repo' format or empty string if not found
        """
        try:
            # Determine the working directory for git command
            working_dir = None
            if roadmap_file:
                roadmap_path = Path(roadmap_file)
                if roadmap_path.is_absolute():
                    working_dir = roadmap_path.parent
                else:
                    # If roadmap_file is relative, use current working directory
                    working_dir = Path.cwd()
            
            # Get the remote origin URL from the roadmap file's directory
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
                check=False,
                cwd=working_dir
            )
            
            if result.returncode != 0 or not result.stdout:
                return ""  # No remote origin URL found
            
            url = result.stdout.strip()
            
            # Only process GitHub URLs
            if "github.com" not in url:
                return ""  # Not a GitHub URL
            
            # Remove .git suffix if present
            if url.endswith(".git"):
                url = url[:-4]
            
            # Handle different URL formats
            if url.startswith("https://"):
                # HTTPS format: https://github.com/owner/repo
                parts = url.split("/")
                if len(parts) >= 4:
                    return f"{parts[-2]}/{parts[-1]}"
            elif "@" in url and ":" in url:
                # SSH format: git@github.com:owner/repo
                repo_part = url.split(":")[-1]
                if repo_part:
                    return repo_part
            
            return ""  # Not a recognized GitHub URL format
            
        except (subprocess.SubprocessError, FileNotFoundError):
            return ""  # Git command not available or other error
    

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import os
import subprocess

# Add the gh_milestone directory to the path so we can import from gh_milestone
sys.path.insert(0, str(Path(__file__).parent.parent / "gh_milestone"))
from gh_milestone.config import Config
from tests.test_base import BaseTestCase

class TestConfig(BaseTestCase):
    """Test cases for the Config class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        super().setUp()

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        pass

    def test_default_schema_file_constant(self):
        """Test that DEFAULT_SCHEMA_FILE constant exists and has correct value."""
        self.assertEqual(Config.DEFAULT_SCHEMA_FILE, "schema.json")

    @patch.dict(os.environ, {"GH_REPO": "test_owner/test_repo"})
    def test_get_repo_name_with_environment_variable(self):
        """Test get_repo_name when GH_REPO environment variable is set."""
        repo_name = Config.get_repo_name()
        self.assertEqual(repo_name, "test_owner/test_repo")

    @patch.dict(os.environ, {}, clear=True)
    @patch('gh_milestone.config.Config._detect_repo_from_git', return_value="")
    def test_get_repo_name_without_environment_variable(self, mock_detect_repo):
        """Test get_repo_name when GH_REPO environment variable is not set."""
        repo_name = Config.get_repo_name()
        self.assertEqual(repo_name, "")

    def test_config_can_be_instantiated(self):
        """Test that Config can be instantiated."""
        # Config should be instantiable
        config_instance = Config()
        self.assertIsInstance(config_instance, Config)

    @patch('subprocess.run')
    def test_detect_repo_from_git_with_github_remote(self, mock_subprocess):
        """Test _detect_repo_from_git when in a git repository with GitHub remote."""
        # Mock subprocess to return a GitHub remote URL
        mock_result = MagicMock()
        mock_result.stdout = "https://github.com/owner/repo.git\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        repo_name = Config._detect_repo_from_git()
        self.assertEqual(repo_name, "owner/repo")

    @patch('subprocess.run')
    def test_detect_repo_from_git_with_ssh_github_remote(self, mock_subprocess):
        """Test _detect_repo_from_git when in a git repository with SSH GitHub remote."""
        # Mock subprocess to return an SSH GitHub remote URL
        mock_result = MagicMock()
        mock_result.stdout = "git@github.com:owner/repo.git\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        repo_name = Config._detect_repo_from_git()
        self.assertEqual(repo_name, "owner/repo")

    @patch('subprocess.run')
    def test_detect_repo_from_git_with_non_github_remote(self, mock_subprocess):
        """Test _detect_repo_from_git when in a git repository with non-GitHub remote."""
        # Mock subprocess to return a non-GitHub remote URL
        mock_result = MagicMock()
        mock_result.stdout = "https://gitlab.com/owner/repo.git\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        repo_name = Config._detect_repo_from_git()
        self.assertEqual(repo_name, "")

    @patch('subprocess.run')
    def test_detect_repo_from_git_not_in_repo(self, mock_subprocess):
        """Test _detect_repo_from_git when not in a git repository."""
        # Mock subprocess to simulate not being in a git repository
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "fatal: not a git repository (or any of the parent directories): .git\n"
        mock_result.returncode = 128
        mock_subprocess.return_value = mock_result
        
        repo_name = Config._detect_repo_from_git()
        self.assertEqual(repo_name, "")

    @patch('subprocess.run')
    def test_detect_repo_from_git_command_fails(self, mock_subprocess):
        """Test _detect_repo_from_git when git command fails."""
        # Mock subprocess to simulate a git command failure
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "git: command not found\n"
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result
        
        repo_name = Config._detect_repo_from_git()
        self.assertEqual(repo_name, "")

    @patch.dict(os.environ, {"GH_REPO": "env_owner/env_repo"}, clear=True)
    @patch('subprocess.run')
    def test_get_repo_name_priority_explicit_repo(self, mock_subprocess):
        """Test get_repo_name priority: explicit repo > environment > auto-detection."""
        # This test should use explicit repo parameter regardless of env or git
        mock_result = MagicMock()
        mock_result.stdout = "https://github.com/git_owner/git_repo.git\n"
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        repo_name = Config.get_repo_name("explicit_owner/explicit_repo")
        self.assertEqual(repo_name, "explicit_owner/explicit_repo")

    @patch.dict(os.environ, {"GH_REPO": "env_owner/env_repo"}, clear=True)
    @patch('subprocess.run')
    def test_get_repo_name_priority_environment_variable(self, mock_subprocess):
        """Test get_repo_name priority: environment > auto-detection."""
        # This test should use environment variable, not git detection
        mock_result = MagicMock()
        mock_result.stdout = "https://github.com/git_owner/git_repo.git\n"
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        repo_name = Config.get_repo_name()
        self.assertEqual(repo_name, "env_owner/env_repo")

    @patch.dict(os.environ, {}, clear=True)
    @patch('subprocess.run')
    def test_get_repo_name_with_auto_detection(self, mock_subprocess):
        """Test get_repo_name with auto-detection from git directory."""
        # This test should use git detection
        mock_result = MagicMock()
        mock_result.stdout = "https://github.com/detected_owner/detected_repo.git\n"
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        repo_name = Config.get_repo_name()
        self.assertEqual(repo_name, "detected_owner/detected_repo")

    @patch.dict(os.environ, {}, clear=True)
    @patch('subprocess.run')
    def test_get_repo_name_no_detection_available(self, mock_subprocess):
        """Test get_repo_name when no repository can be detected."""
        # Mock subprocess to simulate failure in git detection
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "fatal: not a git repository\n"
        mock_result.returncode = 128
        mock_subprocess.return_value = mock_result
        
        repo_name = Config.get_repo_name()
        self.assertEqual(repo_name, "")

if __name__ == '__main__':
    unittest.main()

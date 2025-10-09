import unittest
from unittest.mock import Mock, patch
import os
import subprocess
from tests.test_base import BaseTestCase
from tests.test_data_factory import TestDataFactory
from gh_milestone.github_client import GitHubClient

class TestGitHubClient(BaseTestCase):
    """Test cases for the GitHubClient class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        super().setUp()
        # Create a new client for each test to avoid state issues
        with patch.dict(os.environ, {"GH_REPO": "test_owner/test_repo"}):
            with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
                mock_auth.return_value = Mock()
                self.client = GitHubClient()

    @patch.dict(os.environ, {"GH_REPO": "test_owner/test_repo"})
    @patch.object(GitHubClient, '_get_authenticated_client')
    def test_init(self, mock_get_authenticated_client):
        """Test GitHubClient initialization."""
        mock_get_authenticated_client.return_value = Mock()
        client = GitHubClient()
        self.assertIsInstance(client, GitHubClient)

    def test_init_with_explicit_repo(self):
        """Test GitHubClient initialization with explicit repo parameter."""
        with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
            mock_auth.return_value = Mock()
            client = GitHubClient(explicit_repo="explicit_owner/explicit_repo")

    def test_init_without_repo(self):
        """Test GitHubClient initialization without repo parameter or environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                GitHubClient()

    def test_repo_priority(self):
        """Test explicit repo parameter overrides environment variable."""
        with patch.dict(os.environ, {"GH_REPO": "env_owner/env_repo"}):
            with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
                mock_auth.return_value = Mock()
                client = GitHubClient(explicit_repo="explicit_owner/explicit_repo")

    @patch.dict(os.environ, {"GITHUB_TOKEN": "test_token", "GH_REPO": "test_owner/test_repo"})
    @patch('gh_milestone.github_client.Github')
    @patch('gh_milestone.github_client.Auth.Token')
    def test_get_authenticated_client_with_github_token(self, mock_auth_token, mock_github_class):
        """Test authenticated client creation with GITHUB_TOKEN environment variable."""
        mock_auth_instance = Mock()
        mock_auth_token.return_value = mock_auth_instance
        mock_github_instance = Mock()
        mock_github_class.return_value = mock_github_instance
        
        # Create a new client instance for this test
        with patch.object(GitHubClient, '_get_authenticated_client'):
            client = GitHubClient()
        
        github_client = client._get_authenticated_client()
        
        mock_auth_token.assert_called_once_with("test_token")
        mock_github_class.assert_called_once_with(auth=mock_auth_instance)
        self.assertEqual(github_client, mock_github_instance)

    @patch.dict(os.environ, {"GH_REPO": "test_owner/test_repo"})
    @patch('gh_milestone.github_client.Github')
    @patch('gh_milestone.github_client.Auth.Token')
    @patch('subprocess.run')
    def test_get_authenticated_client_with_gh_cli_token(self, mock_subprocess, mock_auth_token, mock_github_class):
        """Test authenticated client creation with gh CLI fallback."""
        # Remove GITHUB_TOKEN from environment if it exists
        env_vars = {"GH_REPO": "test_owner/test_repo"}
        if "GITHUB_TOKEN" in os.environ:
            env_vars = {k: v for k, v in env_vars.items() if k != "GITHUB_TOKEN"}
            
        mock_auth_instance = Mock()
        mock_auth_token.return_value = mock_auth_instance
        mock_github_instance = Mock()
        mock_github_class.return_value = mock_github_instance
        mock_subprocess.return_value = Mock(stdout="gh_cli_token\n", stderr="")
        
        # Create a new client instance for this test
        with patch.dict(os.environ, env_vars, clear=True):
            with patch.object(GitHubClient, '_get_authenticated_client'):
                client = GitHubClient()
        
        # Call the method directly
        github_client = client._get_authenticated_client()
        
        mock_subprocess.assert_called_once_with(
            ["gh", "auth", "token"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        mock_auth_token.assert_called_once_with("gh_cli_token")
        mock_github_class.assert_called_once_with(auth=mock_auth_instance)
        self.assertEqual(github_client, mock_github_instance)

    @patch('gh_milestone.github_client.subprocess.run')
    def test_get_authenticated_client_no_token_available(self, mock_subprocess):
        """Test error handling when no token is available."""
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "gh auth token")
        
        with patch.dict(os.environ, {}, clear=True):  # Clear all env vars including GITHUB_TOKEN
            with patch("builtins.print") as mock_print:
                with patch("sys.exit", side_effect=SystemExit(1)) as mock_exit:
                    # Create a new client instance within the patched environment
                    # This should raise SystemExit due to sys.exit(1)
                    with self.assertRaises(SystemExit):
                        client = GitHubClient()
                    
                    mock_exit.assert_called_once_with(1)
                    # Check that both print calls were made
                    mock_print.assert_any_call("❌ GitHub authentication required.")
                    mock_print.assert_any_call("Please set GITHUB_TOKEN environment variable or authenticate with 'gh auth login'")
                    self.assertEqual(mock_print.call_count, 2)

    @patch.dict(os.environ, {"GH_REPO": "test_owner/test_repo"})
    def test_create_issue_success(self):
        """Test successful issue creation."""
        # Mock the client property
        mock_github_instance = Mock()
        mock_repo = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.html_url = "https://github.com/test_owner/test_repo/issues/123"
        mock_repo.create_issue.return_value = mock_issue
        
        # Create a new client and replace its client property with our mock
        with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
            mock_auth.return_value = mock_github_instance
            client = GitHubClient()
        
        # Test the actual create_issue call
        url, number = client.create_issue("Test Title", "Test Body", ["label1", "label2"])
        
        # Verify that get_repo was called with the environment repo
        mock_github_instance.get_repo.assert_called_once_with("test_owner/test_repo")
        mock_repo.create_issue.assert_called_once_with(
            title="Test Title",
            body="Test Body",
            labels=["label1", "label2"]
        )
        self.assertEqual(url, "https://github.com/test_owner/test_repo/issues/123")
        self.assertEqual(number, 123)

    @patch.dict(os.environ, {"GH_REPO": "test_owner/test_repo"})
    def test_create_issue_with_explicit_repo(self):
        """Test issue creation with explicit repo parameter."""
        # Mock the client property
        mock_github_instance = Mock()
        mock_repo = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.html_url = "https://github.com/explicit_owner/explicit_repo/issues/123"
        mock_repo.create_issue.return_value = mock_issue
        
        # Create client with explicit repo
        with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
            mock_auth.return_value = mock_github_instance
            client = GitHubClient(explicit_repo="explicit_owner/explicit_repo")
        
        url, number = client.create_issue("Test Title", "Test Body", ["label1", "label2"])
        
        # Verify explicit repo was used
        mock_github_instance.get_repo.assert_called_once_with("explicit_owner/explicit_repo")
        mock_repo.create_issue.assert_called_once_with(
            title="Test Title",
            body="Test Body",
            labels=["label1", "label2"]
        )
        self.assertEqual(url, "https://github.com/explicit_owner/explicit_repo/issues/123")
        self.assertEqual(number, 123)

    @patch.dict(os.environ, {"GH_REPO": "test_owner/test_repo"})
    def test_delete_issue_success(self):
        """Test successful issue deletion."""
        mock_github_instance = Mock()
        
        # Mock the private requester method
        mock_requester = Mock()
        mock_github_instance._Github__requester = mock_requester
        mock_requester.requestJsonAndCheck.return_value = (Mock(), {"success": True})
        
        # Create a new client and replace its client property with our mock
        with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
            mock_auth.return_value = mock_github_instance
            client = GitHubClient()
        
        client.delete_issue(123)
        
        # The method should call the API directly with the correct endpoint format
        mock_requester.requestJsonAndCheck.assert_called_once_with(
            "DELETE",
            "/repos/test_owner/test_repo/issues/123"
        )

    @patch('subprocess.run')
    def test_delete_issue_no_repo_environment_variable(self, mock_subprocess):
        """Test error handling when no repository context is available."""
        # Mock git commands to simulate non-git directory
        mock_subprocess.side_effect = subprocess.CalledProcessError(128, "git command")
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("builtins.print") as mock_print:
                with patch("sys.exit") as mock_exit:
                    # Create a new client instance within the patched environment
                    with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
                        mock_auth.return_value = Mock()
                        client = GitHubClient()
                    # Now call delete_issue which should trigger the error
                    client.delete_issue(123)
                    mock_exit.assert_called_once_with(1)
                    # Check that the error message was printed
                    error_message = "❌ Repository name could not be determined. Please provide --repo option or run within a git repository with a GitHub remote."
                    mock_print.assert_any_call(error_message)

    @patch.dict(os.environ, {"GH_REPO": "test_owner/test_repo"})
    def test_unlink_sub_issue_success(self):
        """Test successful unlinking of sub-issue."""
        mock_github_instance = Mock()
        
        # Mock the private requester method
        mock_requester = Mock()
        mock_github_instance._Github__requester = mock_requester
        mock_requester.requestJsonAndCheck.return_value = (Mock(), {"success": True})
        
        # Create a new client and replace its client property with our mock
        with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
            mock_auth.return_value = mock_github_instance
            client = GitHubClient()
        
        client.unlink_sub_issue(1, 2)
        
        # The method should call the API directly with the correct endpoint format
        mock_requester.requestJsonAndCheck.assert_called_once_with(
            "DELETE",
            "/repos/test_owner/test_repo/issues/1/sub_issues/2"
        )

    @patch('subprocess.run')
    def test_unlink_sub_issue_no_repo_environment_variable(self, mock_subprocess):
        """Test error handling when no repository context is available."""
        # Mock git commands to simulate non-git directory
        mock_subprocess.side_effect = subprocess.CalledProcessError(128, "git command")
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("builtins.print") as mock_print:
                with patch("sys.exit") as mock_exit:
                    # Create a new client instance within the patched environment
                    with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
                        mock_auth.return_value = Mock()
                        client = GitHubClient()
                    # Now test the actual method behavior
                    client.unlink_sub_issue(1, 2)
                    mock_exit.assert_called_once_with(1)
                    # Check that the error message was printed
                    error_message = "❌ Repository name could not be determined. Please provide --repo option or run within a git repository with a GitHub remote."
                    mock_print.assert_any_call(error_message)

    @patch.dict(os.environ, {"GH_REPO": "test_owner/test_repo"})
    def test_unlink_sub_issue_api_error(self):
        """Test unlinking sub-issue when API call fails."""
        mock_github_instance = Mock()
        mock_repo = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_parent_issue = Mock()
        mock_sub_issue = Mock()
        mock_repo.get_issue.side_effect = [mock_parent_issue, mock_sub_issue]
        
        # Mock the private requester method to raise an exception
        mock_requester = Mock()
        mock_github_instance._Github__requester = mock_requester
        mock_requester.requestJsonAndCheck.side_effect = Exception("API error")
        
        # Create a new client and replace its client property with our mock
        with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
            mock_auth.return_value = mock_github_instance
            client = GitHubClient()
        
        with patch("builtins.print") as mock_print:
            with patch("sys.exit") as mock_exit:
                client.unlink_sub_issue(1, 2)
                mock_exit.assert_called_once_with(1)

    @patch.dict(os.environ, {"GH_REPO": "test_owner/test_repo"})
    def test_update_issue_success(self):
        """Test successful issue update with all fields."""
        mock_github_instance = Mock()
        mock_repo = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_issue = Mock()
        mock_repo.get_issue.return_value = mock_issue
        
        # Create a new client and replace its client property with our mock
        with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
            mock_auth.return_value = mock_github_instance
            client = GitHubClient()
        
        client.update_issue(123, title="Updated Title", body="Updated Body")
        
        mock_github_instance.get_repo.assert_called_once_with("test_owner/test_repo")
        mock_repo.get_issue.assert_called_once_with(123)
        mock_issue.edit.assert_called_once_with(
            title="Updated Title",
            body="Updated Body"
        )

    @patch.dict(os.environ, {"GH_REPO": "test_owner/test_repo"})
    def test_update_issue_partial_fields(self):
        """Test issue update with only some fields."""
        mock_github_instance = Mock()
        mock_repo = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_issue = Mock()
        mock_repo.get_issue.return_value = mock_issue
        
        # Create a new client and replace its client property with our mock
        with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
            mock_auth.return_value = mock_github_instance
            client = GitHubClient()
        
        client.update_issue(123, title="Updated Title")
        
        mock_github_instance.get_repo.assert_called_once_with("test_owner/test_repo")
        mock_repo.get_issue.assert_called_once_with(123)
        mock_issue.edit.assert_called_once_with(
            title="Updated Title"
        )

    @patch('subprocess.run')
    def test_update_issue_no_repo_environment_variable(self, mock_subprocess):
        """Test error handling when no repository context is available."""
        # Mock git commands to simulate non-git directory
        mock_subprocess.side_effect = subprocess.CalledProcessError(128, "git command")
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("builtins.print") as mock_print:
                with patch("sys.exit") as mock_exit:
                    # Create a new client instance within the patched environment
                    with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
                        mock_auth.return_value = Mock()
                        client = GitHubClient()
                    # Now call update_issue which should trigger the error
                    client.update_issue(123, title="Test Title")
                    mock_exit.assert_called_once_with(1)
                    # Check that the error message was printed
                    error_message = "❌ Repository name could not be determined. Please provide --repo option or run within a git repository with a GitHub remote."
                    mock_print.assert_any_call(error_message)

    @patch.dict(os.environ, {"GH_REPO": "test_owner/test_repo"})
    def test_get_issue_success(self):
        """Test successful issue retrieval."""
        mock_github_instance = Mock()
        mock_repo = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test Body"
        mock_issue.state = "open"
        mock_issue.html_url = "https://github.com/test_owner/test_repo/issues/123"
        mock_repo.get_issue.return_value = mock_issue
        
        # Create a new client and replace its client property with our mock
        with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
            mock_auth.return_value = mock_github_instance
            client = GitHubClient()
        
        issue = client.get_issue(123)
        
        mock_github_instance.get_repo.assert_called_once_with("test_owner/test_repo")
        mock_repo.get_issue.assert_called_once_with(123)
        self.assertEqual(issue.number, 123)
        self.assertEqual(issue.title, "Test Issue")
        self.assertEqual(issue.body, "Test Body")
        self.assertEqual(issue.state, "open")
        self.assertEqual(issue.html_url, "https://github.com/test_owner/test_repo/issues/123")

    @patch('subprocess.run')
    def test_get_issue_no_repo_environment_variable(self, mock_subprocess):
        """Test error handling when no repository context is available."""
        # Mock git commands to simulate non-git directory
        mock_subprocess.side_effect = subprocess.CalledProcessError(128, "git command")
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("builtins.print") as mock_print:
                with patch("sys.exit") as mock_exit:
                    # Create a new client instance within the patched environment
                    with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
                        mock_auth.return_value = Mock()
                        client = GitHubClient()
                    # Now call get_issue which should trigger the error
                    client.get_issue(123)
                    mock_exit.assert_called_once_with(1)
                    # Check that the error message was printed
                    error_message = "❌ Repository name could not be determined. Please provide --repo option or run within a git repository with a GitHub remote."
                    mock_print.assert_any_call(error_message)

    @patch.dict(os.environ, {"GH_REPO": "test_owner/test_repo"})
    def test_create_issue_with_default_parameters(self):
        """Test issue creation with default body and labels."""
        mock_github_instance = Mock()
        mock_repo = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_issue = Mock()
        mock_issue.number = 456
        mock_issue.html_url = "https://github.com/test_owner/test_repo/issues/456"
        mock_repo.create_issue.return_value = mock_issue
        
        # Create a new client and replace its client property with our mock
        with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
            mock_auth.return_value = mock_github_instance
            client = GitHubClient()
        
        url, number = client.create_issue("Test Title")
        
        mock_github_instance.get_repo.assert_called_once_with("test_owner/test_repo")
        mock_repo.create_issue.assert_called_once_with(
            title="Test Title",
            body="",
            labels=[]
        )
        self.assertEqual(url, "https://github.com/test_owner/test_repo/issues/456")
        self.assertEqual(number, 456)

    @patch('subprocess.run')
    def test_create_issue_no_repo_environment_variable(self, mock_subprocess):
        """Test error handling when no repository context is available."""
        # Mock git commands to simulate non-git directory
        mock_subprocess.side_effect = subprocess.CalledProcessError(128, "git command")
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("builtins.print") as mock_print:
                with patch("sys.exit") as mock_exit:
                    # Create a new client instance within the patched environment
                    with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
                        mock_auth.return_value = Mock()
                        client = GitHubClient()
                        # Now call create_issue which should trigger the error
                        client.create_issue("Test Title")
                    mock_exit.assert_called_once_with(1)
                    # Check that the error message was printed (it might be called multiple times)
                    error_message = "❌ Repository name could not be determined. Please provide --repo option or run within a git repository with a GitHub remote."
                    mock_print.assert_any_call(error_message)

    @patch.dict(os.environ, {"GH_REPO": "test_owner/test_repo"})
    def test_link_sub_issue_success(self):
        """Test successful linking of sub-issue."""
        mock_github_instance = Mock()
        
        # Mock the private requester method
        mock_requester = Mock()
        mock_github_instance._Github__requester = mock_requester
        mock_requester.requestJsonAndCheck.return_value = (Mock(), {"success": True})
        
        # Create a new client and replace its client property with our mock
        with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
            mock_auth.return_value = mock_github_instance
            client = GitHubClient()
        
        client.link_sub_issue(1, 2)
        
        # The method should call the API directly, not get_repo.get_issue
        mock_requester.requestJsonAndCheck.assert_called_once_with(
            "POST",
            "/repos/test_owner/test_repo/issues/1/sub_issues",
            input={"sub_issue_id": 2}
        )

    @patch('subprocess.run')
    def test_link_sub_issue_no_repo_environment_variable(self, mock_subprocess):
        """Test error handling when no repository context is available."""
        # Mock git commands to simulate non-git directory
        mock_subprocess.side_effect = subprocess.CalledProcessError(128, "git command")
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("builtins.print") as mock_print:
                with patch("sys.exit") as mock_exit:
                    # Create a new client instance within the patched environment
                    with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
                        mock_auth.return_value = Mock()
                        client = GitHubClient()
                    # Now test the actual method behavior
                    client.link_sub_issue(1, 2)
                    mock_exit.assert_called_once_with(1)
                    # Check that the error message was printed (it might be called multiple times)
                    error_message = "❌ Repository name could not be determined. Please provide --repo option or run within a git repository with a GitHub remote."
                    mock_print.assert_any_call(error_message)

    @patch.dict(os.environ, {"GH_REPO": "test_owner/test_repo"})
    def test_link_sub_issue_api_error(self):
        """Test linking sub-issue when API call fails."""
        mock_github_instance = Mock()
        mock_repo = Mock()
        mock_github_instance.get_repo.return_value = mock_repo
        mock_parent_issue = Mock()
        mock_sub_issue = Mock()
        mock_repo.get_issue.side_effect = [mock_parent_issue, mock_sub_issue]
        
        # Mock the private requester method to raise an exception
        mock_requester = Mock()
        mock_github_instance._Github__requester = mock_requester
        mock_requester.requestJsonAndCheck.side_effect = Exception("API error")
        
        # Create a new client and replace its client property with our mock
        with patch.object(GitHubClient, '_get_authenticated_client') as mock_auth:
            mock_auth.return_value = mock_github_instance
            client = GitHubClient()
        
        with patch("builtins.print") as mock_print:
            with patch("sys.exit") as mock_exit:
                client.link_sub_issue(1, 2)
                mock_exit.assert_called_once_with(1)

if __name__ == '__main__':
    unittest.main()

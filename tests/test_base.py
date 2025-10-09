"""Base test case class with common setup utilities."""

import unittest
from unittest.mock import Mock, patch
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import gh_milestone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gh_milestone.cli import CLI


class BaseTestCase(unittest.TestCase):
    """Base class with common test setup utilities."""
    
    def setUp(self):
        """Set up common test fixtures."""
        self.cli = CLI()
        self.mock_args = self._create_mock_args()
        self.roadmap_data = self._create_roadmap_data()
        self.setup_common_mocks()
    
    def _create_mock_args(self, **kwargs):
        """Create standardized mock arguments."""
        defaults = {
            'command': 'create',
            'roadmap_file': 'roadmap.json',
            'verbose': False,
            'schema': 'schema.json'
        }
        defaults.update(kwargs)
        return Mock(**defaults)
    
    def _create_roadmap_data(self, **kwargs):
        """Create standardized roadmap data."""
        defaults = {
            'project': {'name': 'Test Project'},
            'milestones': [],
            'mainTrackingIssue': {'title': 'Main'}
        }
        defaults.update(kwargs)
        return defaults
    
    def setup_common_mocks(self):
        """Set up commonly used mocks."""
        self.mock_github_client = Mock()
        self.mock_state_manager = Mock()
        self.mock_issue_creator = Mock()
        
        # Patch imports
        self.patcher_github = patch('gh_milestone.github_client.GitHubClient')
        self.patcher_state = patch('gh_milestone.state_manager.StateManager')
        self.patcher_issue = patch('gh_milestone.issue_creator.IssueCreator')
        
        self.mock_github_client_class = self.patcher_github.start()
        self.mock_state_manager_class = self.patcher_state.start()
        self.mock_issue_creator_class = self.patcher_issue.start()
        
        self.mock_github_client_class.return_value = self.mock_github_client
        self.mock_state_manager_class.return_value = self.mock_state_manager
        self.mock_issue_creator_class.return_value = self.mock_issue_creator
        
        self.addCleanup(self.patcher_github.stop)
        self.addCleanup(self.patcher_state.stop)
        self.addCleanup(self.patcher_issue.stop)
    
    def setup_print_and_exit_mocks(self):
        """Set up print and exit mocks."""
        self.patcher_print = patch('builtins.print')
        self.patcher_exit = patch('sys.exit')
        
        self.mock_print = self.patcher_print.start()
        self.mock_exit = self.patcher_exit.start()
        
        self.addCleanup(self.patcher_print.stop)
        self.addCleanup(self.patcher_exit.stop)
    
    def setup_schema_validator_mocks(self):
        """Set up schema validator mocks."""
        self.patcher_load_json = patch('gh_milestone.schema_validator.SchemaValidator.load_json_file')
        self.patcher_validate_schema = patch('gh_milestone.schema_validator.SchemaValidator.validate_schema')
        
        self.mock_load_json = self.patcher_load_json.start()
        self.mock_validate_schema = self.patcher_validate_schema.start()
        
        self.addCleanup(self.patcher_load_json.stop)
        self.addCleanup(self.patcher_validate_schema.stop)
    
    def setup_path_exists_mocks(self, roadmap_exists=True, schema_exists=True):
        """Set up path existence mocks."""
        self.patcher_path_exists = patch('gh_milestone.cli.Path')
        
        self.mock_path = self.patcher_path_exists.start()
        self.mock_path.return_value.exists.return_value = roadmap_exists
        
        # Create a mock for schema file path
        self.mock_schema_path = Mock()
        self.mock_schema_path.exists.return_value = schema_exists
        
        def side_effect(path):
            if 'schema' in str(path):
                return self.mock_schema_path
            return self.mock_path
        
        self.mock_path.side_effect = side_effect
        
        self.addCleanup(self.patcher_path_exists.stop)

import sys
import unittest
from unittest.mock import Mock, patch
from tests.test_base import BaseTestCase
from tests.test_data_factory import TestDataFactory
from gh_milestone.cli import CLI

class TestCLI(BaseTestCase):
    """Test cases for the CLI class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        super().setUp()
        self.cli = CLI()

    def test_init(self):
        """Test CLI initialization."""
        cli = CLI()
        self.assertIsNotNone(cli.parser)
        self.assertIn('create', cli.command_handlers)
        self.assertIn('validate', cli.command_handlers)
        self.assertIn('delete', cli.command_handlers)
        self.assertIn('update', cli.command_handlers)
        self.assertIn('list', cli.command_handlers)
        self.assertIn('status', cli.command_handlers)
        self.assertIn('validate-state', cli.command_handlers)
        self.assertIn('migrate-state', cli.command_handlers)

    def test_parse_args_create_command(self):
        """Test parsing arguments for create command."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'create', 'roadmap.json']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='create',
                    roadmap_file='roadmap.json',
                    repo=None,
                    verbose=False
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.command, 'create')
                self.assertEqual(args.roadmap_file, 'roadmap.json')
                self.assertIsNone(args.repo)
                self.assertFalse(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_validate_command(self):
        """Test parsing arguments for validate command."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'validate', 'roadmap.json']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='validate',
                    roadmap_file='roadmap.json',
                    repo=None,
                    schema='schema.json',
                    verbose=False
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.command, 'validate')
                self.assertEqual(args.roadmap_file, 'roadmap.json')
                self.assertIsNone(args.repo)
                self.assertEqual(args.schema, 'schema.json')
                self.assertFalse(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_create_command_with_repo(self):
        """Test parsing arguments for create command with --repo option."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'create', 'roadmap.json', '--repo', 'testowner/testrepo']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='create',
                    roadmap_file='roadmap.json',
                    repo='testowner/testrepo',
                    verbose=False
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.command, 'create')
                self.assertEqual(args.repo, 'testowner/testrepo')
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_create_command_verbose(self):
        """Test parsing arguments for create command with verbose flag."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'create', 'roadmap.json', '--verbose']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='create',
                    roadmap_file='roadmap.json',
                    repo=None,
                    verbose=True
                )
                
                args = self.cli.parse_args()
                
                self.assertTrue(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_validate_command_verbose(self):
        """Test parsing arguments for validate command with verbose flag."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'validate', 'roadmap.json', '--schema', 'custom_schema.json', '--verbose']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='validate',
                    roadmap_file='roadmap.json',
                    schema='custom_schema.json',
                    verbose=True
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.schema, 'custom_schema.json')
                self.assertTrue(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_list_command(self):
        """Test parsing arguments for list command."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'list', 'roadmap.json']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='list',
                    roadmap_file='roadmap.json',
                    format='tree',
                    show_missing=False,
                    verbose=False
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.command, 'list')
                self.assertEqual(args.roadmap_file, 'roadmap.json')
                self.assertEqual(args.format, 'tree')
                self.assertFalse(args.show_missing)
                self.assertFalse(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_list_command_with_options(self):
        """Test parsing arguments for list command with options."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'list', 'roadmap.json', '--format', 'table', '--show-missing', '--verbose']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='list',
                    roadmap_file='roadmap.json',
                    format='table',
                    show_missing=True,
                    verbose=True
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.command, 'list')
                self.assertEqual(args.roadmap_file, 'roadmap.json')
                self.assertEqual(args.format, 'table')
                self.assertTrue(args.show_missing)
                self.assertTrue(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_delete_command(self):
        """Test parsing arguments for delete command."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'delete', 'roadmap.json', '--main']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='delete',
                    roadmap_file='roadmap.json',
                    repo=None,
                    main=True,
                    milestone=None,
                    task=None,
                    verbose=False
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.command, 'delete')
                self.assertEqual(args.roadmap_file, 'roadmap.json')
                self.assertIsNone(args.repo)
                self.assertTrue(args.main)
                self.assertIsNone(args.milestone)
                self.assertIsNone(args.task)
                self.assertFalse(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_delete_command_with_milestone(self):
        """Test delete command with milestone option."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'delete', 'roadmap.json', '--milestone', 'Test Milestone']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='delete',
                    roadmap_file='roadmap.json',
                    main=False,
                    milestone='Test Milestone',
                    task=None,
                    verbose=False
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.command, 'delete')
                self.assertEqual(args.roadmap_file, 'roadmap.json')
                self.assertFalse(args.main)
                self.assertEqual(args.milestone, 'Test Milestone')
                self.assertIsNone(args.task)
                self.assertFalse(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_delete_command_with_task(self):
        """Test delete command with task option."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'delete', 'roadmap.json', '--task', 'Test Task']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='delete',
                    roadmap_file='roadmap.json',
                    main=False,
                    milestone=None,
                    task='Test Task',
                    verbose=True
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.command, 'delete')
                self.assertEqual(args.roadmap_file, 'roadmap.json')
                self.assertFalse(args.main)
                self.assertIsNone(args.milestone)
                self.assertEqual(args.task, 'Test Task')
                self.assertTrue(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_update_command(self):
        """Test parsing arguments for update command."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'update', 'roadmap.json']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='update',
                    roadmap_file='roadmap.json',
                    verbose=False
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.command, 'update')
                self.assertEqual(args.roadmap_file, 'roadmap.json')
                self.assertFalse(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_update_command_with_options(self):
        """Test update command with various options."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'update', 'roadmap.json', '--verbose']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='update',
                    roadmap_file='roadmap.json',
                    verbose=True
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.command, 'update')
                self.assertEqual(args.roadmap_file, 'roadmap.json')
                self.assertTrue(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_status_command(self):
        """Test parsing arguments for status command."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'status', 'roadmap.json']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='status',
                    roadmap_file='roadmap.json',
                    format='tree',
                    verbose=False
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.command, 'status')
                self.assertEqual(args.roadmap_file, 'roadmap.json')
                self.assertEqual(args.format, 'tree')
                self.assertFalse(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_status_command_with_options(self):
        """Test status command with various options."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'status', 'roadmap.json', '--format', 'table', '--verbose']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='status',
                    roadmap_file='roadmap.json',
                    format='table',
                    verbose=True
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.command, 'status')
                self.assertEqual(args.roadmap_file, 'roadmap.json')
                self.assertEqual(args.format, 'table')
                self.assertTrue(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_validate_state_command(self):
        """Test parsing arguments for validate-state command."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'validate-state', 'roadmap.json']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='validate-state',
                    roadmap_file='roadmap.json',
                    cleanup=False,
                    dry_run=False,
                    verbose=False
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.command, 'validate-state')
                self.assertEqual(args.roadmap_file, 'roadmap.json')
                self.assertFalse(args.cleanup)
                self.assertFalse(args.dry_run)
                self.assertFalse(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_validate_state_command_with_cleanup(self):
        """Test parsing arguments for validate-state command with cleanup flag."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'validate-state', 'roadmap.json', '--cleanup']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='validate-state',
                    roadmap_file='roadmap.json',
                    cleanup=True,
                    dry_run=False,
                    verbose=False
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.command, 'validate-state')
                self.assertEqual(args.roadmap_file, 'roadmap.json')
                self.assertTrue(args.cleanup)
                self.assertFalse(args.dry_run)
                self.assertFalse(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_validate_state_command_with_dry_run(self):
        """Test parsing arguments for validate-state command with dry-run flag."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'validate-state', 'roadmap.json', '--dry-run']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='validate-state',
                    roadmap_file='roadmap.json',
                    cleanup=False,
                    dry_run=True,
                    verbose=False
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.command, 'validate-state')
                self.assertEqual(args.roadmap_file, 'roadmap.json')
                self.assertFalse(args.cleanup)
                self.assertTrue(args.dry_run)
                self.assertFalse(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_migrate_state_command(self):
        """Test parsing arguments for migrate-state command."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'migrate-state', 'roadmap.json']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='migrate-state',
                    roadmap_file='roadmap.json',
                    dry_run=False,
                    verbose=False
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.command, 'migrate-state')
                self.assertEqual(args.roadmap_file, 'roadmap.json')
                self.assertFalse(args.dry_run)
                self.assertFalse(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_parse_args_migrate_state_command_with_dry_run(self):
        """Test parsing arguments for migrate-state command with dry-run flag."""
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Set sys.argv to simulate command line arguments
            sys.argv = ['cli.py', 'migrate-state', 'roadmap.json', '--dry-run']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='migrate-state',
                    roadmap_file='roadmap.json',
                    dry_run=True,
                    verbose=False
                )
                
                args = self.cli.parse_args()
                
                self.assertEqual(args.command, 'migrate-state')
                self.assertEqual(args.roadmap_file, 'roadmap.json')
                self.assertTrue(args.dry_run)
                self.assertFalse(args.verbose)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    @patch('gh_milestone.cli.argparse.ArgumentParser.parse_args')
    @patch('gh_milestone.cli.Path.exists')
    @patch('builtins.print')
    @patch('sys.exit')
    def test_run_no_command(self, mock_exit, mock_print, mock_exists, mock_parse_args):
        """Test run method with no command provided."""
        mock_args = Mock(command=None, roadmap_file='roadmap.json', verbose=False, schema='schema.json')
        mock_parse_args.return_value = mock_args
        
        self.cli.run(mock_args)
        
        # Should show help and exit with code 0
        self.assertTrue(mock_exit.called)
        mock_exit.assert_any_call(0)

    @patch('gh_milestone.cli.argparse.ArgumentParser.parse_args')
    @patch('gh_milestone.cli.Path.exists')
    @patch('builtins.print')
    def test_run_file_not_found(self, mock_print, mock_exists, mock_parse_args):
        """Test run method when roadmap file doesn't exist."""
        mock_args = Mock(command='create', roadmap_file='nonexistent.json', verbose=False, schema='schema.json')
        mock_parse_args.return_value = mock_args
        mock_exists.return_value = False
        
        with patch('sys.exit') as mock_exit:
            self.cli.run(mock_args)
            # Check that exit was called with 1 (don't care how many times)
            mock_exit.assert_any_call(1)

    @patch('gh_milestone.cli.argparse.ArgumentParser.parse_args')
    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.GitHubClient')
    @patch('gh_milestone.cli.StateManager')
    @patch('gh_milestone.cli.SchemaValidator.load_json_file')
    @patch('gh_milestone.cli.SchemaValidator.validate_schema')
    @patch('gh_milestone.cli.SharedOperations.create_issues_from_roadmap')
    @patch('builtins.print')
    def test_run_create_command_success(self, mock_print, mock_create_issues, mock_validate_schema, mock_load_json, 
                                         mock_state_manager, mock_github_client, mock_exists, mock_parse_args):
        """Test run method with successful create command."""
        mock_args = Mock(command='create', roadmap_file='roadmap.json', verbose=False, schema='schema.json', repo=None)
        mock_parse_args.return_value = mock_args
        mock_exists.return_value = True
        roadmap_data = {'project': {'name': 'Test'}, 'milestones': []}
        mock_load_json.return_value = roadmap_data
        
        # Mock the GitHubClient and StateManager constructors
        mock_github_instance = Mock()
        mock_github_client.return_value = mock_github_instance
        mock_state_instance = Mock()
        mock_state_manager.return_value = mock_state_instance
        
        self.cli.run(mock_args)
        
        # Verify that the command was processed successfully
        mock_load_json.assert_called_once_with('roadmap.json')
        mock_validate_schema.assert_called_once_with(roadmap_data, 'schema.json')
        mock_create_issues.assert_called_once_with(roadmap_data, mock_github_instance, mock_state_instance)

    @patch('gh_milestone.cli.argparse.ArgumentParser.parse_args')
    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.GitHubClient')
    @patch('gh_milestone.cli.StateManager')
    @patch('gh_milestone.cli.SchemaValidator.load_json_file')
    @patch('gh_milestone.cli.SchemaValidator.validate_schema')
    @patch('gh_milestone.cli.SharedOperations.validate_roadmap_only')
    @patch('builtins.print')
    @patch('sys.exit')
    def test_run_validate_command_success(self, mock_exit, mock_print, mock_validate_roadmap_only, mock_validate_schema, 
                                         mock_load_json, mock_state_manager, mock_github_client, mock_exists, mock_parse_args):
        """Test run method with successful validate command."""
        mock_args = Mock(command='validate', roadmap_file='roadmap.json', 
                                         schema='schema.json', verbose=False, repo=None)
        mock_parse_args.return_value = mock_args
        mock_exists.return_value = True
        roadmap_data = {'project': {'name': 'Test'}, 'milestones': []}
        mock_load_json.return_value = roadmap_data
        
        # Mock the validate_roadmap_only method to do nothing (success case)
        mock_validate_roadmap_only.return_value = None
        
        # Configure sys.exit to raise SystemExit exception
        mock_exit.side_effect = SystemExit(0)
        
        # Verify that SystemExit is raised (CLI calls sys.exit on success)
        with self.assertRaises(SystemExit):
            self.cli.run(mock_args)
        
        # Verify that command was processed successfully
        mock_load_json.assert_called_once_with('roadmap.json')
        mock_validate_schema.assert_called_once_with(roadmap_data, 'schema.json')
        mock_validate_roadmap_only.assert_called_once_with(roadmap_data, 'schema.json')
        # Check that the validation message was called
        mock_print.assert_any_call("✅ Roadmap validation successful")

if __name__ == '__main__':
    unittest.main()

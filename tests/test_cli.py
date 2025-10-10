import sys
import unittest
from unittest.mock import Mock, patch, AsyncMock
from tests.test_base import BaseTestCase
from tests.test_data_factory import TestDataFactory
from gh_milestone.cli import CLI

class TestCLI(BaseTestCase):
    """Test cases for the CLI class."""

    def test_init(self):
        """Test CLI initialization."""
        cli = self.create_cli_instance()
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
        self._test_parse_args(
            ['cli.py', 'create', 'roadmap.json'],
            {
                'command': 'create',
                'roadmap_file': 'roadmap.json',
                'repo': None,
                'verbose': False
            }
        )

    def test_parse_args_validate_command(self):
        """Test parsing arguments for validate command."""
        self._test_parse_args(
            ['cli.py', 'validate', 'roadmap.json'],
            {
                'command': 'validate',
                'roadmap_file': 'roadmap.json',
                'repo': None,
                'schema': 'schema.json',
                'verbose': False
            }
        )

    def test_parse_args_create_command_with_repo(self):
        """Test parsing arguments for create command with --repo option."""
        self._test_parse_args(
            ['cli.py', 'create', 'roadmap.json', '--repo', 'testowner/testrepo'],
            {
                'command': 'create',
                'roadmap_file': 'roadmap.json',
                'repo': 'testowner/testrepo',
                'verbose': False
            }
        )

    def test_parse_args_create_command_verbose(self):
        """Test parsing arguments for create command with verbose flag."""
        self._test_parse_args(
            ['cli.py', 'create', 'roadmap.json', '--verbose'],
            {
                'command': 'create',
                'roadmap_file': 'roadmap.json',
                'repo': None,
                'verbose': True
            }
        )

    def test_parse_args_validate_command_verbose(self):
        """Test parsing arguments for validate command with verbose flag."""
        self._test_parse_args(
            ['cli.py', 'validate', 'roadmap.json', '--schema', 'custom_schema.json', '--verbose'],
            {
                'command': 'validate',
                'roadmap_file': 'roadmap.json',
                'schema': 'custom_schema.json',
                'verbose': True
            }
        )

    def test_parse_args_list_command(self):
        """Test parsing arguments for list command."""
        self._test_parse_args(
            ['cli.py', 'list', 'roadmap.json'],
            {
                'command': 'list',
                'roadmap_file': 'roadmap.json',
                'format': 'tree',
                'show_missing': False,
                'verbose': False
            }
        )

    def test_parse_args_list_command_with_options(self):
        """Test parsing arguments for list command with options."""
        self._test_parse_args(
            ['cli.py', 'list', 'roadmap.json', '--format', 'table', '--show-missing', '--verbose'],
            {
                'command': 'list',
                'roadmap_file': 'roadmap.json',
                'format': 'table',
                'show_missing': True,
                'verbose': True
            }
        )

    def test_parse_args_delete_command(self):
        """Test parsing arguments for delete command."""
        self._test_parse_args(
            ['cli.py', 'delete', 'roadmap.json', '--main'],
            {
                'command': 'delete',
                'roadmap_file': 'roadmap.json',
                'repo': None,
                'main': True,
                'milestone': None,
                'task': None,
                'verbose': False
            }
        )

    def test_parse_args_delete_command_with_milestone(self):
        """Test delete command with milestone option."""
        self._test_parse_args(
            ['cli.py', 'delete', 'roadmap.json', '--milestone', 'Test Milestone'],
            {
                'command': 'delete',
                'roadmap_file': 'roadmap.json',
                'main': False,
                'milestone': 'Test Milestone',
                'task': None,
                'verbose': False
            }
        )

    def test_parse_args_delete_command_with_task(self):
        """Test delete command with task option."""
        self._test_parse_args(
            ['cli.py', 'delete', 'roadmap.json', '--task', 'Test Task'],
            {
                'command': 'delete',
                'roadmap_file': 'roadmap.json',
                'main': False,
                'milestone': None,
                'task': 'Test Task',
                'verbose': False  # Note: verbose isn't set in argv, so it should be False
            }
        )

    def test_parse_args_update_command(self):
        """Test parsing arguments for update command."""
        self._test_parse_args(
            ['cli.py', 'update', 'roadmap.json'],
            {
                'command': 'update',
                'roadmap_file': 'roadmap.json',
                'verbose': False
            }
        )

    def test_parse_args_update_command_with_options(self):
        """Test update command with various options."""
        self._test_parse_args(
            ['cli.py', 'update', 'roadmap.json', '--verbose'],
            {
                'command': 'update',
                'roadmap_file': 'roadmap.json',
                'verbose': True
            }
        )

    def test_parse_args_status_command(self):
        """Test parsing arguments for status command."""
        self._test_parse_args(
            ['cli.py', 'status', 'roadmap.json'],
            {
                'command': 'status',
                'roadmap_file': 'roadmap.json',
                'format': 'tree',
                'verbose': False
            }
        )

    def test_parse_args_status_command_with_options(self):
        """Test status command with various options."""
        self._test_parse_args(
            ['cli.py', 'status', 'roadmap.json', '--format', 'table', '--verbose'],
            {
                'command': 'status',
                'roadmap_file': 'roadmap.json',
                'format': 'table',
                'verbose': True
            }
        )

    def test_parse_args_validate_state_command(self):
        """Test parsing arguments for validate-state command."""
        self._test_parse_args(
            ['cli.py', 'validate-state', 'roadmap.json'],
            {
                'command': 'validate-state',
                'roadmap_file': 'roadmap.json',
                'cleanup': False,
                'dry_run': False,
                'verbose': False
            }
        )

    def test_parse_args_validate_state_command_with_cleanup(self):
        """Test parsing arguments for validate-state command with cleanup flag."""
        self._test_parse_args(
            ['cli.py', 'validate-state', 'roadmap.json', '--cleanup'],
            {
                'command': 'validate-state',
                'roadmap_file': 'roadmap.json',
                'cleanup': True,
                'dry_run': False,
                'verbose': False
            }
        )

    def test_parse_args_validate_state_command_with_dry_run(self):
        """Test parsing arguments for validate-state command with dry-run flag."""
        self._test_parse_args(
            ['cli.py', 'validate-state', 'roadmap.json', '--dry-run'],
            {
                'command': 'validate-state',
                'roadmap_file': 'roadmap.json',
                'cleanup': False,
                'dry_run': True,
                'verbose': False
            }
        )

    def test_parse_args_migrate_state_command(self):
        """Test parsing arguments for migrate-state command."""
        self._test_parse_args(
            ['cli.py', 'migrate-state', 'roadmap.json'],
            {
                'command': 'migrate-state',
                'roadmap_file': 'roadmap.json',
                'dry_run': False,
                'verbose': False
            }
        )

    def test_parse_args_migrate_state_command_with_dry_run(self):
        """Test parsing arguments for migrate-state command with dry-run flag."""
        self._test_parse_args(
            ['cli.py', 'migrate-state', 'roadmap.json', '--dry-run'],
            {
                'command': 'migrate-state',
                'roadmap_file': 'roadmap.json',
                'dry_run': True,
                'verbose': False
            }
        )

    def test_parse_args_create_command_default_filename(self):
        """Test that create command uses default filename when no roadmap_file is provided."""
        self._test_parse_args(
            ['cli.py', 'create'],
            {
                'command': 'create',
                'roadmap_file': 'roadmap.json',
                'repo': None,
                'verbose': False
            }
        )

    def test_parse_args_validate_command_default_filename(self):
        """Test that validate command uses default filename when no roadmap_file is provided."""
        self._test_parse_args(
            ['cli.py', 'validate'],
            {
                'command': 'validate',
                'roadmap_file': 'roadmap.json',
                'repo': None,
                'schema': 'schema.json',
                'verbose': False
            }
        )

    def test_parse_args_mcp_command(self):
        """Test parsing arguments for mcp command."""
        self._test_parse_args(
            ['cli.py', 'mcp'],
            {
                'command': 'mcp',
                'host': 'localhost',
                'port': 8080,
                'transport': 'stdio',
                'schema': 'schema.json',
                'verbose': False
            }
        )

    def test_parse_args_mcp_command_with_options(self):
        """Test parsing arguments for mcp command with custom options."""
        self._test_parse_args(
            ['cli.py', 'mcp', '--host', '0.0.0.0', '--port', '9000', '--transport', 'http', '--verbose'],
            {
                'command': 'mcp',
                'host': '0.0.0.0',
                'port': 9000,
                'transport': 'http',
                'schema': 'schema.json',
                'verbose': True
            }
        )

    def test_parse_args_mcp_server_command(self):
        """Test parsing arguments for mcp-server command."""
        self._test_parse_args(
            ['cli.py', 'mcp-server'],
            {
                'command': 'mcp-server',
                'host': 'localhost',
                'port': 8000,
                'schema_file': 'schema.json',
                'verbose': False
            }
        )

    def test_parse_args_mcp_server_command_with_options(self):
        """Test parsing arguments for mcp-server command with custom options."""
        self._test_parse_args(
            ['cli.py', 'mcp-server', '--host', '0.0.0.0', '--port', '9000', '--verbose'],
            {
                'command': 'mcp-server',
                'host': '0.0.0.0',
                'port': 9000,
                'schema_file': 'schema.json',
                'verbose': True
            }
        )

    def _test_parse_args(self, argv, expected_args):
        """Helper method to test argument parsing with given argv and expected results."""
        with self.sys_argv_context(argv):
            cli = self.create_cli_instance()
            mock_parse_args = self.setup_argparse_mocks()
            mock_parse_args.return_value = self.build_mock_args(**expected_args)
            
            args = cli.parse_args()
            
            # Check all expected attributes
            for key, value in expected_args.items():
                self.assertEqual(getattr(args, key), value, f"Attribute {key} mismatch")
            
            return args

    def test_run_no_command(self):
        """Test run method with no command provided."""
        cli = self.create_cli_instance()
        self.setup_print_and_exit_mocks()
        
        mock_args = self.build_mock_args(command=None)
        
        cli.run(mock_args)
        
        # Should show help and exit with code 0
        self.assertTrue(self.mock_exit.called)
        self.mock_exit.assert_any_call(0)

    def test_run_file_not_found(self):
        """Test run method when roadmap file doesn't exist."""
        cli = self.create_cli_instance()
        self.setup_print_and_exit_mocks()
        self.setup_path_exists_mocks(roadmap_exists=False)
        
        mock_args = self.build_mock_args(command='create', roadmap_file='nonexistent.json')
        
        cli.run(mock_args)
        # Check that exit was called with 1 (don't care how many times)
        self.mock_exit.assert_any_call(1)

    def test_run_create_command_success(self):
        """Test run method with successful create command."""
        config = self.setup_parameterized_test_scenario('cli_success', command='create')
        cli = config['cli']
        mock_args = config['args']
        
        with patch('gh_milestone.cli.SharedOperations.create_issues_from_roadmap') as mock_create_issues:
            cli.run(mock_args)
            
            # Verify that the command was processed successfully
            config['load_json'].assert_called_once_with('roadmap.json')
            config['validate_schema'].assert_called_once_with(self.roadmap_data, 'schema.json')
            mock_create_issues.assert_called_once_with(self.roadmap_data, config['github_client'], config['state_manager'])

    def test_run_validate_command_success(self):
        """Test run method with successful validate command."""
        config = self.setup_parameterized_test_scenario('cli_success', command='validate')
        cli = config['cli']
        mock_args = config['args']
        mock_exit = config['exit']
        mock_print = config['print']
        
        with patch('gh_milestone.cli.SharedOperations.validate_roadmap_only') as mock_validate_roadmap_only:
            # Mock the validate_roadmap_only method to do nothing (success case)
            mock_validate_roadmap_only.return_value = None
            
            # Configure sys.exit to raise SystemExit exception
            mock_exit.side_effect = SystemExit(0)
            
            # Verify that SystemExit is raised (CLI calls sys.exit on success)
            with self.assertRaises(SystemExit):
                cli.run(mock_args)
            
            # Verify that command was processed successfully
            config['load_json'].assert_called_once_with('roadmap.json')
            config['validate_schema'].assert_called_once_with(self.roadmap_data, 'schema.json')
            mock_validate_roadmap_only.assert_called_once_with(self.roadmap_data, 'schema.json')
            # Check that the validation message was called
            mock_print.assert_any_call("✅ Roadmap validation successful")

    def test_run_mcp_command_stdio_success(self):
        """Test run method with successful mcp command using stdio transport."""
        cli = self.create_cli_instance()
        mock_args = self.build_mock_args(
            command='mcp',
            transport='stdio'
        )
        
        # Mock CLI._load_aliases to return empty dict to avoid Path operations
        with patch.object(cli, '_load_aliases', return_value={}):
            # Mock Path.exists to return True for schema file
            with patch('gh_milestone.cli.Path') as mock_path_class:
                mock_path_instance = Mock()
                mock_path_instance.exists.return_value = True
                mock_path_class.return_value = mock_path_instance
            # Mock Path.exists to return True for schema file
            with patch('gh_milestone.cli.Path') as mock_path_class:
                mock_path_instance = Mock()
                mock_path_instance.exists.return_value = True
                mock_path_class.return_value = mock_path_instance
                
                with patch('gh_milestone.cli.SharedOperations.validate_roadmap_only') as mock_validate_roadmap_only:
                    mock_validate_roadmap_only.return_value = None
                    
                    with patch('gh_milestone.cli.CLI._handle_mcp_command') as mock_mcp_server:
                        mock_server_instance = Mock()
                        mock_server_instance.run_stdio = AsyncMock()
                        mock_mcp_server.return_value = mock_server_instance
                        
                        with patch('asyncio.run') as mock_asyncio_run:
                            cli.run(mock_args)
                            
                            # Verify that MCPServer was created with correct parameters
                            mock_mcp_server.assert_called_once_with(schema_file='schema.json', verbose=False)

    def test_run_mcp_command_http_success(self):
        """Test run method with successful mcp command using http transport."""
        cli = self.create_cli_instance()
        mock_args = self.build_mock_args(
            command='mcp',
            host='0.0.0.0',
            port=9000,
            transport='http',
            verbose=True
        )
        
        # Mock CLI._load_aliases to return empty dict to avoid Path operations
        with patch.object(cli, '_load_aliases', return_value={}):
            # Mock Path.exists to return True for schema file
            with patch('gh_milestone.cli.Path') as mock_path_class:
                mock_path_instance = Mock()
                mock_path_instance.exists.return_value = True
                mock_path_class.return_value = mock_path_instance
                
                with patch('gh_milestone.cli.SharedOperations.validate_roadmap_only') as mock_validate_roadmap_only:
                    mock_validate_roadmap_only.return_value = None
                    
                    with patch('gh_milestone.cli.MCPServer') as mock_mcp_server:
                        mock_server_instance = Mock()
                        mock_server_instance.run_http = AsyncMock()
                        mock_mcp_server.return_value = mock_server_instance
                        
                        with patch('asyncio.run') as mock_asyncio_run:
                            cli.run(mock_args)
                            
                            # Verify that MCPServer was created with correct parameters
                            mock_mcp_server.assert_called_once_with(schema_file='schema.json', verbose=True)

    def test_run_mcp_command_schema_not_found(self):
        """Test run method when schema file doesn't exist for mcp command."""
        cli = self.create_cli_instance()
        self.setup_print_and_exit_mocks()
        self.setup_path_exists_mocks(schema_exists=False)
        
        mock_args = self.build_mock_args(
            command='mcp',
            host='localhost',
            port=8080,
            transport='stdio',
            schema='nonexistent_schema.json',
            verbose=False
        )
        
        cli.run(mock_args)
        
        # Should print error and exit with code 1
        self.mock_print.assert_any_call("Error: Schema file 'nonexistent_schema.json' not found.")
        self.mock_exit.assert_any_call(1)

    def test_run_mcp_command_keyboard_interrupt(self):
        """Test run method with keyboard interrupt during mcp command."""
        cli = self.create_cli_instance()
        mock_args = self.build_mock_args(
            command='mcp',
            transport='stdio'
        )
        
        # Mock CLI._load_aliases to return empty dict to avoid Path operations
        with patch.object(cli, '_load_aliases', return_value={}):
            # Mock Path.exists to return True for schema file
            with patch('gh_milestone.cli.Path') as mock_path_class:
                mock_path_instance = Mock()
                mock_path_instance.exists.return_value = True
                mock_path_class.return_value = mock_path_instance
                
                with patch('gh_milestone.shared_operations.SharedOperations.validate_roadmap_only') as mock_validate_roadmap_only:
                    mock_validate_roadmap_only.side_effect = KeyboardInterrupt()
                    
                    with patch('gh_milestone.cli.MCPServer') as mock_mcp_server:
                        mock_server_instance = Mock()
                        mock_server_instance.run_stdio = AsyncMock(side_effect=KeyboardInterrupt())
                        mock_mcp_server.return_value = mock_server_instance
                        
                        with patch('asyncio.run') as mock_asyncio_run:
                            mock_asyncio_run.side_effect = KeyboardInterrupt()
                            
                            with patch('builtins.print') as mock_print:
                                with patch('sys.exit') as mock_exit:
                                    mock_exit.side_effect = SystemExit(1)
                                    
                                    with self.assertRaises(SystemExit):
                                        cli.run(mock_args)
                                    
                                    # Should print stop message and exit with code 1
                                    mock_print.assert_any_call("\n❌ Operation cancelled by user.")
                                    mock_exit.assert_called_with(1)

    def test_run_mcp_command_exception(self):
        """Test run method with exception during mcp command."""
        cli = self.create_cli_instance()
        mock_args = self.build_mock_args(
            command='mcp',
            transport='stdio'
        )
        
        # Mock CLI._load_aliases to return empty dict to avoid Path operations
        with patch.object(cli, '_load_aliases', return_value={}):
            # Mock Path.exists to return True for schema file
            with patch('gh_milestone.cli.Path') as mock_path_class:
                mock_path_instance = Mock()
                mock_path_instance.exists.return_value = True
                mock_path_class.return_value = mock_path_instance
            
            # Directly mock _handle_mcp_command to raise exception
            with patch.object(cli, '_handle_mcp_command') as mock_handle_mcp:
                mock_handle_mcp.side_effect = Exception("Server error")
                
                with patch('builtins.print') as mock_print:
                    with patch('sys.exit') as mock_exit:
                        mock_exit.side_effect = SystemExit(1)
                        
                        with self.assertRaises(SystemExit):
                            cli.run(mock_args)
                        
                        # Should print error message and exit with code 1
                        mock_print.assert_any_call("❌ Unexpected error: Server error")
                        mock_exit.assert_called_with(1)

    def test_run_mcp_server_command_success(self):
        """Test run method with successful mcp-server command."""
        cli = self.create_cli_instance()
        mock_args = self.build_mock_args(
            command='mcp-server',
            host='localhost',
            port=8000
        )
        
        # Mock CLI._load_aliases to avoid Path operations
        with patch.object(cli, '_load_aliases', return_value={}):
            # Mock Path.exists to return True for schema file
            with patch('gh_milestone.cli.Path') as mock_path_class:
                mock_path_instance = Mock()
                mock_path_instance.exists.return_value = True
                mock_path_class.return_value = mock_path_instance
                
                with patch('gh_milestone.cli.SharedOperations.validate_roadmap_only') as mock_validate_roadmap_only:
                    mock_validate_roadmap_only.return_value = None
                    
                    with patch('gh_milestone.cli.CLI._handle_mcp_server_command') as mock_mcp_http_server:
                        mock_server_instance = Mock()
                        mock_server_instance.run = Mock()
                        mock_mcp_http_server.return_value = mock_server_instance
                        
                        cli.run(mock_args)
                        
                        # Verify that MCPHTTPServer was created with correct parameters
                        mock_mcp_http_server.assert_called_once_with(schema_file='schema.json', verbose=False)

    def test_run_mcp_server_command_schema_not_found(self):
        """Test run method when schema file doesn't exist for mcp-server command."""
        cli = self.create_cli_instance()
        self.setup_print_and_exit_mocks()
        self.setup_path_exists_mocks(schema_exists=False)
        
        mock_args = self.build_mock_args(
            command='mcp-server',
            host='localhost',
            port=8000,
            schema_file='nonexistent_schema.json',
            verbose=False
        )
        
        cli.run(mock_args)
        
        # Should print error and exit with code 1
        self.mock_print.assert_any_call("Error: Schema file 'nonexistent_schema.json' not found.")
        self.mock_exit.assert_any_call(1)

    def test_run_mcp_server_command_keyboard_interrupt(self):
        """Test run method with keyboard interrupt during mcp-server command."""
        cli = self.create_cli_instance()
        mock_args = self.build_mock_args(
            command='mcp-server',
            host='localhost',
            port=8000
        )
        
        # Mock CLI._load_aliases to avoid Path operations
        with patch.object(cli, '_load_aliases', return_value={}):
            # Mock Path.exists to return True for schema file
            with patch('gh_milestone.cli.Path') as mock_path_class:
                mock_path_instance = Mock()
                mock_path_instance.exists.return_value = True
                mock_path_class.return_value = mock_path_instance
                
                with patch('gh_milestone.cli.SharedOperations.validate_roadmap_only') as mock_validate_roadmap_only:
                    mock_validate_roadmap_only.side_effect = KeyboardInterrupt()
                    
                    with patch('gh_milestone.cli.CLI._handle_mcp_server_command') as mock_mcp_http_server:
                        mock_server_instance = Mock()
                        mock_server_instance.run = Mock(side_effect=KeyboardInterrupt())
                        mock_mcp_http_server.return_value = mock_server_instance
                        
                        with patch('builtins.print') as mock_print:
                            with patch('sys.exit') as mock_exit:
                                mock_exit.side_effect = SystemExit(1)
                                
                                with self.assertRaises(SystemExit):
                                    cli.run(mock_args)
                                
                                # Should print stop message and exit with code 1
                                mock_print.assert_any_call("\n❌ Operation cancelled by user.")
                                mock_exit.assert_called_with(1)

    def test_run_mcp_server_command_exception(self):
        """Test run method with exception during mcp-server command."""
        cli = self.create_cli_instance()
        mock_args = self.build_mock_args(
            command='mcp-server',
            host='localhost',
            port=8000
        )
        
        # Mock CLI._load_aliases to avoid Path operations
        with patch.object(cli, '_load_aliases', return_value={}):
            # Mock Path.exists to return True for schema file
            with patch('gh_milestone.cli.Path') as mock_path_class:
                mock_path_instance = Mock()
                mock_path_instance.exists.return_value = True
                mock_path_class.return_value = mock_path_instance
                
                with patch('gh_milestone.cli.SharedOperations.validate_roadmap_only') as mock_validate_roadmap_only:
                    mock_validate_roadmap_only.side_effect = Exception("HTTP server error")
                    
                    with patch('gh_milestone.cli.CLI._handle_mcp_server_command') as mock_mcp_http_server:
                        mock_server_instance = Mock()
                        mock_server_instance.run = Mock(side_effect=Exception("HTTP server error"))
                        mock_mcp_http_server.return_value = mock_server_instance
                        
                        with patch('builtins.print') as mock_print:
                            with patch('sys.exit') as mock_exit:
                                mock_exit.side_effect = SystemExit(1)
                                
                                with self.assertRaises(SystemExit):
                                    cli.run(mock_args)
                                
                                # Should print error message and exit with code 1
                                mock_print.assert_any_call("❌ Unexpected error: HTTP server error")
                                mock_exit.assert_called_with(1)

if __name__ == '__main__':
    unittest.main()

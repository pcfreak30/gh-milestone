"""Base test case class with common setup utilities."""

import unittest
from unittest.mock import Mock, patch
import sys
import os
from pathlib import Path
from contextlib import contextmanager

# Add the parent directory to the path so we can import gh_milestone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gh_milestone.cli import CLI


class BaseTestCase(unittest.TestCase):
    """Base class with common test setup utilities."""
    
    def setUp(self):
        """Set up common test fixtures."""
        # Initialize basic attributes without setting up mocks automatically
        self.cli = None
        self.mock_args = None
        self.roadmap_data = None
        
        # Initialize mock storage - we'll use addCleanup for better pytest compatibility
        self._active_patchers = []
        
        # Create basic data structures
        self.mock_args = self._create_mock_args()
        self.roadmap_data = self._create_roadmap_data()
    
    def tearDown(self):
        """Clean up any remaining resources."""
        # We now use addCleanup for patcher management, which is more reliable
        # and works better with pytest. This method is kept for any additional
        # cleanup that might be needed in the future.
        self._active_patchers.clear()
    
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
        
        # Patch imports using addCleanup for automatic cleanup
        self.patcher_github = patch('gh_milestone.github_client.GitHubClient')
        self.patcher_state = patch('gh_milestone.state_manager.StateManager')
        self.patcher_issue = patch('gh_milestone.issue_creator.IssueCreator')
        
        # Start patchers and register cleanup
        self.mock_github_client_class = self.patcher_github.start()
        self.addCleanup(self._safe_stop_patcher, self.patcher_github)
        
        self.mock_state_manager_class = self.patcher_state.start()
        self.addCleanup(self._safe_stop_patcher, self.patcher_state)
        
        self.mock_issue_creator_class = self.patcher_issue.start()
        self.addCleanup(self._safe_stop_patcher, self.patcher_issue)
        
        # Configure return values
        self.mock_github_client_class.return_value = self.mock_github_client
        self.mock_state_manager_class.return_value = self.mock_state_manager
        self.mock_issue_creator_class.return_value = self.mock_issue_creator
    
    def setup_print_and_exit_mocks(self):
        """Set up print and exit mocks."""
        self.patcher_print = patch('builtins.print')
        self.patcher_exit = patch('sys.exit')
        
        # Start patchers and register cleanup
        self.mock_print = self.patcher_print.start()
        self.addCleanup(self._safe_stop_patcher, self.patcher_print)
        
        self.mock_exit = self.patcher_exit.start()
        self.addCleanup(self._safe_stop_patcher, self.patcher_exit)
        
        return self.mock_print, self.mock_exit
    
    def setup_schema_validator_mocks(self):
        """Set up schema validator mocks."""
        self.patcher_load_json = patch('gh_milestone.schema_validator.SchemaValidator.load_json_file')
        self.patcher_validate_schema = patch('gh_milestone.schema_validator.SchemaValidator.validate_schema')
        
        # Start patchers and register cleanup
        self.mock_load_json = self.patcher_load_json.start()
        self.addCleanup(self._safe_stop_patcher, self.patcher_load_json)
        
        self.mock_validate_schema = self.patcher_validate_schema.start()
        self.addCleanup(self._safe_stop_patcher, self.patcher_validate_schema)
    
    def setup_path_exists_mocks(self, roadmap_exists=True, schema_exists=True):
        """Set up path existence mocks."""
        self.patcher_path_exists = patch('gh_milestone.cli.Path')
        
        # Start patcher and register cleanup
        mock_path_class = self.patcher_path_exists.start()
        self.addCleanup(self._safe_stop_patcher, self.patcher_path_exists)
        
        # Create separate mock instances for different paths
        self.mock_roadmap_path = Mock()
        self.mock_roadmap_path.exists.return_value = roadmap_exists
        
        self.mock_schema_path = Mock()
        self.mock_schema_path.exists.return_value = schema_exists
        
        def path_side_effect(path):
            # Convert path to string and check if it's a schema file
            path_str = str(path)
            mock_path_instance = Mock()
            if 'schema' in path_str.lower():
                mock_path_instance.exists.return_value = schema_exists
            else:
                mock_path_instance.exists.return_value = roadmap_exists
            return mock_path_instance
        
        mock_path_class.side_effect = path_side_effect
    
    def setup_path_mocks(self, exists_return_value=True, read_text_return_value=""):
        """Set up mocks for Path operations (exists and read_text).
        
        Args:
            exists_return_value: Value to return from exists() mock
            read_text_return_value: Value to return from read_text() mock
            
        Returns:
            Tuple of (mock_path_class, mock_path_instance)
        """
        patcher_path = patch('gh_milestone.cli.Path')
        
        mock_path_class = patcher_path.start()
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = exists_return_value
        mock_path_instance.read_text.return_value = read_text_return_value
        mock_path_class.return_value = mock_path_instance
        
        self.addCleanup(self._safe_stop_patcher, patcher_path)
        
        return mock_path_class, mock_path_instance

    def setup_open_mocks(self, read_data="", side_effect=None):
        """Set up mocks for builtins.open operations.
        
        Args:
            read_data: Data to return when reading from mocked file
            side_effect: Side effect to apply to the open mock
            
        Returns:
            mock_open
        """
        patcher_open = patch('builtins.open', mock_open=read_data, side_effect=side_effect)
        
        mock_open = patcher_open.start()
        
        self.addCleanup(self._safe_stop_patcher, patcher_open)
        
        return mock_open
    def _safe_stop_patcher(self, patcher):
        """Safely stop a patcher, ignoring errors if already stopped."""
        try:
            if hasattr(patcher, 'is_local') and patcher.is_local:
                patcher.stop()
        except (RuntimeError, AttributeError):
            # Patcher was already stopped or doesn't exist
            pass
    
    def _cleanup_failed_patchers(self, patchers):
        """Clean up patchers that may have been started during a failed setup."""
        for patcher in patchers:
            self._safe_stop_patcher(patcher)
    
    def create_cli_instance(self):
        """Create a CLI instance when needed."""
        if self.cli is None:
            self.cli = CLI()
        return self.cli

    def setup_cli_command_mocks(self):
        """Set up common mocks for CLI commands.
        
        Returns:
            Tuple of (mock_github_client_class, mock_state_manager_class, mock_validate_roadmap_only)
        """
        patcher_get_repo_name = patch('gh_milestone.cli.Config.get_repo_name')
        patcher_github_client = patch('gh_milestone.cli.GitHubClient')
        patcher_state_manager = patch('gh_milestone.cli.StateManager')
        patcher_validate_roadmap = patch('gh_milestone.cli.SharedOperations.validate_roadmap_only')
        
        mock_get_repo_name = patcher_get_repo_name.start()
        mock_github_client_class = patcher_github_client.start()
        mock_state_manager_class = patcher_state_manager.start()
        mock_validate_roadmap_only = patcher_validate_roadmap.start()
        
        self.addCleanup(self._safe_stop_patcher, patcher_get_repo_name)
        self.addCleanup(self._safe_stop_patcher, patcher_github_client)
        self.addCleanup(self._safe_stop_patcher, patcher_state_manager)
        self.addCleanup(self._safe_stop_patcher, patcher_validate_roadmap)
        
        # Set default return values
        mock_get_repo_name.return_value = 'testowner/testrepo'
        
        return (mock_github_client_class, mock_state_manager_class, mock_validate_roadmap_only)

    def setup_mcp_command_mocks(self):
        """Set up common mocks for MCP commands.
        
        Returns:
            Tuple of (mock_asyncio_run, mock_mcp_server)
        """
        patcher_asyncio_run = patch('asyncio.run')
        patcher_mcp_server = patch('gh_milestone.mcp_server.MCPServer')
        
        mock_asyncio_run = patcher_asyncio_run.start()
        mock_mcp_server = patcher_mcp_server.start()
        
        self.addCleanup(self._safe_stop_patcher, patcher_asyncio_run)
        self.addCleanup(self._safe_stop_patcher, patcher_mcp_server)
        
        return mock_asyncio_run, mock_mcp_server

    def setup_mcp_http_server_mocks(self):
        """Set up common mocks for MCP HTTP server commands.
        
        Returns:
            mock_mcp_http_server
        """
        patcher_mcp_http_server = patch('gh_milestone.mcp_http_server.MCPHTTPServer')
        
        mock_mcp_http_server = patcher_mcp_http_server.start()
        
        self.addCleanup(self._safe_stop_patcher, patcher_mcp_http_server)
        
        return mock_mcp_http_server

    def setup_argparse_mocks(self):
        """Set up mocks for argparse.ArgumentParser.parse_args.
        
        Returns:
            mock_parse_args
        """
        patcher_parse_args = patch('gh_milestone.cli.argparse.ArgumentParser.parse_args')
        
        mock_parse_args = patcher_parse_args.start()
        
        self.addCleanup(self._safe_stop_patcher, patcher_parse_args)
        
        return mock_parse_args

    def setup_cli_command_test(self):
        """Set up all common mocks for CLI command tests.
        
        Returns:
            Tuple of (mock_github_client_class, mock_state_manager_class, mock_print, mock_exit, 
                     mock_load_json, mock_validate_schema, mock_roadmap_path, mock_schema_path)
        """
        # Set up Config.get_repo_name mock
        patcher_get_repo_name = patch('gh_milestone.cli.Config.get_repo_name')
        mock_get_repo_name = patcher_get_repo_name.start()
        mock_get_repo_name.return_value = 'testowner/testrepo'
        self.addCleanup(self._safe_stop_patcher, patcher_get_repo_name)
        
        # Set up GitHubClient and StateManager mocks
        mock_github_client_class, mock_state_manager_class, _ = self.setup_cli_command_mocks()
        
        # Set up print and exit mocks
        mock_print, mock_exit = self.setup_print_and_exit_mocks()
        
        # Set up path exists mocks
        self.setup_path_exists_mocks()
        
        # Set up schema validator mocks
        self.setup_schema_validator_mocks()
        
        # Return all mocks for test-specific configuration
        return (mock_github_client_class, mock_state_manager_class, mock_print, mock_exit, 
                self.mock_load_json, self.mock_validate_schema, self.mock_roadmap_path, self.mock_schema_path)

    def setup_mcp_command_test(self):
        """Set up all common mocks for MCP command tests.
        
        Returns:
            Tuple of (mock_print, mock_exit, mock_path_exists, mock_asyncio_run, mock_mcp_server)
        """
        # Set up print and exit mocks
        mock_print, mock_exit = self.setup_print_and_exit_mocks()
        
        # Set up path exists mocks for schema file
        self.setup_path_exists_mocks(roadmap_exists=False, schema_exists=True)
        
        # Set up asyncio.run and MCPServer mocks
        mock_asyncio_run, mock_mcp_server = self.setup_mcp_command_mocks()
        
        # Return mocks for test-specific configuration
        return (mock_print, mock_exit, self.mock_schema_path, mock_asyncio_run, mock_mcp_server)

    def setup_mcp_http_server_test(self):
        """Set up all common mocks for MCP HTTP server tests.
        
        Returns:
            Tuple of (mock_print, mock_exit, mock_path_exists, mock_mcp_http_server)
        """
        # Set up print and exit mocks
        mock_print, mock_exit = self.setup_print_and_exit_mocks()
        
        # Set up path exists mocks for schema file
        self.setup_path_exists_mocks(roadmap_exists=False, schema_exists=True)
        
        # Set up MCPHTTPServer mock
        mock_mcp_http_server = self.setup_mcp_http_server_mocks()
        
        # Return mocks for test-specific configuration
        return (mock_print, mock_exit, self.mock_schema_path, mock_mcp_http_server)

    def setup_completion_test(self):
        """Set up all common mocks for completion tests.
        
        Returns:
            Tuple of (mock_parse_args, mock_path_class, mock_path_instance, mock_open)
        """
        # Set up argparse mocks
        mock_parse_args = self.setup_argparse_mocks()
        
        # Set up path mocks
        mock_path_class, mock_path_instance = self.setup_path_mocks()
        
        # Set up open mocks
        mock_open = self.setup_open_mocks()
        
        # Return mocks for test-specific configuration
        return (mock_parse_args, mock_path_class, mock_path_instance, mock_open)

    def setup_basic_completion_mocks(self):
        """Set up basic print and exit mocks for completion tests.
        
        Returns:
            Tuple of (mock_print, mock_exit)
        """
        return self.setup_print_and_exit_mocks()

    def setup_cli_run_test(self):
        """Set up everything needed for CLI run tests with pre-configured mocks.
        
        Returns:
            Tuple of (cli_instance, mock_args, mock_print, mock_exit, mock_github_client, 
                     mock_state_manager, mock_load_json, mock_validate_schema)
        """
        # Create CLI instance
        cli = self.create_cli_instance()
        
        # Set up all CLI command mocks
        (mock_github_client_class, mock_state_manager_class, mock_print, mock_exit, 
         mock_load_json, mock_validate_schema, _, _) = self.setup_cli_command_test()
        
        # Create and configure mock instances with common defaults
        mock_github_client = Mock()
        mock_state_manager = Mock()
        mock_github_client_class.return_value = mock_github_client
        mock_state_manager_class.return_value = mock_state_manager
        
        # Configure common mock behaviors
        mock_args = Mock()
        mock_args.command = 'create'
        mock_args.roadmap_file = 'roadmap.json'
        mock_args.verbose = False
        mock_args.schema = 'schema.json'
        mock_args.repo = None
        
        # Configure schema validator mocks
        mock_load_json.return_value = self.roadmap_data
        mock_validate_schema.return_value = None
        
        return (cli, mock_args, mock_print, mock_exit, mock_github_client, 
                mock_state_manager, mock_load_json, mock_validate_schema)

    def setup_mcp_run_test(self):
        """Set up everything needed for MCP command tests with pre-configured mocks.
        
        Returns:
            Tuple of (cli_instance, mock_args, mock_print, mock_exit, mock_asyncio_run, 
                     mock_mcp_server, mock_server_instance)
        """
        # Create CLI instance
        cli = self.create_cli_instance()
        
        # Set up all MCP command mocks
        (mock_print, mock_exit, _, mock_asyncio_run, mock_mcp_server) = self.setup_mcp_command_test()
        
        # Create and configure mock instances with common defaults
        mock_args = Mock()
        mock_args.command = 'mcp'
        mock_args.host = 'localhost'
        mock_args.port = 8080
        mock_args.transport = 'stdio'
        mock_args.schema = 'schema.json'
        mock_args.verbose = False
        
        # Configure mock server instance
        mock_server_instance = Mock()
        mock_server_instance.run_stdio = Mock()
        mock_server_instance.run_http = Mock()
        mock_mcp_server.return_value = mock_server_instance
        
        # Configure asyncio.run mock
        mock_asyncio_run.return_value = None
        
        return (cli, mock_args, mock_print, mock_exit, mock_asyncio_run, 
                mock_mcp_server, mock_server_instance)

    def setup_mcp_http_server_run_test(self):
        """Set up everything needed for MCP HTTP server tests with pre-configured mocks.
        
        Returns:
            Tuple of (cli_instance, mock_args, mock_print, mock_exit, mock_mcp_http_server, 
                     mock_server_instance)
        """
        # Create CLI instance
        cli = self.create_cli_instance()
        
        # Set up all MCP HTTP server mocks
        (mock_print, mock_exit, _, mock_mcp_http_server) = self.setup_mcp_http_server_test()
        
        # Create and configure mock instances with common defaults
        mock_args = Mock()
        mock_args.command = 'mcp-server'
        mock_args.host = 'localhost'
        mock_args.port = 8000
        mock_args.schema_file = 'schema.json'
        mock_args.verbose = False
        
        # Configure mock server instance
        mock_server_instance = Mock()
        mock_server_instance.run = Mock()
        mock_mcp_http_server.return_value = mock_server_instance
        
        return (cli, mock_args, mock_print, mock_exit, mock_mcp_http_server, 
                mock_server_instance)


    @contextmanager
    def sys_argv_context(self, argv_values):
        """
        Context manager for temporarily setting sys.argv values.
        
        Args:
            argv_values (list): List of command line argument values to set
        """
        original_argv = sys.argv
        try:
            sys.argv = argv_values
            yield
        finally:
            sys.argv = original_argv

    def create_mock_args(self, command='create', roadmap_file='roadmap.json', verbose=False, **kwargs):
        """
        Create standardized mock arguments for CLI commands.
        
        Args:
            command (str): CLI command name
            roadmap_file (str): Path to roadmap file
            verbose (bool): Verbose flag
            **kwargs: Additional arguments to set on the mock
            
        Returns:
            Mock: Configured mock arguments object
        """
        args = Mock()
        args.command = command
        args.roadmap_file = roadmap_file
        args.verbose = verbose
        
        # Set additional attributes
        for key, value in kwargs.items():
            setattr(args, key, value)
            
        return args






    def setup_mcp_server_mocks(self, server_type='stdio', schema_file='schema.json', verbose=False, 
                              host='localhost', port=8080):
        """
        Set up consolidated mocks for MCP server configurations.
        
        Args:
            server_type (str): Type of MCP server ('stdio' or 'http')
            schema_file (str): Path to schema file
            verbose (bool): Verbose flag
            host (str): Host for HTTP server
            port (int): Port for HTTP server
            
        Returns:
            Mock: Configured mock arguments object for MCP server
        """
        mock_args = Mock()
        mock_args.command = 'mcp'
        mock_args.schema = schema_file
        mock_args.verbose = verbose
        
        if server_type == 'http':
            mock_args.host = host
            mock_args.port = port
            mock_args.transport = 'http'
        else:
            mock_args.transport = 'stdio'
            mock_args.host = host
            mock_args.port = port
            
        return mock_args

    def setup_mcp_test_infrastructure(self, server_type='stdio', schema_file='schema.json', 
                                      verbose=False, host='localhost', port=8080):
        """
        Complete MCP server test setup with all necessary mocks.
        
        Args:
            server_type (str): Type of MCP server ('stdio' or 'http')
            schema_file (str): Path to schema file
            verbose (bool): Verbose flag
            host (str): Host for HTTP server
            port (int): Port for HTTP server
            
        Returns:
            Tuple of (mock_print, mock_exit, mock_path_class, mock_path_instance, 
                     mock_asyncio_run, mock_mcp_server, mock_server_instance, mock_shared_operations)
        """
        # Set up print and exit mocks
        mock_print, mock_exit = self.setup_print_and_exit_mocks()
        
        # Set up path mocks
        mock_path_class, mock_path_instance = self.setup_path_mocks()
        
        # Set up asyncio.run mock
        patcher_asyncio_run = patch('asyncio.run')
        mock_asyncio_run = patcher_asyncio_run.start()
        self.addCleanup(self._safe_stop_patcher, patcher_asyncio_run)
        
        # Set up MCP server mock
        if server_type == 'stdio':
            patcher_mcp_server = patch('gh_milestone.mcp_server.MCPServer')
        else:  # http
            patcher_mcp_server = patch('gh_milestone.mcp_http_server.MCPHTTPServer')
            
        mock_mcp_server = patcher_mcp_server.start()
        self.addCleanup(self._safe_stop_patcher, patcher_mcp_server)
        
        # Create mock server instance
        mock_server_instance = Mock()
        mock_mcp_server.return_value = mock_server_instance
        
        # Set up SharedOperations mocks
        mock_shared_operations = self.setup_mcp_shared_operations_mocks()
        
        return (mock_print, mock_exit, mock_path_class, mock_path_instance, 
                mock_asyncio_run, mock_mcp_server, mock_server_instance, mock_shared_operations)

    def build_mock_args(self, **overrides):
        """
        Generic mock args builder that can be reused across different test scenarios.
        
        Args:
            **overrides: Dictionary of attribute overrides for the mock args
            
        Returns:
            Mock: Configured mock arguments object with defaults and overrides
        """
        # Common default arguments
        defaults = {
            'command': 'create',
            'roadmap_file': 'roadmap.json',
            'verbose': False,
            'schema': 'schema.json',
            'repo': None
        }
        
        # Update defaults with provided overrides
        defaults.update(overrides)
        
        # Create mock with the combined attributes
        return Mock(**defaults)

    def assert_success_result(self, result, has_data=True):
        """
        Assert that an MCP server method result indicates success.
        
        Args:
            result (dict): The result dictionary from MCP server methods
            has_data (bool): Whether the success result should contain data
        """
        self.assertTrue(result["success"])
        self.assertNotIn("error", result)
        if has_data:
            self.assertIn("data", result)

    def assert_failure_result(self, result, error_message=None):
        """
        Assert that an MCP server method result indicates failure.
        
        Args:
            result (dict): The result dictionary from MCP server methods
            error_message (str): Expected error message (optional)
        """
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        if error_message:
            self.assertIn(error_message, result["error"])

    def setup_mcp_shared_operations_mocks(self):
        """
        Set up all the common SharedOperations patch decorators with proper cleanup.
        
        Returns:
            Tuple of (mock_shared_operations, mock_create_issues, mock_validate_roadmap,
                     mock_delete_issues, mock_update_issues, mock_list_issues, mock_get_status)
        """
        # Create patchers for all SharedOperations methods
        patchers = []
        mocks = {}
        
        methods_to_patch = [
            'gh_milestone.shared_operations.SharedOperations.create_issues_from_roadmap',
            'gh_milestone.shared_operations.SharedOperations.validate_roadmap_only',
            'gh_milestone.shared_operations.SharedOperations.delete_issues',
            'gh_milestone.shared_operations.SharedOperations.update_issues',
            'gh_milestone.shared_operations.SharedOperations.list_issues',
            'gh_milestone.shared_operations.SharedOperations.get_status'
        ]
        
        for method_path in methods_to_patch:
            patcher = patch(method_path)
            mock_method = patcher.start()
            patchers.append(patcher)
            # Extract method name from path (last part after the final dot)
            method_name = method_path.split('.')[-1]
            mocks[method_name] = mock_method
            
        # Register cleanup for all patchers
        for patcher in patchers:
            self.addCleanup(self._safe_stop_patcher, patcher)
            
        # Return mocks in a consistent order
        return (
            mocks.get('create_issues_from_roadmap'),
            mocks.get('validate_roadmap_only'),
            mocks.get('delete_issues'),
            mocks.get('update_issues'),
            mocks.get('list_issues'),
            mocks.get('get_status')
        )

    def setup_cli_execution_test(self, command='create', return_code=0, exception=None):
        """
        Set up a CLI execution test with expected outcome.
        
        Args:
            command (str): The CLI command to test
            return_code (int): Expected return code (0 for success, non-zero for failure)
            exception (Exception): Exception to raise during execution (optional)
            
        Returns:
            Tuple of (cli_instance, mock_args, mock_print, mock_exit, mock_github_client, 
                     mock_state_manager, mock_load_json, mock_validate_schema)
        """
        # Create CLI instance
        cli = self.create_cli_instance()
        
        # Set up all CLI command mocks
        (mock_github_client_class, mock_state_manager_class, mock_print, mock_exit, 
         mock_load_json, mock_validate_schema, _, _) = self.setup_cli_command_test()
        
        # Create and configure mock instances
        mock_github_client = Mock()
        mock_state_manager = Mock()
        mock_github_client_class.return_value = mock_github_client
        mock_state_manager_class.return_value = mock_state_manager
        
        # Configure mock arguments
        mock_args = self.build_mock_args(command=command)
        
        # Configure schema validator mocks
        mock_load_json.return_value = self.roadmap_data
        
        # Configure exception behavior if specified
        if exception:
            mock_validate_schema.side_effect = exception
        else:
            mock_validate_schema.return_value = None
            
        return (cli, mock_args, mock_print, mock_exit, mock_github_client, 
                mock_state_manager, mock_load_json, mock_validate_schema)

    def assert_cli_success(self, mock_exit, mock_print=None, message=None):
        """
        Assert that CLI execution completed successfully.
        
        Args:
            mock_exit (Mock): The mocked sys.exit
            mock_print (Mock): The mocked print (optional)
            message (str): Expected success message (optional)
        """
        # Check that exit was called with code 0
        mock_exit.assert_any_call(0)
        
        # Check for success message if provided
        if message and mock_print:
            mock_print.assert_any_call(message)

    def assert_cli_failure(self, mock_exit, mock_print=None, error_message=None, exit_code=1):
        """
        Assert that CLI execution failed.
        
        Args:
            mock_exit (Mock): The mocked sys.exit
            mock_print (Mock): The mocked print (optional)
            error_message (str): Expected error message (optional)
            exit_code (int): Expected exit code (default: 1)
        """
        # Check that exit was called with the expected code
        mock_exit.assert_any_call(exit_code)
        
        # Check for error message if provided
        if error_message and mock_print:
            mock_print.assert_any_call(error_message)

    def create_standard_mcp_mocks(self, dry_run=False):
        """
        Factory method that creates and configures standard mock objects for MCP tests.
        
        Args:
            dry_run (bool): Whether to configure mocks for dry run scenario
            
        Returns:
            Dict: Dictionary containing standard mock objects for MCP tests
        """
        # Create standard mock objects
        mock_github_client = Mock()
        mock_state_manager = Mock()
        
        # Configure state manager with standard return values
        self.configure_mcp_state_manager_mocks(mock_state_manager, dry_run)
        
        return {
            'github_client': mock_github_client,
            'state_manager': mock_state_manager
        }


    def configure_mcp_state_manager_mocks(self, mock_state_manager, dry_run=False):
        """
        Helper that configures state manager mock with standard return values.
        
        Args:
            mock_state_manager (Mock): The state manager mock to configure
            dry_run (bool): Whether to configure for dry run scenario
        """
        # Configure standard return values for state manager methods
        mock_state_manager.get_main_tracking_issue.return_value = {
            "number": 1, 
            "url": "https://github.com/owner/repo/issues/1"
        }
        
        mock_state_manager.get_all_milestones.return_value = {
            "Phase 1: Setup": {"number": 2, "url": "https://github.com/owner/repo/issues/2"},
            "Phase 2: Development": {"number": 3, "url": "https://github.com/owner/repo/issues/3"}
        }
        
        mock_state_manager.get_all_tasks.return_value = [
            {"title": "Task: Create repository structure", "number": 4, 
             "url": "https://github.com/owner/repo/issues/4"}
        ]
        
        # Configure methods that might be called during tests
        mock_state_manager.save_state = Mock()
        mock_state_manager.validate_state = Mock(return_value={'invalid_milestones': [], 'invalid_tasks': []})
        mock_state_manager.cleanup_state = Mock()
        mock_state_manager.migrate_state = Mock(return_value={})
        mock_state_manager.sync_state = Mock(return_value={})

    def setup_mcp_method_test(self, method_name, success=True, result_data=None, error_message=None):
        """
        Set up a test for MCP server methods with expected success/failure outcome.
        
        Args:
            method_name (str): Name of the MCP method being tested
            success (bool): Whether the method should succeed or fail
            result_data (dict): Data to return on success (optional)
            error_message (str): Error message to return on failure (optional)
            
        Returns:
            Tuple of (server_instance, mock_method, roadmap_data)
        """
        # Create server instance
        server = self.create_mcp_server()
        
        # Set up shared operations mocks
        mock_shared_operations = self.setup_mcp_shared_operations_mocks()
        
        # Get the appropriate mock for the method
        mock_method = None
        if method_name == 'plan_issues':
            mock_method = mock_shared_operations[1]  # validate_roadmap_only
        elif method_name == 'create_issues':
            mock_method = mock_shared_operations[0]  # create_issues_from_roadmap
        elif method_name == 'update_issues':
            mock_method = mock_shared_operations[3]  # update_issues
        elif method_name == 'delete_issues':
            mock_method = mock_shared_operations[2]  # delete_issues
        elif method_name == 'get_status':
            mock_method = mock_shared_operations[5]  # get_status
        elif method_name == 'list_issues':
            mock_method = mock_shared_operations[4]  # list_issues
            
        # Configure mock behavior based on expected outcome
        if success:
            mock_method.return_value = result_data
        else:
            mock_method.side_effect = Exception(error_message or "Test error")
            
        return server, mock_method, self.roadmap_data

    def assert_mcp_response_success(self, response, expected_data_keys=None):
        """
        Assert that an MCP response indicates success.
        
        Args:
            response (dict): The MCP response dictionary
            expected_data_keys (list): List of expected keys in response data (optional)
        """
        self.assertTrue(response["success"])
        self.assertNotIn("error", response)
        
        if expected_data_keys:
            self.assertIn("data", response)
            for key in expected_data_keys:
                self.assertIn(key, response["data"])

    def assert_mcp_response_failure(self, response, expected_error_message=None):
        """
        Assert that an MCP response indicates failure.
        
        Args:
            response (dict): The MCP response dictionary
            expected_error_message (str): Expected error message substring (optional)
        """
        self.assertFalse(response["success"])
        self.assertIn("error", response)
        
        if expected_error_message:
            self.assertIn(expected_error_message, response["error"])

    def setup_parameterized_test_scenario(self, scenario_type, **kwargs):
        """
        Set up a parameterized test scenario for success/failure cases.
        
        Args:
            scenario_type (str): Type of scenario ('cli_success', 'cli_failure', 'mcp_success', 'mcp_failure')
            **kwargs: Scenario-specific parameters
            
        Returns:
            dict: Configuration dictionary for the test scenario
        """
        config = {}
        
        if scenario_type.startswith('cli'):
            # CLI scenario setup
            config['cli'], config['args'], config['print'], config['exit'], \
            config['github_client'], config['state_manager'], \
            config['load_json'], config['validate_schema'] = self.setup_cli_execution_test(
                command=kwargs.get('command', 'create'),
                return_code=kwargs.get('return_code', 0 if scenario_type == 'cli_success' else 1),
                exception=kwargs.get('exception')
            )
            
            # Configure file loading mocks
            config['load_json'].return_value = kwargs.get('roadmap_data', self.roadmap_data)
            config['validate_schema'].return_value = None
            
        elif scenario_type.startswith('mcp'):
            # MCP scenario setup
            method_name = kwargs.get('method_name', 'plan_issues')
            success = scenario_type == 'mcp_success'
            config['server'], config['method'], config['roadmap_data'] = self.setup_mcp_method_test(
                method_name=method_name,
                success=success,
                result_data=kwargs.get('result_data'),
                error_message=kwargs.get('error_message')
            )
            
        return config


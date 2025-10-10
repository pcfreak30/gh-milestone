import unittest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from tests.test_data_factory import TestDataFactory
from tests.test_base import BaseTestCase
from gh_milestone.mcp_server import MCPServer
from gh_milestone.mcp_http_server import MCPHTTPServer


class MCPTestBase(BaseTestCase):
    """Base class for MCP server tests with common setup methods."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        super().setUp()
        self.schema_file = "schema.json"
        self.roadmap_file = "test_roadmap.json"
        self.server = None
    
    def create_mcp_server(self, verbose=False):
        """Create MCPServer instance."""
        if self.server is None:
            self.server = MCPServer(schema_file=self.schema_file, verbose=verbose)
        return self.server
    
    def create_mcp_http_server(self, verbose=False):
        """Create MCPHTTPServer instance."""
        if self.server is None:
            self.server = MCPHTTPServer(schema_file=self.schema_file, verbose=verbose)
        return self.server
    
    def setup_mcp_test(self, server_type='stdio'):
        """Set up common MCP test infrastructure."""
        return self.setup_mcp_test_infrastructure(server_type=server_type, schema_file=self.schema_file)



class TestMCPServer(MCPTestBase):
    """Test cases for the MCPServer class."""

    def test_init(self):
        """Test MCPServer initialization."""
        server = self.create_mcp_server()
        self.assertEqual(server.schema_file, self.schema_file)
        self.assertFalse(server.verbose)
        self.assertIsNotNone(server.server)
        self.assertIsNotNone(server.cli)
        
        # Test with verbose=True
        verbose_server = MCPServer(schema_file=self.schema_file, verbose=True)
        self.assertTrue(verbose_server.verbose)

    async def test_plan_issues_success(self):
        """Test plan_issues method with valid roadmap."""
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Use shared operations mocks
        mock_validate_roadmap = self.setup_mcp_shared_operations_mocks()[1]
        mock_validate_roadmap.return_value = None

        result = await self.create_mcp_server().plan_issues(roadmap_data)

        self.assertTrue(result["success"])
        self.assertIn("plan", result)
        self.assertEqual(result["plan"]["project"], "Test Project")
        self.assertEqual(result["plan"]["total_milestones"], 2)

    async def test_plan_issues_validation_error(self):
        """Test plan_issues method with invalid roadmap."""
        roadmap_data = {"invalid": "data"}
        
        # Use shared operations mocks
        mock_validate_roadmap = self.setup_mcp_shared_operations_mocks()[1]
        mock_validate_roadmap.side_effect = Exception("Validation failed")

        result = await self.create_mcp_server().plan_issues(roadmap_data)

        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("Validation failed", result["error"])

    async def _test_operation_dry_run_vs_actual(self, operation_name, dry_run_message, actual_run_message):
        """Helper to test dry run vs actual run scenarios for operations."""
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Use test infrastructure setup
        (_, _, _, _, _, _, _, mock_shared_operations) = self.setup_mcp_test()
        mock_operation = mock_shared_operations[operation_name]
        mock_operation.return_value = None

        # Test dry run
        result_dry = await self.create_mcp_server().execute_operation(roadmap_data, dry_run=True)
        self.assertTrue(result_dry["success"])
        self.assertTrue(result_dry["dry_run"])
        self.assertIn(dry_run_message, result_dry["message"])

        # Test actual run
        result_actual = await self.create_mcp_server().execute_operation(roadmap_data, dry_run=False)
        self.assertTrue(result_actual["success"])
        self.assertFalse(result_actual.get("dry_run", False))
        self.assertIn(actual_run_message, result_actual["message"])

    async def test_create_issues_dry_run_vs_actual(self):
        """Test create_issues method with dry_run vs actual run."""
        await self._test_operation_dry_run_vs_actual(
            'create_issues_from_roadmap', 
            "Dry run", 
            "created successfully"
        )

    async def test_update_issues_dry_run_vs_actual(self):
        """Test update_issues method with dry_run vs actual run."""
        await self._test_operation_dry_run_vs_actual(
            'update_issues', 
            "Would update issues", 
            "updated successfully"
        )

    async def test_delete_issues_dry_run_vs_actual(self):
        """Test delete_issues method with dry_run vs actual run."""
        await self._test_operation_dry_run_vs_actual(
            'delete_issues', 
            "Would delete", 
            "Deleted"
        )

    async def _test_operation_success_vs_failure(self, operation_name, method_name, *args):
        """Helper to test success vs failure scenarios for operations."""
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Use test infrastructure setup
        (_, _, _, _, _, _, _, mock_shared_operations) = self.setup_mcp_test()
        mock_operation = mock_shared_operations[operation_name]
        
        # Test success case
        mock_operation.return_value = None
        server = self.create_mcp_server()
        method = getattr(server, method_name)
        result_success = await method(*args)
        self.assert_success_result(result_success, has_data=(operation_name in ['list_issues', 'get_status']))

        # Test failure case
        mock_operation.side_effect = Exception("Operation failed")
        result_failure = await method(*args)
        self.assert_failure_result(result_failure, "Operation failed")

    async def test_get_status_success_vs_failure(self):
        """Test get_status method success vs failure scenarios."""
        await self._test_operation_success_vs_failure('get_status', 'get_status', self.roadmap_file)

    async def test_list_issues_success_vs_failure(self):
        """Test list_issues method success vs failure scenarios."""
        await self._test_operation_success_vs_failure('list_issues', 'list_issues', self.roadmap_file)

    async def test_run_stdio_success(self):
        """Test run_stdio method with successful execution."""
        # Use test infrastructure setup
        (mock_print, mock_exit, mock_path_class, mock_path_instance, 
         mock_asyncio_run, mock_mcp_server, mock_server_instance, _) = self.setup_mcp_test()
        
        # Mock the stdio_server context manager
        mock_read_stream = Mock()
        mock_write_stream = Mock()
        mock_stdio_server = patch('gh_milestone.mcp_server.stdio_server')
        mock_stdio_server.start()
        self.addCleanup(self._safe_stop_patcher, mock_stdio_server)
        mock_stdio_server.return_value.__aenter__.return_value = (mock_read_stream, mock_write_stream)
        mock_stdio_server.return_value.__aexit__.return_value = None
        
        # Mock the server.run method as an awaitable
        server = self.create_mcp_server()
        server.server.run = AsyncMock()
        
        await server.run_stdio()
        
        # Verify that stdio_server was called as a context manager
        mock_stdio_server.assert_called_once()
        
        # Verify that server.run was called with correct streams
        server.server.run.assert_called_once_with(mock_read_stream, mock_write_stream)

    async def test_run_stdio_exception(self):
        """Test run_stdio method with exception during execution."""
        # Use test infrastructure setup
        (mock_print, mock_exit, mock_path_class, mock_path_instance, 
         mock_asyncio_run, mock_mcp_server, mock_server_instance, _) = self.setup_mcp_test()
        
        # Mock the stdio_server context manager
        mock_read_stream = Mock()
        mock_write_stream = Mock()
        mock_stdio_server = patch('gh_milestone.mcp_server.stdio_server')
        mock_stdio_server.start()
        self.addCleanup(self._safe_stop_patcher, mock_stdio_server)
        mock_stdio_server.return_value.__aenter__.return_value = (mock_read_stream, mock_write_stream)
        mock_stdio_server.return_value.__aexit__.return_value = None
        
        # Mock the server.run method to raise an exception
        test_exception = Exception("Test exception")
        server = self.create_mcp_server()
        server.server.run = AsyncMock(side_effect=test_exception)
        
        with self.assertRaises(Exception) as context:
            await server.run_stdio()
        
        self.assertEqual(context.exception, test_exception)

    async def test_run_http_not_implemented(self):
        """Test run_http method raises NotImplementedError."""
        server = self.create_mcp_server()
        with self.assertRaises(NotImplementedError) as context:
            await server.run_http()
        
        self.assertIn("HTTP transport not yet implemented", str(context.exception))


class TestMCPHTTPServer(MCPTestBase):
    """Test cases for the MCPHTTPServer class."""

    def test_init(self):
        """Test MCPHTTPServer initialization."""
        server = self.create_mcp_http_server()
        self.assertEqual(server.schema_file, self.schema_file)
        self.assertFalse(server.verbose)
        self.assertIsNotNone(server.app)
        
        # Test with verbose=True
        verbose_server = MCPHTTPServer(schema_file=self.schema_file, verbose=True)
        self.assertTrue(verbose_server.verbose)

    def test_run_method(self):
        """Test run method creates and starts server."""
        # Use test infrastructure setup
        (mock_print, mock_exit, mock_path_class, mock_path_instance, 
         mock_asyncio_run, mock_mcp_server, mock_server_instance, _) = self.setup_mcp_test(server_type='http')
        
        # Create CLI instance and patch its _load_aliases method
        cli = self.create_cli_instance()
        # Patch CLI._load_aliases to return empty dict to avoid Path operations
        with patch.object(cli, '_load_aliases', return_value={}):
            server = self.create_mcp_http_server()
            self.assertIsNotNone(server.app)


class TestMCPTools(MCPTestBase):
    """Test cases for individual MCP tools."""

    def _test_tool_schema(self, tool_method, expected_name, required_fields):
        """Helper method to test tool schema properties."""
        tool = getattr(self.create_mcp_server(), tool_method)()
        self.assertEqual(tool.name, expected_name)
        
        for field in required_fields:
            self.assertIn(field, tool.inputSchema["properties"])
            self.assertIn(field, tool.inputSchema["required"])

    def test_tool_schemas(self):
        """Test all MCP tool schemas using parameterized testing."""
        test_cases = [
            ('plan_issues_tool', 'plan_issues', ['roadmap_data']),
            ('validate_roadmap_tool', 'validate_roadmap', ['roadmap_data']),
            ('create_issues_tool', 'create_issues', ['roadmap_data']),
            ('get_status_tool', 'get_status', ['roadmap_file']),
            ('list_issues_tool', 'list_issues', ['roadmap_file']),
            ('update_issues_tool', 'update_issues', ['roadmap_data']),
            ('delete_issues_tool', 'delete_issues', ['roadmap_data'])
        ]
        
        for tool_method, expected_name, required_fields in test_cases:
            with self.subTest(tool_method=tool_method):
                self._test_tool_schema(tool_method, expected_name, required_fields)


if __name__ == '__main__':
    unittest.main()

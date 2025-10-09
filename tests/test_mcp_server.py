import unittest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from tests.test_data_factory import TestDataFactory
from gh_milestone.mcp_server import MCPServer
from gh_milestone.mcp_http_server import MCPHTTPServer


class TestMCPServer(unittest.IsolatedAsyncioTestCase):
    """Test cases for the MCPServer class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.schema_file = "schema.json"
        self.server = MCPServer(schema_file=self.schema_file, verbose=False)

    def test_init(self):
        """Test MCPServer initialization."""
        server = MCPServer(schema_file=self.schema_file, verbose=True)
        self.assertEqual(server.schema_file, self.schema_file)
        self.assertTrue(server.verbose)
        self.assertIsNotNone(server.server)
        self.assertIsNotNone(server.cli)

    @patch('gh_milestone.mcp_server.SharedOperations.validate_roadmap_only')
    async def test_plan_issues_success(self, mock_validate):
        """Test plan_issues method with valid roadmap."""
        roadmap_data = TestDataFactory.create_roadmap()

        # Mock validation to succeed
        mock_validate.return_value = None

        result = await self.server.plan_issues(roadmap_data)

        self.assertTrue(result["success"])
        self.assertIn("plan", result)
        self.assertEqual(result["plan"]["project"], "Test Project")
        self.assertEqual(result["plan"]["total_milestones"], 2)

    @patch('gh_milestone.mcp_server.SharedOperations.validate_roadmap_only')
    async def test_plan_issues_validation_error(self, mock_validate):
        """Test plan_issues method with invalid roadmap."""
        roadmap_data = {"invalid": "data"}

        # Mock validation to raise exception
        mock_validate.side_effect = Exception("Validation failed")

        result = await self.server.plan_issues(roadmap_data)

        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("Validation failed", result["error"])

    @patch('gh_milestone.mcp_server.SharedOperations.validate_roadmap_only')
    @patch('gh_milestone.mcp_server.CLI._common_setup')
    @patch('gh_milestone.mcp_server.SharedOperations.create_issues_from_roadmap')
    async def test_create_issues_dry_run(self, mock_create, mock_setup, mock_validate):
        """Test create_issues method with dry_run=True."""
        roadmap_data = TestDataFactory.create_roadmap()

        # Mock validation to succeed
        mock_validate.return_value = None

        result = await self.server.create_issues(roadmap_data, dry_run=True)

        self.assertTrue(result["success"])
        self.assertTrue(result["dry_run"])
        self.assertIn("Dry run", result["message"])

    @patch('gh_milestone.mcp_server.SharedOperations.validate_roadmap_only')
    @patch('gh_milestone.mcp_server.CLI._common_setup')
    @patch('gh_milestone.mcp_server.SharedOperations.create_issues_from_roadmap')
    async def test_create_issues_actual_run(self, mock_create, mock_setup, mock_validate):
        """Test create_issues method with dry_run=False."""
        roadmap_data = TestDataFactory.create_roadmap()

        # Mock setup to return fake objects
        mock_github_client = Mock()
        mock_state_manager = Mock()
        mock_state_manager.get_main_tracking_issue.return_value = {
            "number": 1, "url": "https://github.com/owner/repo/issues/1"
        }
        mock_state_manager.get_all_milestones.return_value = {
            "Phase 1: Setup": {"number": 2, "url": "https://github.com/owner/repo/issues/2"},
            "Phase 2: Development": {"number": 3, "url": "https://github.com/owner/repo/issues/3"}
        }
        mock_state_manager.get_all_tasks.return_value = [
            {"title": "Task: Create repository structure", "number": 4, "url": "https://github.com/owner/repo/issues/4"}
        ]

        mock_setup.return_value = (mock_github_client, mock_state_manager, roadmap_data)

        # Mock validation to succeed
        mock_validate.return_value = None

        result = await self.server.create_issues(roadmap_data, dry_run=False)

        self.assertTrue(result["success"])
        self.assertFalse(result.get("dry_run", False))
        self.assertIn("created successfully", result["message"])

    @patch('gh_milestone.mcp_server.CLI._common_setup')
    @patch('gh_milestone.mcp_server.SharedOperations.get_status')
    async def test_get_status_success(self, mock_get_status, mock_setup):
        """Test get_status method."""
        roadmap_file = "test_roadmap.json"

        # Mock status result
        status_result = {
            "project": "Test Project",
            "milestones": 2,
            "tasks": 4,
            "completed": 0
        }
        mock_get_status.return_value = status_result

        # Mock setup to return fake objects
        mock_github_client = Mock()
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        mock_setup.return_value = (mock_github_client, mock_state_manager, roadmap_data)

        result = await self.server.get_status(roadmap_file)

        self.assertTrue(result["success"])
        self.assertNotIn("error", result)

    @patch('gh_milestone.mcp_server.CLI._common_setup')
    async def test_get_status_failure(self, mock_setup):
        """Test get_status method with failure."""
        roadmap_file = "test_roadmap.json"

        # Mock setup to raise exception
        mock_setup.side_effect = Exception("Setup failed")

        result = await self.server.get_status(roadmap_file)

        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("Setup failed", result["error"])

    @patch('gh_milestone.mcp_server.CLI._common_setup')
    @patch('gh_milestone.mcp_server.SharedOperations.list_issues')
    async def test_list_issues_success(self, mock_list_issues, mock_setup):
        """Test list_issues method."""
        roadmap_file = "test_roadmap.json"
        format_type = "json"
        show_missing = False

        # Mock list result
        list_result = {
            "project": "Test Project",
            "milestones": [
                {"title": "Phase 1: Setup", "number": 1},
                {"title": "Phase 2: Development", "number": 2}
            ]
        }
        mock_list_issues.return_value = list_result

        # Mock setup to return fake objects
        mock_github_client = Mock()
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        mock_setup.return_value = (mock_github_client, mock_state_manager, roadmap_data)

        result = await self.server.list_issues(roadmap_file, format_type, show_missing)

        self.assertTrue(result["success"])
        self.assertEqual(result["data"], list_result)

    @patch('gh_milestone.mcp_server.CLI._common_setup')
    async def test_list_issues_failure(self, mock_setup):
        """Test list_issues method with failure."""
        roadmap_file = "test_roadmap.json"

        # Mock setup to raise exception
        mock_setup.side_effect = Exception("Setup failed")

        result = await self.server.list_issues(roadmap_file)

        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("Setup failed", result["error"])

    @patch('gh_milestone.mcp_server.SharedOperations.validate_roadmap_only')
    @patch('gh_milestone.mcp_server.CLI._common_setup')
    @patch('gh_milestone.mcp_server.SharedOperations.update_all_issues')
    async def test_update_issues_dry_run(self, mock_update_all, mock_setup, mock_validate):
        """Test update_issues method with dry_run=True."""
        roadmap_data = TestDataFactory.create_roadmap()

        # Mock validation to succeed
        mock_validate.return_value = None

        result = await self.server.update_issues(roadmap_data, dry_run=True)

        self.assertTrue(result["success"])
        self.assertTrue(result["dry_run"])
        self.assertIn("Would update issues", result["message"])

    @patch('gh_milestone.mcp_server.SharedOperations.validate_roadmap_only')
    @patch('gh_milestone.mcp_server.CLI._common_setup')
    @patch('gh_milestone.mcp_server.SharedOperations.update_all_issues')
    async def test_update_issues_actual_run(self, mock_update_all, mock_setup, mock_validate):
        """Test update_issues method with dry_run=False."""
        roadmap_data = TestDataFactory.create_roadmap()

        # Mock setup to return fake objects
        mock_github_client = Mock()
        mock_state_manager = Mock()
        mock_setup.return_value = (mock_github_client, mock_state_manager, roadmap_data)

        # Mock validation to succeed
        mock_validate.return_value = None

        result = await self.server.update_issues(roadmap_data, dry_run=False)

        self.assertTrue(result["success"])
        self.assertFalse(result.get("dry_run", False))
        self.assertIn("updated successfully", result["message"])

    @patch('gh_milestone.mcp_server.SharedOperations.validate_roadmap_only')
    @patch('gh_milestone.mcp_server.CLI._common_setup')
    @patch('gh_milestone.mcp_server.SharedOperations.delete_all_milestones')
    async def test_delete_issues_dry_run(self, mock_delete_all, mock_setup, mock_validate):
        """Test delete_issues method with dry_run=True."""
        roadmap_data = TestDataFactory.create_roadmap()

        # Mock validation to succeed
        mock_validate.return_value = None

        result = await self.server.delete_issues(roadmap_data, dry_run=True)

        self.assertTrue(result["success"])
        self.assertTrue(result["dry_run"])
        self.assertIn("Would delete", result["message"])

    @patch('gh_milestone.mcp_server.SharedOperations.validate_roadmap_only')
    @patch('gh_milestone.mcp_server.CLI._common_setup')
    @patch('gh_milestone.mcp_server.SharedOperations.delete_all_milestones')
    async def test_delete_issues_actual_run(self, mock_delete_all, mock_setup, mock_validate):
        """Test delete_issues method with dry_run=False."""
        roadmap_data = TestDataFactory.create_roadmap()

        # Mock setup to return fake objects
        mock_github_client = Mock()
        mock_state_manager = Mock()
        mock_setup.return_value = (mock_github_client, mock_state_manager, roadmap_data)

        # Mock validation to succeed
        mock_validate.return_value = None

        result = await self.server.delete_issues(roadmap_data, dry_run=False)

        self.assertTrue(result["success"])
        self.assertFalse(result.get("dry_run", False))
        self.assertIn("Deleted", result["message"])


class TestMCPHTTPServer(unittest.TestCase):
    """Test cases for the MCPHTTPServer class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.schema_file = "schema.json"
        self.server = MCPHTTPServer(schema_file=self.schema_file, verbose=False)

    def test_init(self):
        """Test MCPHTTPServer initialization."""
        server = MCPHTTPServer(schema_file=self.schema_file, verbose=True)
        self.assertEqual(server.schema_file, self.schema_file)
        self.assertTrue(server.verbose)
        self.assertIsNotNone(server.app)

    @patch('gh_milestone.mcp_http_server.MCPServer')
    def test_run_method(self, mock_mcp_server):
        """Test run method creates and starts server."""
        mock_server_instance = Mock()
        mock_mcp_server.return_value = mock_server_instance

        # This would normally start the server, but we're just testing initialization
        server = MCPHTTPServer(schema_file=self.schema_file, verbose=False)
        self.assertIsNotNone(server.app)
        # Check that MCPServer was called with positional arguments
        mock_mcp_server.assert_called_once_with(self.schema_file, False)


class TestMCPTools(unittest.TestCase):
    """Test cases for individual MCP tools."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mcp_server = MCPServer(schema_file="schema.json")

    def test_plan_issues_tool(self):
        """Test plan_issues_tool method."""
        tool = self.mcp_server.plan_issues_tool()
        self.assertEqual(tool.name, "plan_issues")
        self.assertIn("roadmap_data", tool.inputSchema["properties"])
        self.assertIn("roadmap_data", tool.inputSchema["required"])

    def test_validate_roadmap_tool(self):
        """Test validate_roadmap_tool method."""
        tool = self.mcp_server.validate_roadmap_tool()
        self.assertEqual(tool.name, "validate_roadmap")
        self.assertIn("roadmap_data", tool.inputSchema["properties"])
        self.assertIn("roadmap_data", tool.inputSchema["required"])

    def test_create_issues_tool(self):
        """Test create_issues_tool method."""
        tool = self.mcp_server.create_issues_tool()
        self.assertEqual(tool.name, "create_issues")
        self.assertIn("roadmap_data", tool.inputSchema["properties"])
        self.assertIn("roadmap_data", tool.inputSchema["required"])
        self.assertIn("dry_run", tool.inputSchema["properties"])

    def test_get_status_tool(self):
        """Test get_status_tool method."""
        tool = self.mcp_server.get_status_tool()
        self.assertEqual(tool.name, "get_status")
        self.assertIn("roadmap_file", tool.inputSchema["properties"])
        self.assertIn("roadmap_file", tool.inputSchema["required"])

    def test_list_issues_tool(self):
        """Test list_issues_tool method."""
        tool = self.mcp_server.list_issues_tool()
        self.assertEqual(tool.name, "list_issues")
        self.assertIn("roadmap_file", tool.inputSchema["properties"])
        self.assertIn("roadmap_file", tool.inputSchema["required"])
        self.assertIn("format", tool.inputSchema["properties"])
        self.assertIn("show_missing", tool.inputSchema["properties"])

    def test_update_issues_tool(self):
        """Test update_issues_tool method."""
        tool = self.mcp_server.update_issues_tool()
        self.assertEqual(tool.name, "update_issues")
        self.assertIn("roadmap_data", tool.inputSchema["properties"])
        self.assertIn("roadmap_data", tool.inputSchema["required"])
        self.assertIn("dry_run", tool.inputSchema["properties"])

    def test_delete_issues_tool(self):
        """Test delete_issues_tool method."""
        tool = self.mcp_server.delete_issues_tool()
        self.assertEqual(tool.name, "delete_issues")
        self.assertIn("roadmap_data", tool.inputSchema["properties"])
        self.assertIn("roadmap_data", tool.inputSchema["required"])
        self.assertIn("dry_run", tool.inputSchema["properties"])


if __name__ == '__main__':
    unittest.main()

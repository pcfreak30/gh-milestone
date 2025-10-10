"""
MCP Server implementation for GitHub Milestone CLI.
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import asyncio
from .cli import CLI
from .github_client import GitHubClient
from .state_manager import StateManager
from .schema_validator import SchemaValidator
from .shared_operations import SharedOperations
from .config import Config

class MCPServer:
    """MCP Server with GitHub Milestone CLI."""
    
    def __init__(self, schema_file: str = Config.DEFAULT_SCHEMA_FILE, verbose: bool = False):
        """Initialize MCP server with tools."""
        # Ensure schema file exists
        if not os.path.exists(schema_file):
            # Try to find it relative to the current file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            schema_path = os.path.join(parent_dir, "schema.json")
            if os.path.exists(schema_path):
                self.schema_file = schema_path
            else:
                raise FileNotFoundError(f"Schema file '{schema_file}' not found.")
        else:
            self.schema_file = schema_file
            
        self.verbose = verbose
        self.server = Server("gh-milestone-cli")
        self.cli = CLI()
        self._register_tools()
    
    def _register_tools(self):
        """Register all MCP tools."""
        # Set up tool handlers - the MCP server will call these when tools are invoked
        self.server.list_tools = self._list_tools
        self.server.call_tool = self._call_tool
    
    async def _list_tools(self):
        """List all available tools."""
        tools = [
            self.plan_issues_tool(),
            self.validate_roadmap_tool(),
            self.create_issues_tool(),
            self.get_status_tool(),
            self.list_issues_tool(),
            self.update_issues_tool(),
            self.delete_issues_tool()
        ]
        return tools
    
    async def _call_tool(self, name: str, arguments: Dict[str, Any]):
        """Handle tool calls."""
        if name == "plan_issues":
            return await self.plan_issues(arguments.get("roadmap_data"))
        elif name == "validate_roadmap":
            return await self.validate_roadmap(arguments.get("roadmap_data"))
        elif name == "create_issues":
            return await self.create_issues(
                arguments.get("roadmap_data"),
                arguments.get("dry_run", False)
            )
        elif name == "get_status":
            return await self.get_status(arguments.get("roadmap_file"))
        elif name == "list_issues":
            return await self.list_issues(
                arguments.get("roadmap_file"),
                arguments.get("format", "json"),
                arguments.get("show_missing", False)
            )
        elif name == "update_issues":
            return await self.update_issues(
                arguments.get("roadmap_data"),
                arguments.get("dry_run", False)
            )
        elif name == "delete_issues":
            return await self.delete_issues(
                arguments.get("roadmap_data"),
                arguments.get("dry_run", False)
            )
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    def plan_issues_tool(self) -> Tool:
        """Tool for planning issue creation without actually creating them."""
        return Tool(
            name="plan_issues",
            description="Validates roadmap data and returns a detailed creation plan without actually creating issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "roadmap_data": {
                        "type": "object",
                        "description": "The roadmap data to validate and plan"
                    }
                },
                "required": ["roadmap_data"]
            }
        )
    
    def validate_roadmap_tool(self) -> Tool:
        """Tool for validating roadmap structure."""
        return Tool(
            name="validate_roadmap",
            description="Validates roadmap structure and returns detailed validation feedback",
            inputSchema={
                "type": "object",
                "properties": {
                    "roadmap_data": {
                        "type": "object",
                        "description": "The roadmap data to validate"
                    }
                },
                "required": ["roadmap_data"]
            }
        )
    
    def create_issues_tool(self) -> Tool:
        """Tool for bulk creating issues."""
        return Tool(
            name="create_issues",
            description="Bulk creates issues from validated roadmap data with progress tracking",
            inputSchema={
                "type": "object",
                "properties": {
                    "roadmap_data": {
                        "type": "object",
                        "description": "The roadmap data to create issues from"
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, only simulate the creation without actually creating issues",
                        "default": False
                    }
                },
                "required": ["roadmap_data"]
            }
        )
    
    def get_status_tool(self) -> Tool:
        """Tool for getting current state and progress."""
        return Tool(
            name="get_status",
            description="Returns current state and progress information in AI-friendly format",
            inputSchema={
                "type": "object",
                "properties": {
                    "roadmap_file": {
                        "type": "string",
                        "description": "Path to the roadmap file to get status for"
                    }
                },
                "required": ["roadmap_file"]
            }
        )
    
    def list_issues_tool(self) -> Tool:
        """Tool for listing existing issues."""
        return Tool(
            name="list_issues",
            description="Lists existing issues with filtering options",
            inputSchema={
                "type": "object",
                "properties": {
                    "roadmap_file": {
                        "type": "string",
                        "description": "Path to the roadmap file to list issues for"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["tree", "table", "json"],
                        "description": "Output format for the list",
                        "default": "json"
                    },
                    "show_missing": {
                        "type": "boolean",
                        "description": "If true, show issues defined in roadmap but not existing in GitHub",
                        "default": False
                    }
                },
                "required": ["roadmap_file"]
            }
        )
    
    def update_issues_tool(self) -> Tool:
        """Tool for bulk updating issues."""
        return Tool(
            name="update_issues",
            description="Bulk updates existing issues from roadmap changes",
            inputSchema={
                "type": "object",
                "properties": {
                    "roadmap_data": {
                        "type": "object",
                        "description": "The updated roadmap data"
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, only simulate the updates without actually updating issues",
                        "default": False
                    }
                },
                "required": ["roadmap_data"]
            }
        )
    
    def delete_issues_tool(self) -> Tool:
        """Tool for bulk deleting issues."""
        return Tool(
            name="delete_issues",
            description="Bulk deletes issues with safety checks",
            inputSchema={
                "type": "object",
                "properties": {
                    "roadmap_data": {
                        "type": "object",
                        "description": "The roadmap data containing issues to delete"
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, only simulate the deletion without actually deleting issues",
                        "default": False
                    }
                },
                "required": ["roadmap_data"]
            }
        )
    
    async def plan_issues(self, roadmap_data: Dict[str, Any]) -> Dict[str, Any]:
        """Plan issues creation without actually creating them."""
        try:
            # Use shared validation method
            SharedOperations.validate_roadmap_only(roadmap_data, self.schema_file)
            
            # Calculate what would be created
            project = roadmap_data['project']
            milestones = roadmap_data['milestones']
            
            plan = {
                "project": project['name'],
                "total_milestones": len(milestones),
                "total_tasks": sum(len(milestone.get('tasks', [])) for milestone in milestones),
                "milestones": []
            }
            
            for milestone in milestones:
                milestone_plan = {
                    "title": milestone['title'],
                    "description": milestone.get('description', 'No description'),
                    "task_count": len(milestone.get('tasks', [])),
                    "tasks": [task['title'] for task in milestone.get('tasks', [])]
                }
                plan["milestones"].append(milestone_plan)
            
            return {
                "success": True,
                "plan": plan,
                "message": "Issue creation plan generated successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to generate issue creation plan: {str(e)}"
            }
    
    async def validate_roadmap(self, roadmap_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate roadmap structure and return feedback."""
        try:
            # Use shared validation method
            SharedOperations.validate_roadmap_only(roadmap_data, self.schema_file)
            return {
                "success": True,
                "message": "Roadmap validation successful",
                "valid": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Roadmap validation failed: {str(e)}",
                "valid": False
            }
    
    async def create_issues(self, roadmap_data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """Bulk create issues from roadmap data."""
        try:
            if dry_run:
                # For dry run, just validate and return success
                SharedOperations.validate_roadmap_only(roadmap_data, self.schema_file)
                return {
                    "success": True,
                    "message": "Dry run: Roadmap validation successful. No issues created.",
                    "dry_run": True
                }
            
            # Use CLI's common setup method
            github_client, state_manager, _ = self.cli._common_setup("temp_roadmap.json", self.schema_file)
            
            # Use shared create issues method
            SharedOperations.create_issues_from_roadmap(roadmap_data, github_client, state_manager)
            
            # Return created issues information
            result = {
                "success": True,
                "message": "Issues created successfully",
                "main_tracking_issue": state_manager.get_main_tracking_issue(),
                "milestones": state_manager.get_all_milestones(),
                "tasks": {}
            }
            
            # Add tasks for each milestone
            for milestone_title in state_manager.get_all_milestones().keys():
                result["tasks"][milestone_title] = state_manager.get_all_tasks(milestone_title)
            
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create issues: {str(e)}",
                "dry_run": dry_run
            }
    
    async def get_status(self, roadmap_file: str) -> Dict[str, Any]:
        """Get current state and progress information."""
        try:
            # Use CLI's common setup method
            github_client, state_manager, roadmap_data = self.cli._common_setup(roadmap_file, self.schema_file)
            
            # Use shared status method
            result = SharedOperations.get_status(github_client, state_manager, roadmap_data, "json", detailed=True)
            return {
                "success": True,
                "data": result,
                "message": "Status retrieved successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get status: {str(e)}"
            }
    
    async def list_issues(self, roadmap_file: str, format: str = "json", show_missing: bool = False) -> Dict[str, Any]:
        """List existing issues with filtering options."""
        try:
            # Use CLI's common setup method
            _, state_manager, roadmap_data = self.cli._common_setup(roadmap_file, self.schema_file)
            
            # Use shared list method
            result = SharedOperations.list_issues(state_manager, roadmap_data, format, show_missing)
            return {
                "success": True,
                "data": result,
                "message": "Issues listed successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to list issues: {str(e)}"
            }
    
    async def update_issues(self, roadmap_data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """Bulk update existing issues from roadmap changes."""
        try:
            # Validate roadmap using shared method
            SharedOperations.validate_roadmap_only(roadmap_data, self.schema_file)
            
            project_name = roadmap_data['project'].get('name', 'Unknown Project')
            
            if dry_run:
                return {
                    "success": True,
                    "message": f"Dry run: Would update issues for project '{project_name}'. No changes made.",
                    "dry_run": True
                }
            
            # Use CLI's common setup method
            github_client, state_manager, _ = self.cli._common_setup("temp_roadmap.json", self.schema_file)
            
            # Process all milestones and tasks in the roadmap using shared method
            SharedOperations.update_all_issues(github_client, state_manager, roadmap_data)
            
            return {
                "success": True,
                "message": f"Issues updated successfully for project '{project_name}'",
                "project": project_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update issues: {str(e)}",
                "dry_run": dry_run
            }
    
    async def delete_issues(self, roadmap_data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """Bulk delete issues with safety checks."""
        try:
            # Validate roadmap using shared method
            SharedOperations.validate_roadmap_only(roadmap_data, self.schema_file)
            
            project_name = roadmap_data['project'].get('name', 'Unknown Project')
            total_milestones = len(roadmap_data.get('milestones', []))
            total_tasks = sum(len(milestone.get('tasks', [])) for milestone in roadmap_data.get('milestones', []))
            
            if dry_run:
                return {
                    "success": True,
                    "message": f"Dry run: Would delete {total_milestones} milestones and {total_tasks} tasks for project '{project_name}'. No changes made.",
                    "milestones_to_delete": total_milestones,
                    "tasks_to_delete": total_tasks,
                    "dry_run": True
                }
            
            # Use CLI's common setup method
            github_client, state_manager, _ = self.cli._common_setup("temp_roadmap.json", self.schema_file)
            
            # Process all milestones in the roadmap using shared method
            SharedOperations.delete_all_milestones(github_client, state_manager, roadmap_data)
            
            return {
                "success": True,
                "message": f"Deleted {total_milestones} milestones and {total_tasks} tasks for project '{project_name}'",
                "milestones_deleted": total_milestones,
                "tasks_deleted": total_tasks
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to delete issues: {str(e)}",
                "dry_run": dry_run
            }
    
    
    async def run_stdio(self):
        """Run the MCP server using stdio transport."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, 
                write_stream,
                initialization_options={}
            )
    async def run_http(self, host: str = Config.DEFAULT_HOST, port: int = Config.DEFAULT_MCP_PORT):
        """Run the MCP server using HTTP transport."""
        # HTTP transport would require additional setup
        # For now, we'll just raise NotImplementedError
        raise NotImplementedError("HTTP transport not yet implemented")

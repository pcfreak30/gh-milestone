"""
HTTP-based MCP Server implementation for GitHub Milestone CLI.
"""

import json
import os
import sys
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from .mcp_server import MCPServer
from .config import Config


class PlanIssuesRequest(BaseModel):
    """Request model for plan_issues endpoint."""
    roadmap_data: Dict[str, Any]


class ValidateRoadmapRequest(BaseModel):
    """Request model for validate_roadmap endpoint."""
    roadmap_data: Dict[str, Any]


class CreateIssuesRequest(BaseModel):
    """Request model for create_issues endpoint."""
    roadmap_data: Dict[str, Any]
    dry_run: Optional[bool] = False


class UpdateIssuesRequest(BaseModel):
    """Request model for update_issues endpoint."""
    roadmap_data: Dict[str, Any]
    dry_run: Optional[bool] = False


class DeleteIssuesRequest(BaseModel):
    """Request model for delete_issues endpoint."""
    roadmap_data: Dict[str, Any]
    dry_run: Optional[bool] = False


class MCPHTTPServer:
    """HTTP wrapper for MCP Server."""
    
    def __init__(self, schema_file: str = Config.DEFAULT_SCHEMA_FILE, verbose: bool = False):
        """Initialize HTTP server with MCP tools."""
        self.schema_file = schema_file
        self.verbose = verbose
        self.mcp_server = MCPServer(schema_file, verbose)
        self.app = FastAPI(
            title="GitHub Milestone CLI MCP Server",
            description="HTTP-based Model Context Protocol server for GitHub Milestone CLI",
            version="0.1.0"
        )
        
        # Add CORS middleware for AI agent integration
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._register_routes()
    
    def _register_routes(self):
        """Register HTTP routes for MCP tools."""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy"}
        
        @self.app.post("/plan-issues")
        async def plan_issues(request: PlanIssuesRequest):
            """Plan issues creation without actually creating them."""
            try:
                result = await self.mcp_server.plan_issues(request.roadmap_data)
                if result.get("success"):
                    return result
                else:
                    raise HTTPException(status_code=400, detail=result.get("message", "Failed to plan issues"))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/validate-roadmap")
        async def validate_roadmap(request: ValidateRoadmapRequest):
            """Validate roadmap structure."""
            try:
                result = await self.mcp_server.validate_roadmap(request.roadmap_data)
                if result.get("success"):
                    return result
                else:
                    raise HTTPException(status_code=400, detail=result.get("message", "Roadmap validation failed"))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/create-issues")
        async def create_issues(request: CreateIssuesRequest):
            """Bulk create issues from roadmap data."""
            try:
                result = await self.mcp_server.create_issues(request.roadmap_data, request.dry_run)
                if result.get("success"):
                    return result
                else:
                    raise HTTPException(status_code=400, detail=result.get("message", "Failed to create issues"))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/status")
        async def get_status(roadmap_file: str):
            """Get current state and progress information."""
            try:
                result = await self.mcp_server.get_status(roadmap_file)
                if result.get("success"):
                    return result
                else:
                    raise HTTPException(status_code=400, detail=result.get("message", "Failed to get status"))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/issues")
        async def list_issues(roadmap_file: str, format: str = "json", show_missing: bool = False):
            """List existing issues with filtering options."""
            try:
                result = await self.mcp_server.list_issues(roadmap_file, format, show_missing)
                if result.get("success"):
                    return result
                else:
                    raise HTTPException(status_code=400, detail=result.get("message", "Failed to list issues"))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/update-issues")
        async def update_issues(request: UpdateIssuesRequest):
            """Bulk update existing issues from roadmap changes."""
            try:
                result = await self.mcp_server.update_issues(request.roadmap_data, request.dry_run)
                if result.get("success"):
                    return result
                else:
                    raise HTTPException(status_code=400, detail=result.get("message", "Failed to update issues"))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/delete-issues")
        async def delete_issues(request: DeleteIssuesRequest):
            """Bulk delete issues with safety checks."""
            try:
                result = await self.mcp_server.delete_issues(request.roadmap_data, request.dry_run)
                if result.get("success"):
                    return result
                else:
                    raise HTTPException(status_code=400, detail=result.get("message", "Failed to delete issues"))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    def run(self, host: str = "localhost", port: int = 8000):
        """Run the HTTP server."""
        uvicorn.run(self.app, host=host, port=port)

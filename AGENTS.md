# AGENTS.md
This file provides guidance to various AI agents when working with code in this repository.

## Common Commands

### Development and Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_specific_file.py

# Run tests with verbose output
python -m pytest tests/ -v

# Install the CLI extension
gh extension install ./gh-milestone

# Validate a roadmap file
gh milestone validate roadmap.json --repo owner/repo

# Create issues in specific repository
gh milestone create roadmap.json --repo owner/repo

# Create issues with verbose output
gh milestone create roadmap.json --repo owner/repo --verbose

# Delete issues from explicit repository
gh milestone delete roadmap.json --repo owner/repo --milestone "Phase 1"
```

### MCP Server Operations
```bash
# Start MCP server for AI agents
gh milestone mcp-server

# Start MCP HTTP server on custom port
gh milestone mcp-server --port 9000

# Start MCP server with stdio transport
gh milestone mcp --transport stdio
```

### Shell Completion
```bash
# Install shell completion
gh milestone completion --install

# Generate completion script for bash
gh milestone completion --shell bash

# Generate completion script for zsh
gh milestone completion --shell zsh
```

## High-Level Architecture

### Project Structure
This is a Python-based GitHub CLI extension that creates hierarchical GitHub milestone structures from JSON roadmap definitions. The project follows a modular architecture with clear separation of concerns:

```
gh-milestone-cli/
├── gh_milestone/           # Main package directory
│   ├── cli.py             # Command-line interface and argument parsing
│   ├── github_client.py   # GitHub API interactions using PyGithub
│   ├── state_manager.py    # State persistence and management
│   ├── shared_operations.py # Business logic shared across interfaces
│   ├── issue_creator.py    # Issue creation and linking logic
│   ├── schema_validator.py # JSON schema validation
│   ├── config.py          # Configuration constants
│   ├── mcp_server.py      # MCP (Model Context Protocol) server
│   ├── mcp_http_server.py # HTTP wrapper for MCP server
│   └── main.py           # Entry point
├── tests/                 # Comprehensive test suite
├── completion/            # Shell completion scripts and aliases
├── schema.json           # JSON schema for roadmap validation
├── requirements.txt      # Python dependencies
├── pyproject.toml       # Project configuration
└── README.md            # Project documentation
```

### Core Components

#### CLI Layer (`cli.py`)
- **Purpose**: Handles command-line argument parsing and user interaction
- **Key Commands**: `create`, `validate`, `delete`, `update`, `list`, `status`, `validate-state`, `migrate-state`, `sync`, `completion`, `mcp`, `mcp-server`  
- **Repository Options**: `--repo` option for explicit repository targeting overriding environment/config
- **Pattern**: Uses argparse with subparsers for different commands, includes exception handling decorator

#### GitHub Integration (`github_client.py`)
- **Purpose**: Wraps GitHub API interactions using PyGithub SDK
- **Key Features**: Authentication via GITHUB_TOKEN or gh CLI, issue creation/deletion, sub-issue linking using GitHub's native sub-issues API
- **Authentication**: Supports both environment variables and gh CLI authentication

#### State Management (`state_manager.py`)
- **Purpose**: Manages persistent state of created issues and their relationships
- **State File**: Creates `.roadmap.json.state` files alongside roadmap files
- **Key Operations**: State validation, cleanup, migration, and synchronization with GitHub
- **Features**: Handles renamed milestones, moved tasks, and invalid state entries

#### Business Logic (`shared_operations.py`)
- **Purpose**: Contains shared business logic used by both CLI and MCP implementations
- **Key Operations**: Issue creation, deletion, updates, status reporting, and listing
- **Pattern**: Static methods that can be called from different interfaces

#### Issue Creation (`issue_creator.py`)
- **Purpose**: Handles the actual creation and linking of GitHub issues
- **Hierarchy**: Creates 3-level structure: Main Tracking Issue → Milestone Issues → Task Issues
- **Linking**: Uses GitHub's sub-issues API for proper parent-child relationships

#### MCP Integration (`mcp_server.py`, `mcp_http_server.py`)
- **Purpose**: Provides Model Context Protocol server for AI agent integration
- **Transport**: Supports both stdio and HTTP transports
- **Tools**: Exposes all CLI functionality as MCP tools for AI agents

### Data Flow

1. **Input**: JSON roadmap file validated against schema
2. **Processing**: CLI parses arguments and delegates to shared operations
3. **GitHub Interaction**: GitHub client creates/updates issues and establishes relationships
4. **State Management**: State manager tracks created issues and their relationships
5. **Output**: Success/failure messages and updated state files

### Key Design Patterns

#### State Management Pattern
- **Incremental Updates**: Preserves existing issues, only creates new ones
- **State File Structure**: Tracks main tracking issue, milestones, tasks, and relationships
- **Validation**: Regular validation against GitHub API to ensure state consistency

#### Command Pattern
- **Exception Handling**: Decorator-based exception handling across all commands
- **Common Setup**: Shared setup method for GitHub client and state manager
- **Dry Run Support**: Most commands support `--dry-run` for testing

#### MCP Integration Pattern
- **Tool Exposure**: All CLI functionality available as MCP tools
- **Shared Logic**: MCP server reuses business logic from shared operations
- **Transport Flexibility**: Supports both stdio and HTTP transports

### Configuration and Constants

#### Default Values (`config.py`)
- **Schema File**: `schema.json`
- **Host**: `localhost`
- **Ports**: MCP server (8080), HTTP server (8000)
- **Formats**: Tree (default list), summary (default status)
- **Labels**: Default task label ("task"), main tracking labels (["epic", "roadmap"])
- **Task Prefix**: "Task: "

#### Roadmap Schema
- **Required Fields**: `project`, `milestones`, `mainTrackingIssue`
- **Project Structure**: Name, description, labels
- **Milestone Structure**: Title, description, labels, tasks array
- **Task Structure**: Title, description
- **Main Tracking Issue**: Title, description, labels

### Testing Strategy

#### Test Structure
- **Base Class**: `BaseTestCase` provides common setup and mocking utilities
- **Data Factory**: `TestDataFactory` creates standardized test data
- **Coverage**: Comprehensive test coverage for all major components
- **Mocking**: Extensive use of mocking for GitHub API and file system operations

#### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: CLI command testing with mocked dependencies
- **MCP Tests**: MCP server tool testing
- **State Management Tests**: State persistence and migration testing

### Shell Integration

#### Completion System
- **Bash and Zsh Support**: Complete shell completion for all commands and options
- **Dynamic Completion**: File completion and roadmap-based completion (requires jq)
- **Installation**: Automatic and manual installation scripts

#### Command Aliases
- **Comprehensive Alias Set**: Short aliases for all common operations
- **Function Aliases**: Multi-step workflow aliases
- **Format-Specific Aliases**: Aliases for different output formats
- **Verbose Aliases**: Separate aliases for verbose operations

### Error Handling and Validation

#### Schema Validation
- **JSON Schema**: Strict validation against defined schema
- **Early Validation**: Validate roadmap before any GitHub operations
- **Clear Error Messages**: Detailed validation error reporting

#### State Validation
- **GitHub API Validation**: Regular validation of state against actual GitHub issues
- **Cleanup Operations**: Automatic cleanup of invalid state entries
- **Migration Support**: Handles roadmap structure changes gracefully

#### Exception Handling
- **Decorator Pattern**: Consistent exception handling across all commands
- **User-Friendly Messages**: Clear error messages with actionable guidance
- **Verbose Mode**: Detailed error information when requested

This architecture ensures maintainability, testability, and extensibility while providing a robust CLI tool for GitHub milestone management.

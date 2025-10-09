# GitHub Milestone CLI Extension

A GitHub CLI extension that creates hierarchical GitHub milestone structures from milestone/task definitions using the GitHub sub-issues API. The extension now automatically detects the target repository from your current git directory.

## Features

- ✅ Create hierarchical GitHub milestone structures from JSON roadmap definitions
- ✅ Use proper GitHub sub-issues API (not comments) for issue relationships
- ✅ State management for incremental updates without altering existing issues
- ✅ JSON schema validation for roadmap files
- ✅ GitHub CLI extension integration
- ✅ PyGithub SDK for robust API interactions
- ✅ MCP (Model Context Protocol) server for AI agent integration

## Installation

### Prerequisites

- GitHub CLI (`gh`) installed
- Python 3.8+ with PyGithub and jsonschema packages
- GitHub authentication (personal access token or `gh auth login`)

### Install Dependencies

```bash
pip install PyGithub jsonschema
```

### Install Extension

```bash
gh extension install ./gh-milestone
```

## Repository Auto-Detection

The extension now automatically detects the target repository from your current git directory, eliminating the need to explicitly specify the repository in many cases.

### Priority Order

Repository specification follows this priority order:
1. `--repo` command-line option (highest priority)
2. `GH_REPO` environment variable
3. Auto-detection from current git directory (lowest priority)

When running the extension within a git repository, it will automatically extract the owner and repository name from your remote origin URL.

### Supported Formats

Auto-detection works with the following git remote URL formats:
- HTTPS: `https://github.com/owner/repo.git`
- SSH: `git@github.com:owner/repo.git`
- GitHub CLI context: Current `gh` repository context

### Examples

```bash
# No need to specify --repo if you're in a git repository
gh milestone create roadmap.json

# Auto-detection works with validation too
gh milestone validate roadmap.json

# Explicit --repo still overrides auto-detection
gh milestone create roadmap.json --repo owner/another-repo
```

### Error Handling

When no repository can be detected, you'll get a clear error message:
```bash
❌ No repository specified and could not auto-detect from current directory.
Please specify a repository using --repo option or GH_REPO environment variable.
```

## Usage

### Basic Usage

```bash
# Create issues (repository auto-detected from current git directory)
gh milestone create roadmap.json

# Create issues in specific repository
gh milestone create roadmap.json --repo owner/repo

# Validate roadmap file without creating issues
gh milestone validate roadmap.json

# Use custom schema file
gh milestone create roadmap.json --schema custom_schema.json

# Enable verbose output
gh milestone create roadmap.json --verbose
```

### Roadmap File Format

Create a JSON file defining your project milestones and tasks:

```json
{
  "project": {
    "name": "My Project",
    "description": "A sample project for demonstration",
    "labels": ["project", "demo"]
  },
  "milestones": [
    {
      "title": "Phase 1: Setup",
      "description": "Initial project setup and configuration",
      "labels": ["setup"],
      "tasks": [
        {
          "title": "Create repository structure",
          "description": "Set up the basic directory structure"
        },
        {
          "title": "Configure CI/CD pipeline",
          "description": "Set up continuous integration and deployment"
        }
      ]
    },
    {
      "title": "Phase 2: Development",
      "description": "Core development work",
      "labels": ["development"],
      "tasks": [
        {
          "title": "Implement core features",
          "description": "Develop the main functionality"
        },
        {
          "title": "Write tests",
          "description": "Create comprehensive test suite"
        }
      ]
    }
  ],
  "mainTrackingIssue": {
    "title": "Project Roadmap",
    "description": "Main tracking issue for the entire project",
    "labels": ["epic", "roadmap"]
  }
}
```

### State Management

The extension creates a state file (`.roadmap.json.state`) to track created issues:

- **Main tracking issue**: ID and URL
- **Milestone issues**: IDs and URLs for each milestone
- **Task issues**: IDs and URLs for each task
- **Hierarchy relationships**: Parent-child issue relationships
- **Last sync timestamp**: When the roadmap was last processed

When you run the command again, it:
- ✅ Uses existing issues without modifying their status
- ✅ Only creates new issues that don't exist yet
- ✅ Updates relationships as needed
- ✅ Preserves checked/unchecked status of existing issues

## Repository Targeting

Specify the target repository using either the `--repo` option, `GH_REPO` environment variable, or rely on auto-detection:

```bash
# Create issues (repository auto-detected from current git directory)
gh milestone create roadmap.json

# Create issues in specific repository
gh milestone create roadmap.json --repo owner/repo

# Validate roadmap against different repository
gh milestone validate roadmap.json --repo another-owner/another-repo

# Delete issues from explicit repository
gh milestone delete roadmap.json --repo explicit-owner/explicit-repo --milestone "Phase 1"
```

**Precedence Rules:**
1. `--repo` command-line option (highest priority)
2. `GH_REPO` environment variable
3. Auto-detection from current git directory (lowest priority)

When running the extension within a git repository, it will automatically extract the owner and repository name from your remote origin URL.

### Supported Formats

Auto-detection works with the following git remote URL formats:
- HTTPS: `https://github.com/owner/repo.git`
- SSH: `git@github.com:owner/repo.git`
- GitHub CLI context: Current `gh` repository context

### Error Handling

When no repository can be detected, you'll get a clear error message:
```bash
❌ No repository specified and unable to auto-detect from current directory.
Please specify a repository using --repo option or GH_REPO environment variable.
```

### Authentication

The extension supports multiple authentication methods:

1. **Environment Variable** (recommended):
   ```bash
   export GITHUB_TOKEN=your_personal_access_token
   ```

2. **GitHub CLI Authentication**:
   ```bash
   gh auth login
   ```

## Schema Validation

The extension validates roadmap files against a JSON schema to ensure proper structure. The default schema is `schema.json`.

### Schema Structure

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GitHub Milestone Schema",
  "type": "object",
  "required": ["project", "milestones", "mainTrackingIssue"],
  "properties": {
    "project": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "labels": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    "milestones": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["title", "tasks"],
        "properties": {
          "title": {"type": "string"},
          "description": {"type": "string"},
          "labels": {
            "type": "array",
            "items": {"type": "string"}
          },
          "tasks": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["title"],
              "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"}
              }
            }
          }
        }
      }
    },
    "mainTrackingIssue": {
      "type": "object",
      "required": ["title"],
      "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "labels": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    }
  }
}
```

## Issue Hierarchy

The extension creates a three-level hierarchy:

1. **Main Tracking Issue** (Level 1)
   - Links to all milestone issues
   - Contains project overview and statistics

2. **Milestone Issues** (Level 2)
   - Parent issues for each milestone
   - Contain task lists and acceptance criteria
   - Linked to the main tracking issue

3. **Task Issues** (Level 3)
   - Sub-issues for individual tasks
   - Linked to their parent milestone issues
   - Use the GitHub sub-issues API for proper relationships

## Examples

### Example 1: Basic Project Setup

```bash
# Create a simple roadmap
cat > simple_roadmap.json << EOF
{
  "project": {
    "name": "Simple Project",
    "labels": ["simple"]
  },
  "milestones": [
    {
      "title": "Setup",
      "description": "Initial setup",
      "tasks": [
        {
          "title": "Install dependencies",
          "description": "Install required packages"
        }
      ]
    }
  ],
  "mainTrackingIssue": {
    "title": "Simple Project Roadmap",
    "labels": ["epic"]
  }
}
EOF

# Create issues
gh milestone create simple_roadmap.json
```

### Example 2: Large Project with Multiple Milestones

```bash
# Create a comprehensive roadmap
cat > complex_roadmap.json << EOF
{
  "project": {
    "name": "Enterprise Application",
    "description": "A large-scale enterprise application",
    "labels": ["enterprise", "backend"]
  },
  "milestones": [
    {
      "title": "Architecture Design",
      "description": "Design system architecture",
      "labels": ["architecture"],
      "tasks": [
        {
          "title": "Design database schema",
          "description": "Create comprehensive database design"
        },
        {
          "title": "Define API endpoints",
          "description": "Design REST API structure"
        },
        {
          "title": "Create system diagrams",
          "description": "Generate architecture diagrams"
        }
      ]
    },
    {
      "title": "Core Implementation",
      "description": "Implement core functionality",
      "labels": ["implementation"],
      "tasks": [
        {
          "title": "Set up project structure",
          "description": "Create directory structure and build system"
        },
        {
          "title": "Implement authentication",
          "description": "Create user authentication system"
        },
        {
          "title": "Build data models",
          "description": "Implement core data models and ORM"
        }
      ]
    },
    {
      "title": "Testing and Deployment",
      "description": "Testing strategy and deployment pipeline",
      "labels": ["testing", "devops"],
      "tasks": [
        {
          "title": "Write unit tests",
          "description": "Create comprehensive test suite"
        },
        {
          "title": "Set up CI/CD",
          "description": "Configure continuous integration and deployment"
        },
        {
          "title": "Deploy to staging",
          "description": "Deploy application to staging environment"
        }
      ]
    }
  ],
  "mainTrackingIssue": {
    "title": "Enterprise Application Roadmap",
    "description": "Complete roadmap for enterprise application development",
    "labels": ["epic", "roadmap", "enterprise"]
  }
}
EOF

# Create issues with verbose output
gh milestone create complex_roadmap.json --verbose
```

## Troubleshooting

### Common Issues

1. **Extension not found**:
   ```bash
   gh extension install --force ./gh-milestone
   ```

2. **Authentication errors**:
   ```bash
   # Check authentication status
   gh auth status
   
   # Or set environment variable
   export GITHUB_TOKEN=your_token
   ```

3. **Schema validation errors**:
   - Ensure your JSON file is valid
   - Check that all required fields are present
   - Use the validate command first: `gh milestone validate roadmap.json`

4. **Permission errors**:
   - Ensure your GitHub token has appropriate permissions
   - Check that you have write access to the repository

### Debug Mode

Enable verbose output to see detailed information:

```bash
gh milestone create roadmap.json --verbose
```

## Development

### Project Structure

```
gh-milestone/
├── gh-milestone          # Main extension script
├── gh-milestone.yml      # Extension manifest
└── schema.json  # JSON schema for validation
```

### Testing

```bash
# Validate a roadmap file
gh milestone validate test_roadmap.json

# Test with verbose output
gh milestone create test_roadmap.json --verbose
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section above
- Review the examples for common use cases

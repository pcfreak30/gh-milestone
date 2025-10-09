"""
Command-line interface module for GitHub Milestone CLI.
"""

import argparse
import sys
import os
import json
from pathlib import Path
from typing import Any, Callable
import shutil
from .config import Config
from .schema_validator import SchemaValidator
from .github_client import GitHubClient
from .state_manager import StateManager
from .shared_operations import SharedOperations


def exception_handler(func: Callable) -> Callable:
    """Decorator to handle common exceptions across CLI command handlers."""
    def wrapper(self, args, *extra_args, **kwargs):
        try:
            return func(self, args, *extra_args, **kwargs)
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user.")
            sys.exit(1)
        except SystemExit:
            # Re-raise SystemExit exceptions without modification
            raise
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            if getattr(args, 'verbose', False):
                import traceback
                traceback.print_exc()
            sys.exit(1)
    return wrapper


class CLI:
    """Command-line interface handler for GitHub Milestone CLI."""
    
    def __init__(self):
        """Initialize CLI parser and handlers."""
        self.parser = self._create_parser()
        self.aliases = self._load_aliases()
        self.command_handlers = {
            'create': self._handle_create_command,
            'validate': self._handle_validate_command,
            'delete': self._handle_delete_command,
            'update': self._handle_update_command,
            'list': self._handle_list_command,
            'status': self._handle_status_command,
            'validate-state': self._handle_validate_state_command,
            'migrate-state': self._handle_migrate_state_command,
            'sync': self._handle_sync_command,
            'completion': self._handle_completion_command,
            'mcp': self._handle_mcp_command,
            'mcp-server': self._handle_mcp_server_command
        }
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure argument parser."""
        parser = argparse.ArgumentParser(
            description="Create GitHub milestone structures from milestone/task definitions",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Create milestones using default schema
  gh milestone create roadmap.json

  # Create milestones with custom schema
  gh milestone create roadmap.json --schema custom_schema.json

  # Only validate without creating milestones
  gh milestone validate roadmap.json

  # Use verbose output
  gh milestone create roadmap.json --verbose

  # Delete a milestone and all its tasks
  gh milestone delete roadmap.json --milestone "Phase 1: Setup"

  # Delete a specific task from a milestone
  gh milestone delete roadmap.json --task "Create repository structure" --milestone-parent "Phase 1: Setup"

  # Update milestone title and description
  gh milestone update roadmap.json --milestone "Phase 1: Setup" --update-title --update-description

  # Update task labels
  gh milestone update roadmap.json --task "Implement core features" --milestone-parent "Phase 2: Development" --update-labels

  # List milestones in tree format (default)
  gh milestone list roadmap.json

  # List milestones in table format
  gh milestone list roadmap.json --format table

  # List milestones showing missing ones
  gh milestone list roadmap.json --show-missing

  # Show status summary
  gh milestone status roadmap.json

  # Show detailed status
  gh milestone status roadmap.json --detailed

  # Show status in JSON format
  gh milestone status roadmap.json --format json

  # Validate state file
  gh milestone validate-state roadmap.json

  # Validate state and clean up invalid entries
  gh milestone validate-state roadmap.json --cleanup

  # Show what would be cleaned up without actually cleaning
  gh milestone validate-state roadmap.json --cleanup --dry-run

  # Migrate state file
  gh milestone migrate-state roadmap.json

  # Migrate state file with custom schema
  gh milestone migrate-state roadmap.json --schema custom_schema.json

  # Show what would be migrated without actually migrating
  gh milestone migrate-state roadmap.json --dry-run

  # Sync state with GitHub and roadmap
  gh milestone sync roadmap.json

  # Show what would be synced without actually syncing
  gh milestone sync roadmap.json --dry-run

  # Use custom schema file
  gh milestone sync roadmap.json --schema custom_schema.json

  # Start MCP server for AI agents
  gh milestone mcp-server

  # Start MCP server on custom host/port
  gh milestone mcp-server --host 0.0.0.0 --port 9000
            """
        )

        # Add subparsers for different commands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')

        # Create command
        create_parser = subparsers.add_parser('create', help='Create GitHub milestone structures from roadmap')
        create_parser.add_argument(
            "roadmap_file",
            help="Path to the JSON file containing milestone/task definitions"
        )
        create_parser.add_argument(
            "--repo",
            help="Target GitHub repository in 'owner/repo' format (overrides auto-detection)"
        )
        create_parser.add_argument(
            "--schema",
            default=Config.DEFAULT_SCHEMA_FILE,
            help="Path to the JSON schema file (default: schema.json)"
        )
        create_parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
        )

        # Validate command
        validate_parser = subparsers.add_parser('validate', help='Validate roadmap file against schema')
        validate_parser.add_argument(
            "roadmap_file",
            help="Path to the JSON file containing milestone/task definitions"
        )
        validate_parser.add_argument(
            "--repo",
            help="Target GitHub repository in 'owner/repo' format (overrides auto-detection)"
        )
        validate_parser.add_argument(
            "--schema",
            default=Config.DEFAULT_SCHEMA_FILE,
            help="Path to the JSON schema file (default: schema.json)"
        )
        validate_parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
        )

        # Delete command
        delete_parser = subparsers.add_parser('delete', help='Delete GitHub issues from roadmap')
        delete_parser.add_argument(
            "roadmap_file",
            help="Path to the JSON file containing milestone/task definitions"
        )
        delete_parser.add_argument(
            "--repo",
            help="Target GitHub repository in 'owner/repo' format (overrides auto-detection)"
        )
        delete_parser.add_argument(
            "--milestone",
            help="Title of the milestone to delete"
        )
        delete_parser.add_argument(
            "--task",
            help="Title of the task to delete"
        )
        delete_parser.add_argument(
            "--milestone-parent",
            help="Title of the parent milestone when deleting a task"
        )
        delete_parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
        )
        
        # Update command
        update_parser = subparsers.add_parser('update', help='Update existing GitHub issues from roadmap')
        update_parser.add_argument(
            "roadmap_file",
            help="Path to the JSON file containing milestone/task definitions"
        )
        update_parser.add_argument(
            "--schema",
            default=Config.DEFAULT_SCHEMA_FILE,
            help="Path to the JSON schema file (default: schema.json)"
        )
        update_parser.add_argument(
            "--milestone",
            help="Title of the milestone to update"
        )
        update_parser.add_argument(
            "--task",
            help="Title of the task to update"
        )
        update_parser.add_argument(
            "--milestone-parent",
            help="Title of the parent milestone when updating a task"
        )
        update_parser.add_argument(
            "--update-title",
            action="store_true",
            help="Update issue titles"
        )
        update_parser.add_argument(
            "--update-description",
            action="store_true",
            help="Update issue descriptions"
        )
        update_parser.add_argument(
            "--update-labels",
            action="store_true",
            help="Update issue labels"
        )
        update_parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
        )
        
        # List command
        list_parser = subparsers.add_parser('list', help='List current hierarchy and state')
        list_parser.add_argument(
            "roadmap_file",
            help="Path to the JSON file containing milestone/task definitions"
        )
        list_parser.add_argument(
            "--schema",
            default=Config.DEFAULT_SCHEMA_FILE,
            help="Path to the JSON schema file (default: schema.json)"
        )
        list_parser.add_argument(
            "--format",
            choices=['tree', 'table', 'json'],
            default=Config.DEFAULT_LIST_FORMAT,
            help=f"Output format (default: {Config.DEFAULT_LIST_FORMAT})"
        )
        list_parser.add_argument(
            "--show-missing",
            action="store_true",
            help="Show issues defined in roadmap but not existing in GitHub"
        )
        list_parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
        )
        
        # Status command
        status_parser = subparsers.add_parser('status', help='Show progress and completion status')
        status_parser.add_argument(
            "roadmap_file",
            help="Path to the JSON file containing milestone/task definitions"
        )
        status_parser.add_argument(
            "--schema",
            default=Config.DEFAULT_SCHEMA_FILE,
            help="Path to the JSON schema file (default: schema.json)"
        )
        status_parser.add_argument(
            "--detailed",
            action="store_true",
            help="Show detailed status information"
        )
        status_parser.add_argument(
            "--format",
            choices=['summary', 'detailed', 'json'],
            default=Config.DEFAULT_STATUS_FORMAT,
            help=f"Output format (default: {Config.DEFAULT_STATUS_FORMAT})"
        )
        status_parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
        )
        
        # Validate-state command
        validate_state_parser = subparsers.add_parser('validate-state', help='Validate state file entries')
        validate_state_parser.add_argument(
            "roadmap_file",
            help="Path to the JSON file containing milestone/task definitions"
        )
        validate_state_parser.add_argument(
            "--cleanup",
            action="store_true",
            help="Automatically remove invalid entries from state"
        )
        validate_state_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be cleaned up without actually cleaning"
        )
        validate_state_parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
        )
        
        # Migrate-state command
        migrate_state_parser = subparsers.add_parser('migrate-state', help='Migrate state file to current format')
        migrate_state_parser.add_argument(
            "roadmap_file",
            help="Path to the JSON file containing milestone/task definitions"
        )
        migrate_state_parser.add_argument(
            "--schema",
            default=Config.DEFAULT_SCHEMA_FILE,
            help="Path to the JSON schema file (default: schema.json)"
        )
        migrate_state_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be migrated without actually migrating"
        )
        migrate_state_parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
        )
        
        # Sync command
        sync_parser = subparsers.add_parser('sync', help='Synchronize state with GitHub and roadmap')
        sync_parser.add_argument(
            "roadmap_file",
            help="Path to the JSON file containing milestone/task definitions"
        )
        sync_parser.add_argument(
            "--schema",
            default=Config.DEFAULT_SCHEMA_FILE,
            help="Path to the JSON schema file (default: schema.json)"
        )
        sync_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be synced without actually syncing"
        )
        sync_parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
        )
        
        # Completion command
        completion_parser = subparsers.add_parser('completion', help='Install shell completion scripts')
        completion_parser.add_argument(
            "--shell",
            choices=['bash', 'zsh'],
            help="Shell type for completion (default: auto-detect)"
        )
        completion_parser.add_argument(
            "--install",
            action="store_true",
            help="Actually install the completion script (default: show instructions)"
        )
        completion_parser.add_argument(
            "--force",
            action="store_true",
            help="Force installation even if directories don't exist"
        )
        completion_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be installed without actually installing"
        )
        
        # MCP command
        mcp_parser = subparsers.add_parser('mcp', help='Start MCP (Model Context Protocol) server for AI agents')
        mcp_parser.add_argument(
            "--host",
            default=Config.DEFAULT_HOST,
            help=f"Host to bind the server to (default: {Config.DEFAULT_HOST})"
        )
        mcp_parser.add_argument(
            "--port",
            type=int,
            default=Config.DEFAULT_MCP_PORT,
            help=f"Port to bind the server to (default: {Config.DEFAULT_MCP_PORT})"
        )
        mcp_parser.add_argument(
            "--transport",
            choices=['stdio', 'http'],
            default=Config.DEFAULT_MCP_TRANSPORT,
            help=f"Transport mode for MCP communication (default: {Config.DEFAULT_MCP_TRANSPORT})"
        )
        mcp_parser.add_argument(
            "--schema",
            default=Config.DEFAULT_SCHEMA_FILE,
            help="Path to the JSON schema file (default: milestone_tool_schema.json)"
        )
        mcp_parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
        )
        
        # MCP Server command
        mcp_server_parser = subparsers.add_parser('mcp-server', help='Start HTTP server for MCP-compatible bulk issue operations')
        mcp_server_parser.add_argument(
            "--host",
            default=Config.DEFAULT_HOST,
            help=f"Host to bind the server to (default: {Config.DEFAULT_HOST})"
        )
        mcp_server_parser.add_argument(
            "--port",
            type=int,
            default=Config.DEFAULT_HTTP_SERVER_PORT,
            help=f"Port to bind the server to (default: {Config.DEFAULT_HTTP_SERVER_PORT})"
        )
        mcp_server_parser.add_argument(
            "--schema-file",
            default=Config.DEFAULT_SCHEMA_FILE,
            help="Path to the JSON schema file (default: milestone_tool_schema.json)"
        )
        mcp_server_parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
        )
        
        return parser
    
    def parse_args(self) -> argparse.Namespace:
        """Parse command-line arguments."""
        return self.parser.parse_args()
    
    def _common_setup(self, roadmap_file: str, schema_file: str, repo: str = None):
        """Common setup for CLI commands that need GitHub client and state manager."""
        # Get repository name using Config's auto-detection with explicit override
        repo_name = Config.get_repo_name(repo)
        if not repo_name:
            print("❌ No repository specified and unable to auto-detect from current directory.")
            print("Please specify a repository using --repo option or GH_REPO environment variable.")
            sys.exit(1)
            
        github_client = GitHubClient(repo=repo_name)
        state_manager = StateManager(roadmap_file)
        
        # Load and validate roadmap data
        roadmap_data = SchemaValidator.load_json_file(roadmap_file)
        SchemaValidator.validate_schema(roadmap_data, schema_file)
        
        return github_client, state_manager, roadmap_data
    
    @exception_handler
    def _handle_create_command(self, args: argparse.Namespace, schema_file: str, repo: str = None):
        """Handle the create command execution."""
        github_client, state_manager, roadmap_data = self._common_setup(args.roadmap_file, schema_file, args.repo)
        self._create_issues(roadmap_data, github_client, state_manager)

    def _create_issues(self, roadmap_data: dict, github_client: GitHubClient, state_manager: StateManager):
        """Shared business logic for creating milestone structures from roadmap data."""
        SharedOperations.create_issues_from_roadmap(roadmap_data, github_client, state_manager)
    
    @exception_handler
    def _handle_validate_command(self, args: argparse.Namespace, schema_file: str, repo: str = None):
        """Handle the validate command execution."""
        try:
            _, _, roadmap_data = self._common_setup(args.roadmap_file, schema_file, args.repo)
            SharedOperations.validate_roadmap_only(roadmap_data, schema_file)
            print("✅ Roadmap validation successful")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Roadmap validation failed: {e}")
            sys.exit(1)
    
    @exception_handler
    def _handle_delete_command(self, args: argparse.Namespace, schema_file: str, repo: str = None):
        """Handle the delete command execution."""
        github_client, state_manager, roadmap_data = self._common_setup(args.roadmap_file, schema_file, args.repo)
        
        SharedOperations.delete_issues(github_client, state_manager, args.milestone, args.task, 
                                     args.milestone_parent, roadmap_data)
            
        state_manager.save_state()
    
    @exception_handler
    def _handle_update_command(self, args: argparse.Namespace, schema_file: str, repo: str = None):
        """Handle the update command execution."""
        github_client, state_manager, roadmap_data = self._common_setup(args.roadmap_file, schema_file, args.repo)
        
        SharedOperations.update_issues(github_client, state_manager, args.milestone, args.task, 
                                     args.milestone_parent, roadmap_data, args.update_title, 
                                     args.update_description, args.update_labels)
            
        state_manager.save_state()
    
    @exception_handler
    def _handle_validate_state_command(self, args: argparse.Namespace, schema_file: str, repo: str = None):
        """Handle the validate-state command execution."""
        github_client, state_manager, roadmap_data = self._common_setup(args.roadmap_file, schema_file, args.repo)
        
        # Validate state entries
        invalid_entries = state_manager.validate_state(github_client)
        
        # Display results
        if not any(invalid_entries.values()):
            print("✅ State validation complete. All entries are valid.")
        else:
            print("⚠️  Invalid state entries found:")
            if invalid_entries['invalid_milestones']:
                print(f"  Invalid milestones: {len(invalid_entries['invalid_milestones'])}")
            if invalid_entries['invalid_tasks']:
                print(f"  Invalid tasks: {len(invalid_entries['invalid_tasks'])}")
            
            # Handle cleanup if requested
            if args.cleanup:
                if args.dry_run:
                    print("🔄 Dry run mode: Would clean up invalid entries")
                else:
                    print("🧹 Cleaning up invalid entries...")
                    state_manager.cleanup_state(github_client, dry_run=False)
                    state_manager.save_state()
                    print("✅ State cleanup complete.")
            elif args.dry_run:
                print("🔄 Dry run mode: Showing what would be cleaned up")
    
    @exception_handler
    def _handle_migrate_state_command(self, args: argparse.Namespace, schema_file: str, repo: str = None):
        """Handle the migrate-state command execution."""
        github_client, state_manager, roadmap_data = self._common_setup(args.roadmap_file, schema_file, args.repo)
        
        # Perform migration
        migration_summary = state_manager.migrate_state(roadmap_data, dry_run=args.dry_run)
        if migration_summary and (migration_summary.get('milestone_changes') or migration_summary.get('task_changes')):
            if not args.dry_run:
                state_manager.save_state()
                print("✅ State migration complete.")
            else:
                print("🔄 Dry run mode: Showing what would be migrated")
                print("Migration Summary:")
                for key, value in migration_summary.items():
                    print(f"  {key}: {value}")
        else:
            print("✅ No state migrations needed.")
    
    @exception_handler
    def _handle_completion_command(self, args: argparse.Namespace):
        """Handle the completion command execution."""
        # Detect shell type if not specified
        shell = args.shell
        if not shell:
            shell = self._detect_shell()
            if not shell:
                print("❌ Could not detect shell type. Please specify --shell explicitly.")
                sys.exit(1)
        
        # Get completion script content
        completion_script = self._get_completion_script(shell)
        
        if args.install:
            self._install_completion(shell, completion_script, args.force, args.dry_run)
        else:
            # Output completion script content to stdout
            print(completion_script)
    
    def _detect_shell(self) -> str:
        """Detect the current shell type."""
        shell_path = os.environ.get('SHELL', '')
        if 'zsh' in shell_path:
            return 'zsh'
        elif 'bash' in shell_path:
            return 'bash'
        return None
    
    def _get_completion_script(self, shell: str) -> str:
        """Generate completion script for the specified shell."""
        from pathlib import Path
        import os
        
        # Define script names
        if shell == 'bash':
            script_name = 'gh-milestone'
        elif shell == 'zsh':
            script_name = '_gh-milestone'
        else:
            return ""
        
        # Scenario 1: Try relative to current working directory (development scenario)
        script_path = Path(f'completion/{shell}/{script_name}')
        if script_path.exists():
            try:
                return script_path.read_text(encoding='utf-8')
            except Exception as e:
                print(f"❌ Error reading completion script for {shell}: {e}")
                sys.exit(1)
        
        # Scenario 2: Try relative to the CLI module location (package installation)
        try:
            # Get the directory where this module is located
            cli_module_dir = Path(__file__).parent
            script_path = cli_module_dir.parent / 'completion' / shell / script_name
            if script_path.exists():
                try:
                    return script_path.read_text(encoding='utf-8')
                except Exception as e:
                    print(f"❌ Error reading completion script for {shell}: {e}")
                    sys.exit(1)
        except Exception:
            pass  # Continue to next scenario if this fails
        
        # Scenario 3: Try common system directories (system-wide installation)
        common_paths = [
            Path(f'/usr/local/share/gh-milestone/completion/{shell}/{script_name}'),
            Path(f'/usr/share/gh-milestone/completion/{shell}/{script_name}'),
            Path.home() / f'.local/share/gh-milestone/completion/{shell}/{script_name}'
        ]
        
        for path in common_paths:
            if path.exists():
                try:
                    return path.read_text(encoding='utf-8')
                except Exception as e:
                    print(f"❌ Error reading completion script for {shell}: {e}")
                    sys.exit(1)
        
        # If none of the scenarios worked, provide a clear error message
        print(f"❌ Completion script for {shell} not found in any of the expected locations:")
        print(f"  - Development: {Path('completion') / shell / script_name}")
        print(f"  - Package installation: {{installation_dir}}/completion/{shell}/{script_name}")
        print(f"  - System directories: /usr/local/share/gh-milestone/completion/{shell}/{script_name}")
        print(f"                       /usr/share/gh-milestone/completion/{shell}/{script_name}")
        print(f"                       {{home}}/.local/share/gh-milestone/completion/{shell}/{script_name}")
        sys.exit(1)
    
    def _show_completion_instructions(self, shell: str, completion_script: str):
        """Show instructions for installing completion."""
        if shell == 'bash':
            print("To enable bash completion, add the following to your ~/.bashrc:")
            print()
            print("# GitHub Milestone CLI completion")
            print('eval "$(gh-milestone completion --shell bash)"')
            print()
            print("Or to install the completion script:")
            print("gh-milestone completion --shell bash --install")
        elif shell == 'zsh':
            print("To enable zsh completion, add the following to your ~/.zshrc:")
            print()
            print("# GitHub Milestone CLI completion")
            print('eval "$(gh-milestone completion --shell zsh)"')
            print()
            print("Or to install the completion script:")
            print("gh-milestone completion --shell zsh --install")
    
    def _install_completion(self, shell: str, completion_script: str, force: bool, dry_run: bool = False):
        """Install completion script."""
        if shell == 'bash':
            completion_dir = Path.home() / '.bash_completion.d'
            completion_file = completion_dir / 'gh-milestone'
            rc_file = Path.home() / '.bashrc'
            eval_line = '[ -f ~/.bash_completion.d/gh-milestone ] && . ~/.bash_completion.d/gh-milestone'
        elif shell == 'zsh':
            completion_dir = Path.home() / '.zsh_completion.d'
            completion_file = completion_dir / 'gh-milestone'
            rc_file = Path.home() / '.zshrc'
            eval_line = '[ -f ~/.zsh_completion.d/gh-milestone ] && . ~/.zsh_completion.d/gh-milestone'
        else:
            print(f"❌ Unsupported shell: {shell}")
            sys.exit(1)
        
        if dry_run:
            print(f"🔄 Dry run mode: Would install completion for {shell}")
            print(f"  Would create directory: {completion_dir}")
            print(f"  Would write completion script to: {completion_file}")
            print(f"  Would add the following line to: {rc_file}")
            print(f"    {eval_line}")
            return
        
        # Create completion directory if needed
        if not completion_dir.exists():
            if force:
                completion_dir.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {completion_dir}")
            else:
                print(f"❌ Completion directory {completion_dir} does not exist.")
                print("Use --force to create it automatically.")
                sys.exit(1)
        
        # Write completion script
        try:
            with open(completion_file, 'w') as f:
                f.write(completion_script)
            print(f"✅ Completion script installed to: {completion_file}")
        except Exception as e:
            print(f"❌ Failed to write completion script: {e}")
            sys.exit(1)
        
        # Add to shell rc file if not already present
        try:
            with open(rc_file, 'r') as f:
                rc_content = f.read()
        except FileNotFoundError:
            rc_content = ""
        
        if eval_line not in rc_content:
            try:
                with open(rc_file, 'a') as f:
                    f.write(f"\n{eval_line}\n")
                print(f"✅ Added completion to: {rc_file}")
                print("Please restart your shell or run:")
                if shell == 'bash':
                    print("  source ~/.bashrc")
                elif shell == 'zsh':
                    print("  source ~/.zshrc")
            except Exception as e:
                print(f"❌ Failed to add completion to shell rc file: {e}")
                print("Please add the following line to your shell rc file manually:")
                print(f"  {eval_line}")
        else:
            print(f"✅ Completion already configured in: {rc_file}")

    @exception_handler
    def _handle_mcp_command(self, args: argparse.Namespace):
        """Handle the MCP server command execution."""
        from .mcp_server import MCPServer
        
        # Validate schema file exists
        if not Path(args.schema).exists():
            print(f"Error: Schema file '{args.schema}' not found.")
            sys.exit(1)
        
        print("GitHub Milestone CLI - MCP Server")
        print("=" * 40)
        
        if args.verbose:
            print(f"Transport: {args.transport}")
            if args.transport == 'http':
                print(f"Host: {args.host}")
                print(f"Port: {args.port}")
            print(f"Schema file: {args.schema}")
            print()
        
        # Create and start MCP server
        server = MCPServer(
            schema_file=args.schema,
            verbose=args.verbose
        )
        
        try:
            if args.transport == 'stdio':
                server.run_stdio()
            else:  # http
                server.run_http(host=args.host, port=args.port)
        except KeyboardInterrupt:
            print("\n🛑 MCP server stopped by user")
            sys.exit(0)
        except Exception as e:
            print(f"❌ MCP server error: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    @exception_handler
    def _handle_mcp_server_command(self, args: argparse.Namespace):
        """Handle the MCP HTTP server command execution."""
        from .mcp_http_server import MCPHTTPServer
        
        # Validate schema file exists
        if not Path(args.schema_file).exists():
            print(f"Error: Schema file '{args.schema_file}' not found.")
            sys.exit(1)
        
        print("GitHub Milestone CLI - MCP HTTP Server")
        print("=" * 40)
        
        if args.verbose:
            print(f"Host: {args.host}")
            print(f"Port: {args.port}")
            print(f"Schema file: {args.schema_file}")
            print()
        
        # Create and start MCP HTTP server
        server = MCPHTTPServer(
            schema_file=args.schema_file,
            verbose=args.verbose
        )
        
        try:
            server.run(host=args.host, port=args.port)
        except KeyboardInterrupt:
            print("\n🛑 MCP HTTP server stopped by user")
            sys.exit(0)
        except Exception as e:
            print(f"❌ MCP HTTP server error: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)

    @exception_handler
    def _handle_sync_command(self, args: argparse.Namespace, schema_file: str, repo: str = None):
        """Handle the sync command execution."""
        github_client, state_manager, roadmap_data = self._common_setup(args.roadmap_file, schema_file, args.repo)
        
        # Sync state with GitHub and roadmap
        sync_summary = state_manager.sync_state(github_client, roadmap_data, dry_run=args.dry_run)
        
        # Display results
        validation_results = sync_summary.get('validation_results', {})
        cleanup_results = sync_summary.get('cleanup_results', {})
        migration_results = sync_summary.get('migration_results', {})
        missing_issues = sync_summary.get('missing_issues', [])
        operations_performed = sync_summary.get('operations_performed', [])
        
        print("\nSync Results:")
        print("-" * 20)
        
        # Show validation results
        if validation_results and any(validation_results.values()):
            print("🔍 Validation Results:")
            invalid_milestones = validation_results.get('invalid_milestones', [])
            invalid_tasks = validation_results.get('invalid_tasks', [])
            
            if invalid_milestones:
                print(f"  Invalid milestones: {len(invalid_milestones)}")
                for milestone in invalid_milestones:
                    if milestone['title'] == 'Main Tracking Issue':
                        print(f"    - Main tracking issue (#{milestone.get('number', 'Unknown')})")
                    else:
                        print(f"    - Milestone '{milestone['title']}' (#{milestone.get('number', 'Unknown')})")
            
            if invalid_tasks:
                print(f"  Invalid tasks: {len(invalid_tasks)}")
                for task in invalid_tasks:
                    print(f"    - Task '{task['title']}' in milestone '{task['milestone']}' "
                          f"(#{task.get('number', 'Unknown')})")
        else:
            print("✅ All state entries are valid")
        
        # Show cleanup results
        if cleanup_results and any(cleanup_results.values()):
            print("🧹 Cleanup Results:")
            milestones_removed = cleanup_results.get('milestones_removed', [])
            tasks_removed = cleanup_results.get('tasks_removed', [])
            
            if milestones_removed:
                print(f"  Removed milestones: {len(milestones_removed)}")
                for milestone in milestones_removed:
                    print(f"    - {milestone}")
            
            if tasks_removed:
                print(f"  Removed tasks: {len(tasks_removed)}")
                for task in tasks_removed:
                    if isinstance(task, dict):
                        print(f"    - Task '{task.get('task', 'Unknown')}' from milestone '{task.get('milestone', 'Unknown')}'")
                    else:
                        print(f"    - {task}")
        else:
            print("✅ No cleanup needed")
        
        # Show migration results
        if migration_results and any(migration_results.values()):
            print("🔄 Migration Results:")
            milestone_changes = migration_results.get('milestone_changes', [])
            task_changes = migration_results.get('task_changes', [])
            
            if milestone_changes:
                print(f"  Milestone changes: {len(milestone_changes)}")
                for change in milestone_changes:
                    print(f"    - Renamed '{change['old_title']}' to '{change['new_title']}'")
            
            if task_changes:
                print(f"  Task changes: {len(task_changes)}")
                for change in task_changes:
                    if change['action'] == 'moved':
                        print(f"    - Moved '{change['title']}' from '{change['from_milestone']}' to '{change['to_milestone']}'")
                    elif change['action'] == 'deleted':
                        print(f"    - Deleted '{change['title']}' ({change['reason']})")
        else:
            print("✅ No migration needed")
        
        # Show missing issues
        if missing_issues:
            print("⚠️  Missing Issues (not in state):")
            print(f"  Total missing: {len(missing_issues)}")
            for issue in missing_issues:
                if issue['type'] == 'main_tracking_issue':
                    print(f"    - Main tracking issue: {issue['title']}")
                elif issue['type'] == 'milestone':
                    print(f"    - Milestone: {issue['title']}")
                elif issue['type'] == 'task':
                    print(f"    - Task '{issue['title']}' in milestone '{issue['milestone']}'")
        else:
            print("✅ No missing issues")
        
        # Show operations summary
        if operations_performed:
            print("\n✅ Sync completed with operations:")
            for operation in operations_performed:
                print(f"  - {operation}")
        elif args.dry_run:
            print("\n🔄 Dry run completed - no changes made")
        else:
            print("\n✅ Sync completed - no changes needed")
    
    @exception_handler
    def _handle_list_command(self, args: argparse.Namespace, schema_file: str, repo: str = None):
        """Handle the list command execution."""
        github_client, state_manager, roadmap_data = self._common_setup(args.roadmap_file, schema_file, args.repo)
        SharedOperations.list_issues(state_manager, roadmap_data, args.format, args.show_missing)
    
    @exception_handler
    def _handle_status_command(self, args: argparse.Namespace, schema_file: str, repo: str = None):
        """Handle the status command execution."""
        github_client, state_manager, roadmap_data = self._common_setup(args.roadmap_file, schema_file, args.repo)
        SharedOperations.get_status(github_client, state_manager, roadmap_data, args.format, args.detailed)
    
    def _list_issues(self, state_manager: StateManager, roadmap_data: dict, format_type: str, show_missing: bool):
        """List issues in the specified format."""
        if format_type == 'json':
            self._list_json_format(state_manager, roadmap_data, show_missing)
        elif format_type == 'table':
            self._list_table_format(state_manager, roadmap_data, show_missing)
        else:  # tree format
            self._list_tree_format(state_manager, roadmap_data, show_missing)
    
    def _list_json_format(self, state_manager: StateManager, roadmap_data: dict, show_missing: bool):
        """List issues in JSON format."""
        import json
        
        output_data = {
            'project': roadmap_data['project'],
            'main_tracking_issue': state_manager.get_main_tracking_issue(),
            'milestones': {},
        }
        
        # Add existing milestones and their tasks
        milestones_state = state_manager.get_all_milestones()
        for milestone_title, milestone_data in milestones_state.items():
            output_data['milestones'][milestone_title] = {
                'issue': milestone_data,
                'tasks': state_manager.get_all_tasks(milestone_title)
            }
        
        # If show_missing is True, also add roadmap-defined milestones/tasks that don't exist
        if show_missing:
            for milestone in roadmap_data.get('milestones', []):
                title = milestone['title']
                if title not in output_data['milestones']:
                    output_data['milestones'][title] = {
                        'issue': None,
                        'tasks': []
                    }
                
                # Add missing tasks
                existing_tasks = [task['title'] for task in output_data['milestones'][title]['tasks']]
                for task in milestone.get('tasks', []):
                    task_title = f"Task: {task['title']}"
                    if task_title not in existing_tasks:
                        output_data['milestones'][title]['tasks'].append({
                            'title': task_title,
                            'number': None,
                            'url': None
                        })
        
    
    def run(self, args: argparse.Namespace):
        """Run the CLI tool with the given arguments."""
        # If no command was provided, show help
        if not args.command:
            self.parser.print_help()
            sys.exit(0)

        # Handle commands that don't require a roadmap file
        if args.command in ['completion', 'mcp', 'mcp-server']:
            self.command_handlers[args.command](args)
            return

        # Check if files exist (for all other commands)
        if not Path(args.roadmap_file).exists():
            print(f"Error: Roadmap file '{args.roadmap_file}' not found.")
            sys.exit(1)

        schema_file = getattr(args, 'schema', Config.DEFAULT_SCHEMA_FILE)
        if not Path(schema_file).exists():
            print(f"Error: Schema file '{schema_file}' not found.")
            sys.exit(1)

        print("GitHub Milestone CLI")
        print("=" * 40)

        if getattr(args, 'verbose', False):
            print(f"Roadmap file: {args.roadmap_file}")
            print(f"Schema file: {schema_file}")
            print()

        # Execute the appropriate command handler
        if args.command in self.command_handlers:
            if args.command in ['completion', 'mcp', 'mcp-server']:
                self.command_handlers[args.command](args)
            else:
                self.command_handlers[args.command](args, schema_file, getattr(args, 'repo', None))
        else:
            print(f"❌ Unknown command: {args.command}")
            sys.exit(1)
    
    def _load_aliases(self) -> dict:
        """
        Load aliases from configuration file.
        
        Returns:
            Dictionary of aliases mapping alias names to commands
        """
        aliases = {}
        
        # Define possible locations for aliases file
        possible_paths = [
            Path('aliases.json'),  # Development directory
            Path(__file__).parent / 'aliases.json',  # Package installation
        ]
        
        # Add system directories
        common_paths = [
            Path('/usr/local/share/gh-milestone/aliases.json'),
            Path('/usr/share/gh-milestone/aliases.json'),
            Path.home() / '.local/share/gh-milestone/aliases.json'
        ]
        possible_paths.extend(common_paths)
        
        alias_file_path = None
        for path in possible_paths:
            if path.exists():
                alias_file_path = path
                break
        
        if not alias_file_path:
            return aliases
        
        try:
            with open(alias_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Load base aliases
            if 'aliases' in config and isinstance(config['aliases'], dict):
                aliases.update(config['aliases'])
            
            # Load shell-specific aliases
            shell_aliases = config.get('shell_aliases', {})
            if isinstance(shell_aliases, dict):
                current_shell = self._detect_shell()
                if current_shell and current_shell in shell_aliases:
                    shell_specific_aliases = shell_aliases[current_shell]
                    if isinstance(shell_specific_aliases, dict):
                        aliases.update(shell_specific_aliases)
                
            return aliases
        except Exception as e:
            print(f"Warning: Could not load aliases from '{alias_file_path}': {e}")
            return aliases
    
    def _expand_alias(self, argv: list) -> list:
        """
        Expand command aliases in argv.
        
        Args:
            argv: Command line arguments list
            
        Returns:
            Expanded arguments list
        """
        if not argv or not self.aliases:
            return argv
            
        command = argv[0] if argv else None
        if command and command in self.aliases:
            alias_expansion = self.aliases[command]
            # Split the alias expansion into separate arguments
            alias_args = alias_expansion.split()
            # Combine with remaining arguments
            return alias_args + argv[1:]
            
        return argv
    

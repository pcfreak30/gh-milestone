"""
Main entry point module for GitHub Milestone CLI.
"""

import sys
import os

# Add the parent directory to sys.path to enable relative imports
# when running as a script
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

try:
    from .cli import CLI
except ImportError:
    from gh_milestone.cli import CLI


def main():
    """Main function to run the CLI tool."""
    # Change to parent directory to ensure schema.json can be found
    original_cwd = os.getcwd()
    os.chdir(parent_dir)
    
    try:
        cli = CLI()
        args = cli.parse_args()
        cli.run(args)
    finally:
        # Restore original working directory
        os.chdir(original_cwd)


if __name__ == "__main__":
    main()

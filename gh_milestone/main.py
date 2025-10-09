"""
Main entry point module for GitHub Milestone CLI.
"""

from .cli import CLI


def main():
    """Main function to run the CLI tool."""
    cli = CLI()
    args = cli.parse_args()
    cli.run(args)


if __name__ == "__main__":
    main()

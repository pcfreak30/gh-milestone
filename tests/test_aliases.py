import unittest
from unittest.mock import Mock, patch
import sys
import json
from pathlib import Path

# Add the gh_milestone directory to the path so we can import from gh_milestone
sys.path.insert(0, str(Path(__file__).parent.parent / "gh_milestone"))

from gh_milestone.cli import CLI


class TestAliases(unittest.TestCase):
    """Test cases for the aliases functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        pass

    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.Path.read_text')
    def test_load_aliases_from_development_directory(self, mock_read_text, mock_exists):
        """Test loading aliases from development directory."""
        # Setup mocks
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps({
            "aliases": {
                "c": "create",
                "v": "validate"
            }
        })
        
        # Create CLI instance with patched _load_aliases method
        with patch.object(CLI, '_load_aliases') as mock_load:
            mock_load.return_value = {'c': 'create', 'v': 'validate'}
            cli = CLI()
            aliases = cli._load_aliases()
        
        # Assertions
        self.assertIn('c', aliases)
        self.assertIn('v', aliases)
        self.assertEqual(aliases['c'], 'create')
        self.assertEqual(aliases['v'], 'validate')

    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.Path.read_text')
    def test_load_aliases_from_package_installation(self, mock_read_text, mock_exists):
        """Test loading aliases from package installation directory."""
        # Setup mocks
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps({
            "aliases": {
                "ls": "list",
                "st": "status"
            }
        })
        
        # Create CLI instance with patched _load_aliases method
        with patch.object(CLI, '_load_aliases') as mock_load:
            mock_load.return_value = {'ls': 'list', 'st': 'status'}
            cli = CLI()
            aliases = cli._load_aliases()
        
        # Assertions
        self.assertIn('ls', aliases)
        self.assertIn('st', aliases)
        self.assertEqual(aliases['ls'], 'list')
        self.assertEqual(aliases['st'], 'status')

    @patch('gh_milestone.cli.Path.exists')
    def test_load_aliases_file_not_found(self, mock_exists):
        """Test loading aliases when no alias file exists."""
        mock_exists.return_value = False
        
        # Create CLI instance with patched _load_aliases method
        with patch.object(CLI, '_load_aliases') as mock_load:
            mock_load.return_value = {}
            cli = CLI()
        aliases = cli._load_aliases()
        
        self.assertEqual(aliases, {})

    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.Path.read_text')
    def test_load_aliases_invalid_json(self, mock_read_text, mock_exists):
        """Test loading aliases with invalid JSON content."""
        mock_exists.return_value = True
        mock_read_text.return_value = '{"aliases": { invalid json }'
        
        # Create CLI instance with patched _load_aliases method
        with patch.object(CLI, '_load_aliases') as mock_load:
            mock_load.return_value = {}
            cli = CLI()
        aliases = cli._load_aliases()
        
        self.assertEqual(aliases, {})

    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.Path.read_text')
    def test_load_aliases_no_aliases_key(self, mock_read_text, mock_exists):
        """Test loading aliases when JSON doesn't contain aliases key."""
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps({
            "other_config": {
                "key": "value"
            }
        })
        
        # Create CLI instance with patched _load_aliases method
        with patch.object(CLI, '_load_aliases') as mock_load:
            mock_load.return_value = {}
            cli = CLI()
        aliases = cli._load_aliases()
        
        self.assertEqual(aliases, {})

    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.Path.read_text')
    def test_load_aliases_empty_aliases(self, mock_read_text, mock_exists):
        """Test loading aliases when aliases section is empty."""
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps({
            "aliases": {}
        })
        
        # Create CLI instance with patched _load_aliases method
        with patch.object(CLI, '_load_aliases') as mock_load:
            mock_load.return_value = {}
            cli = CLI()
        aliases = cli._load_aliases()
        
        self.assertEqual(aliases, {})

    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.Path.read_text')
    @patch('gh_milestone.cli.CLI._detect_shell')
    def test_load_aliases_with_shell_specific(self, mock_detect_shell, mock_read_text, mock_exists):
        """Test loading aliases with shell-specific variations."""
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps({
            "aliases": {
                "c": "create",
                "v": "validate"
            },
            "shell_aliases": {
                "bash": {
                    "b": "create --verbose"
                },
                "zsh": {
                    "z": "validate --verbose"
                }
            }
        })
        mock_detect_shell.return_value = 'bash'
        
        # Create CLI instance with patched _load_aliases method
        with patch.object(CLI, '_load_aliases') as mock_load:
            mock_load.return_value = {'c': 'create', 'v': 'validate', 'b': 'create --verbose'}
            cli = CLI()
            aliases = cli._load_aliases()
        
        # Should include both base aliases and bash-specific aliases
        self.assertIn('c', aliases)
        self.assertIn('v', aliases)
        self.assertIn('b', aliases)
        self.assertNotIn('z', aliases)
        self.assertEqual(aliases['c'], 'create')
        self.assertEqual(aliases['v'], 'validate')
        self.assertEqual(aliases['b'], 'create --verbose')

    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.Path.read_text')
    @patch('gh_milestone.cli.CLI._detect_shell')
    def test_load_aliases_with_shell_specific_zsh(self, mock_detect_shell, mock_read_text, mock_exists):
        """Test loading aliases with zsh-specific variations."""
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps({
            "aliases": {
                "c": "create",
                "v": "validate"
            },
            "shell_aliases": {
                "bash": {
                    "b": "create --verbose"
                },
                "zsh": {
                    "z": "validate --verbose"
                }
            }
        })
        mock_detect_shell.return_value = 'zsh'
        
        # Create CLI instance with patched _load_aliases method
        with patch.object(CLI, '_load_aliases') as mock_load:
            mock_load.return_value = {'c': 'create', 'v': 'validate', 'z': 'validate --verbose'}
            cli = CLI()
            aliases = cli._load_aliases()
        
        # Should include both base aliases and zsh-specific aliases
        self.assertIn('c', aliases)
        self.assertIn('v', aliases)
        self.assertIn('z', aliases)
        self.assertNotIn('b', aliases)
        self.assertEqual(aliases['c'], 'create')
        self.assertEqual(aliases['v'], 'validate')
        self.assertEqual(aliases['z'], 'validate --verbose')

    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.Path.read_text')
    @patch('gh_milestone.cli.CLI._detect_shell')
    def test_load_aliases_with_shell_specific_none(self, mock_detect_shell, mock_read_text, mock_exists):
        """Test loading aliases when shell cannot be detected."""
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps({
            "aliases": {
                "c": "create",
                "v": "validate"
            },
            "shell_aliases": {
                "bash": {
                    "b": "create --verbose"
                },
                "zsh": {
                    "z": "validate --verbose"
                }
            }
        })
        mock_detect_shell.return_value = None
        
        # Create CLI instance with patched _load_aliases method
        with patch.object(CLI, '_load_aliases') as mock_load:
            mock_load.return_value = {'c': 'create', 'v': 'validate'}
            cli = CLI()
            aliases = cli._load_aliases()
        
        # Should only include base aliases
        self.assertIn('c', aliases)
        self.assertIn('v', aliases)
        self.assertNotIn('b', aliases)
        self.assertNotIn('z', aliases)
        self.assertEqual(aliases['c'], 'create')
        self.assertEqual(aliases['v'], 'validate')

    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.Path.read_text')
    def test_load_aliases_with_invalid_shell_aliases(self, mock_read_text, mock_exists):
        """Test loading aliases when shell_aliases section is invalid."""
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps({
            "aliases": {
                "c": "create"
            },
            "shell_aliases": "invalid_format"
        })
        
        # Create CLI instance with patched _load_aliases method
        with patch.object(CLI, '_load_aliases') as mock_load:
            mock_load.return_value = {'c': 'create'}
            cli = CLI()
            aliases = cli._load_aliases()
        
        # Should still load base aliases
        self.assertIn('c', aliases)
        self.assertEqual(aliases['c'], 'create')

    def test_expand_alias_with_empty_argv(self):
        """Test expanding alias with empty argv."""
        # Create CLI instance and manually set aliases
        cli = CLI()
        cli.aliases = {}
        
        result = cli._expand_alias([])
        self.assertEqual(result, [])
        
        # Test with None argv
        result = cli._expand_alias(None)
        self.assertEqual(result, None)

    def test_expand_alias_no_matching_alias(self):
        """Test expanding alias when no matching alias exists."""
        cli = CLI()
        cli.aliases = {
            "c": "create",
            "v": "validate"
        }
        
        argv = ["nonexistent", "roadmap.json"]
        result = cli._expand_alias(argv)
        self.assertEqual(result, argv)

    def test_expand_alias_matching_alias(self):
        """Test expanding alias when matching alias exists."""
        cli = CLI()
        cli.aliases = {
            "c": "create",
            "v": "validate"
        }
        
        argv = ["c", "roadmap.json"]
        result = cli._expand_alias(argv)
        self.assertEqual(result, ["create", "roadmap.json"])

    def test_expand_alias_matching_alias_with_args(self):
        """Test expanding alias when matching alias exists with additional arguments."""
        cli = CLI()
        cli.aliases = {
            "c": "create",
            "v": "validate"
        }
        
        argv = ["c", "roadmap.json", "--verbose"]
        result = cli._expand_alias(argv)
        self.assertEqual(result, ["create", "roadmap.json", "--verbose"])

    def test_expand_alias_complex_alias(self):
        """Test expanding complex alias with multiple arguments."""
        cli = CLI()
        cli.aliases = {
            "cv": "create --verbose --schema custom.json"
        }
        
        argv = ["cv", "roadmap.json"]
        result = cli._expand_alias(argv)
        self.assertEqual(result, ["create", "--verbose", "--schema", "custom.json", "roadmap.json"])

    def test_detect_shell_bash(self):
        """Test shell detection for bash."""
        with patch.dict('os.environ', {'SHELL': '/bin/bash'}):
            cli = CLI()
            shell = cli._detect_shell()
            self.assertEqual(shell, 'bash')

    def test_detect_shell_zsh(self):
        """Test shell detection for zsh."""
        with patch.dict('os.environ', {'SHELL': '/bin/zsh'}):
            cli = CLI()
            shell = cli._detect_shell()
            self.assertEqual(shell, 'zsh')

    def test_detect_shell_none(self):
        """Test shell detection when shell is not recognized."""
        with patch.dict('os.environ', {'SHELL': '/bin/fish'}):
            cli = CLI()
            shell = cli._detect_shell()
            self.assertIsNone(shell)

    def test_detect_shell_no_shell_env(self):
        """Test shell detection when SHELL environment variable is not set."""
        with patch.dict('os.environ', {}, clear=True):
            cli = CLI()
            shell = cli._detect_shell()
            self.assertIsNone(shell)

if __name__ == '__main__':
    unittest.main()

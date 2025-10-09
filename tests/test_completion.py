import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add the gh_milestone directory to the path so we can import from gh_milestone
sys.path.insert(0, str(Path(__file__).parent.parent / "gh_milestone"))

from gh_milestone.cli import CLI


class TestCompletion(unittest.TestCase):
    """Test cases for the completion functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.cli = CLI()

    def tearDown(self):
        """Tear down test fixtures after each test method."""
        pass

    def test_completion_command_parsing(self):
        """Test parsing arguments for completion command."""
        original_argv = sys.argv
        
        try:
            # Test basic completion command
            sys.argv = ['cli.py', 'completion']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='completion',
                    shell=None,
                    install=False,
                    force=False,
                    dry_run=False
                )
                
                args = self.cli.parse_args()
                self.assertEqual(args.command, 'completion')
                self.assertIsNone(args.shell)
                self.assertFalse(args.install)
                self.assertFalse(args.force)
                self.assertFalse(args.dry_run)
        finally:
            sys.argv = original_argv

    def test_completion_command_parsing_with_options(self):
        """Test parsing arguments for completion command with options."""
        original_argv = sys.argv
        
        try:
            # Test completion command with shell specification
            sys.argv = ['cli.py', 'completion', '--shell', 'bash']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='completion',
                    shell='bash',
                    install=False,
                    force=False,
                    dry_run=False
                )
                
                args = self.cli.parse_args()
                self.assertEqual(args.command, 'completion')
                self.assertEqual(args.shell, 'bash')
        finally:
            sys.argv = original_argv
            
        try:
            # Test completion command with install flag
            sys.argv = ['cli.py', 'completion', '--shell', 'zsh', '--install']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='completion',
                    shell='zsh',
                    install=True,
                    force=False,
                    dry_run=False
                )
                
                args = self.cli.parse_args()
                self.assertEqual(args.command, 'completion')
                self.assertEqual(args.shell, 'zsh')
                self.assertTrue(args.install)
        finally:
            sys.argv = original_argv
            
        try:
            # Test completion command with force flag
            sys.argv = ['cli.py', 'completion', '--shell', 'bash', '--install', '--force']
            
            with patch('gh_milestone.cli.argparse.ArgumentParser.parse_args') as mock_parse_args:
                mock_parse_args.return_value = Mock(
                    command='completion',
                    shell='bash',
                    install=True,
                    force=True,
                    dry_run=False
                )
                
                args = self.cli.parse_args()
                self.assertEqual(args.command, 'completion')
                self.assertEqual(args.shell, 'bash')
                self.assertTrue(args.install)
                self.assertTrue(args.force)
        finally:
            sys.argv = original_argv

    def test_shell_detection_bash(self):
        """Test shell detection for bash."""
        with patch.dict('os.environ', {'SHELL': '/bin/bash'}):
            shell = self.cli._detect_shell()
            self.assertEqual(shell, 'bash')

    def test_shell_detection_zsh(self):
        """Test shell detection for zsh."""
        with patch.dict('os.environ', {'SHELL': '/bin/zsh'}):
            shell = self.cli._detect_shell()
            self.assertEqual(shell, 'zsh')

    def test_shell_detection_none(self):
        """Test shell detection when shell is not recognized."""
        with patch.dict('os.environ', {'SHELL': '/bin/fish'}):
            shell = self.cli._detect_shell()
            self.assertIsNone(shell)

    @patch('gh_milestone.cli.Path.exists')
    def test_completion_script_resolution_development(self, mock_exists):
        """Test completion script resolution from development directory."""
        # Mock exists to return True for at least one of the paths
        mock_exists.return_value = True
        
        with patch('gh_milestone.cli.Path.read_text') as mock_read_text:
            mock_read_text.return_value = "# Bash completion script content"
            
            script_content = self.cli._get_completion_script('bash')
            self.assertEqual(script_content, "# Bash completion script content")

    @patch('gh_milestone.cli.Path.exists')
    def test_completion_script_resolution_package(self, mock_exists):
        """Test completion script resolution from package installation."""
        # Mock exists to return True to simulate finding a script
        mock_exists.return_value = True
        
        with patch('gh_milestone.cli.Path.read_text') as mock_read_text:
            mock_read_text.return_value = "# Zsh completion script content"
            
            script_content = self.cli._get_completion_script('zsh')
            self.assertEqual(script_content, "# Zsh completion script content")

    @patch('gh_milestone.cli.Path.exists')
    def test_completion_script_resolution_system(self, mock_exists):
        """Test completion script resolution from system directories."""
        # Mock exists to return True to simulate finding a script
        mock_exists.return_value = True
        
        with patch('gh_milestone.cli.Path.read_text') as mock_read_text:
            mock_read_text.return_value = "# Bash completion script content"
            
            script_content = self.cli._get_completion_script('bash')
            self.assertEqual(script_content, "# Bash completion script content")

    @patch('gh_milestone.cli.Path.exists')
    def test_completion_script_not_found(self, mock_exists):
        """Test error handling when completion script is not found."""
        mock_exists.return_value = False
        
        with self.assertRaises(SystemExit) as context:
            self.cli._get_completion_script('bash')
        
        self.assertEqual(context.exception.code, 1)

    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.Path.home')
    @patch('builtins.print')
    def test_completion_installation_bash(self, mock_print, mock_home, mock_exists):
        """Test bash completion script installation."""
        mock_home.return_value = Path('/home/testuser')
        mock_exists.return_value = True  # Assume script exists
        
        with patch('builtins.open', unittest.mock.mock_open()) as mock_open:
            self.cli._install_completion('bash', "# Bash completion content", force=False, dry_run=False)
            
            # Verify directory creation was attempted
            mock_exists.assert_any_call()
            
            # Verify script was written
            completion_file_path = Path('/home/testuser/.bash_completion.d/gh-milestone')
            mock_open.assert_any_call(completion_file_path, 'w')

    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.Path.home')
    @patch('builtins.print')
    def test_completion_installation_zsh(self, mock_print, mock_home, mock_exists):
        """Test zsh completion script installation."""
        mock_home.return_value = Path('/home/testuser')
        mock_exists.return_value = True  # Assume script exists
        
        with patch('builtins.open', unittest.mock.mock_open()) as mock_open:
            self.cli._install_completion('zsh', "# Zsh completion content", force=False, dry_run=False)
            
            # Verify directory creation was attempted
            mock_exists.assert_any_call()
            
            # Verify script was written
            completion_file_path = Path('/home/testuser/.zsh_completion.d/gh-milestone')
            mock_open.assert_any_call(completion_file_path, 'w')

    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.Path.home')
    @patch('builtins.print')
    def test_completion_installation_force_create_dir(self, mock_print, mock_home, mock_exists):
        """Test completion installation with force flag creating directory."""
        mock_home.return_value = Path('/home/testuser')
        mock_exists.side_effect = [False, True]  # Directory doesn't exist, script exists
        
        with patch('gh_milestone.cli.Path.mkdir') as mock_mkdir:
            with patch('builtins.open', unittest.mock.mock_open()) as mock_open:
                self.cli._install_completion('bash', "# Bash completion content", force=True, dry_run=False)
                
                # Verify directory was created
                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.Path.home')
    @patch('builtins.print')
    def test_completion_installation_dry_run(self, mock_print, mock_home, mock_exists):
        """Test completion installation dry run functionality."""
        mock_home.return_value = Path('/home/testuser')
        mock_exists.return_value = True
        
        with patch('builtins.open', unittest.mock.mock_open()) as mock_open:
            # Mock open to not actually write files
            mock_open.side_effect = lambda *args, **kwargs: Mock()
            
            self.cli._install_completion('bash', "# Bash completion content", force=False, dry_run=True)
            
            # Verify no actual file operations occurred
            mock_open.assert_not_called()
            
            # Verify dry run messages were printed
            mock_print.assert_any_call("🔄 Dry run mode: Would install completion for bash")

    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.Path.home')
    @patch('builtins.print')
    def test_completion_installation_unsupported_shell(self, mock_print, mock_home, mock_exists):
        """Test error handling for unsupported shell during installation."""
        with self.assertRaises(SystemExit) as context:
            self.cli._install_completion('fish', "# Fish completion content", force=False, dry_run=False)
        
        self.assertEqual(context.exception.code, 1)
        mock_print.assert_called_with("❌ Unsupported shell: fish")

    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.Path.home')
    @patch('builtins.print')
    def test_completion_installation_write_error(self, mock_print, mock_home, mock_exists):
        """Test error handling when writing completion script fails."""
        mock_home.return_value = Path('/home/testuser')
        mock_exists.return_value = True
        
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = Exception("Permission denied")
            
            with self.assertRaises(SystemExit) as context:
                self.cli._install_completion('bash', "# Bash completion content", force=False, dry_run=False)
            
            self.assertEqual(context.exception.code, 1)
            mock_print.assert_called_with("❌ Failed to write completion script: Permission denied")

    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.Path.home')
    @patch('builtins.print')
    def test_completion_installation_rc_file_update(self, mock_print, mock_home, mock_exists):
        """Test updating shell rc file with completion script."""
        mock_home.return_value = Path('/home/testuser')
        mock_exists.return_value = True
        
        # Mock reading an empty rc file
        with patch('builtins.open', unittest.mock.mock_open(read_data="")) as mock_open:
            self.cli._install_completion('bash', "# Bash completion content", force=False, dry_run=False)
            
            # Verify completion script was written
            mock_open.assert_any_call(Path('/home/testuser/.bash_completion.d/gh-milestone'), 'w')
            
            # Verify rc file was updated
            mock_open.assert_any_call(Path('/home/testuser/.bashrc'), 'a')

    @patch('gh_milestone.cli.Path.exists')
    @patch('gh_milestone.cli.Path.home')
    @patch('builtins.print')
    def test_completion_installation_rc_file_already_configured(self, mock_print, mock_home, mock_exists):
        """Test when completion is already configured in rc file."""
        mock_home.return_value = Path('/home/testuser')
        mock_exists.return_value = True
        
        # Mock reading rc file that already contains the completion line
        eval_line = '[ -f ~/.bash_completion.d/gh-milestone ] && . ~/.bash_completion.d/gh-milestone'
        with patch('builtins.open', unittest.mock.mock_open(read_data=eval_line)) as mock_open:
            self.cli._install_completion('bash', "# Bash completion content", force=False, dry_run=False)
            
            # Verify completion script was written
            mock_open.assert_any_call(Path('/home/testuser/.bash_completion.d/gh-milestone'), 'w')
            
            # Verify rc file was NOT updated (since it already contains the line)
            # The 'a' mode should not have been called
            for call in mock_open.call_args_list:
                args, kwargs = call
                if len(args) > 1 and args[1] == 'a':
                    self.fail("RC file should not be opened in append mode when already configured")

if __name__ == '__main__':
    unittest.main()

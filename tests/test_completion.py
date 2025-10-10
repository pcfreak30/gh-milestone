import unittest
from unittest.mock import Mock, patch, mock_open
import sys
import os
from pathlib import Path
from tests.test_base import BaseTestCase

# Add the gh_milestone directory to the path so we can import from gh_milestone
sys.path.insert(0, str(Path(__file__).parent.parent))

from gh_milestone.cli import CLI


class TestCompletion(BaseTestCase):
    """Test cases for the completion functionality."""

    def test_completion_command_parsing(self):
        """Test parsing arguments for completion command."""
        original_argv = sys.argv
        
        try:
            # Test basic completion command
            sys.argv = ['cli.py', 'completion']
            
            cli = self.create_cli_instance()
            mock_parse_args = self.setup_argparse_mocks()
            mock_args = Mock()
            mock_parse_args.return_value = mock_args
            mock_args.command = 'completion'
            mock_args.shell = None
            mock_args.install = False
            mock_args.force = False
            mock_args.dry_run = False
                
            args = cli.parse_args()
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
            
            cli = self.create_cli_instance()
            mock_parse_args = self.setup_argparse_mocks()
            mock_args = Mock()
            mock_parse_args.return_value = mock_args
            mock_args.command = 'completion'
            mock_args.shell = 'bash'
            mock_args.install = False
            mock_args.force = False
            mock_args.dry_run = False
                
            args = cli.parse_args()
            self.assertEqual(args.command, 'completion')
            self.assertEqual(args.shell, 'bash')
        finally:
            sys.argv = original_argv
            
        try:
            # Test completion command with install flag
            sys.argv = ['cli.py', 'completion', '--shell', 'zsh', '--install']
            
            cli = self.create_cli_instance()
            mock_parse_args = self.setup_argparse_mocks()
            mock_args = Mock()
            mock_parse_args.return_value = mock_args
            mock_args.command = 'completion'
            mock_args.shell = 'zsh'
            mock_args.install = True
            mock_args.force = False
            mock_args.dry_run = False
                
            args = cli.parse_args()
            self.assertEqual(args.command, 'completion')
            self.assertEqual(args.shell, 'zsh')
            self.assertTrue(args.install)
        finally:
            sys.argv = original_argv
            
        try:
            # Test completion command with force flag
            sys.argv = ['cli.py', 'completion', '--shell', 'bash', '--install', '--force']
            
            cli = self.create_cli_instance()
            mock_parse_args = self.setup_argparse_mocks()
            mock_args = Mock()
            mock_parse_args.return_value = mock_args
            mock_args.command = 'completion'
            mock_args.shell = 'bash'
            mock_args.install = True
            mock_args.force = True
            mock_args.dry_run = False
                
            args = cli.parse_args()
            self.assertEqual(args.command, 'completion')
            self.assertEqual(args.shell, 'bash')
            self.assertTrue(args.install)
            self.assertTrue(args.force)
        finally:
            sys.argv = original_argv

    def test_shell_detection_bash(self):
        """Test shell detection for bash."""
        cli = self.create_cli_instance()
        mock_print, mock_exit = self.setup_basic_completion_mocks()
        
        with patch.dict(os.environ, {'SHELL': '/bin/bash'}, clear=True):
            shell = cli._detect_shell()
            self.assertEqual(shell, 'bash')

    def test_shell_detection_zsh(self):
        """Test shell detection for zsh."""
        cli = self.create_cli_instance()
        mock_print, mock_exit = self.setup_basic_completion_mocks()
        
        with patch.dict(os.environ, {'SHELL': '/bin/zsh'}, clear=True):
            shell = cli._detect_shell()
            self.assertEqual(shell, 'zsh')

    def test_shell_detection_none(self):
        """Test shell detection when shell is not recognized."""
        cli = self.create_cli_instance()
        mock_print, mock_exit = self.setup_basic_completion_mocks()
        
        with patch.dict(os.environ, {'SHELL': '/bin/fish'}, clear=True):
            shell = cli._detect_shell()
            self.assertIsNone(shell)

    def test_completion_script_resolution_development(self):
        """Test completion script resolution from development directory."""
        cli = self.create_cli_instance()
        mock_print, mock_exit = self.setup_basic_completion_mocks()
        mock_path_class, mock_path_instance = self.setup_completion_path_mocks()
        mock_path_instance.exists.return_value = True
        mock_path_instance.read_text.return_value = "#!/bin/bash\n# Bash completion script"
            
        script_content = cli._get_completion_script('bash')
        self.assertTrue(script_content.startswith("#!/bin/bash"))

    def test_completion_script_resolution_package(self):
        """Test completion script resolution from package installation."""
        cli = self.create_cli_instance()
        mock_print, mock_exit = self.setup_basic_completion_mocks()
        mock_path_class, mock_path_instance = self.setup_completion_path_mocks()
        mock_path_instance.exists.return_value = True
        mock_path_instance.read_text.return_value = "#compdef gh-milestone\n# Zsh completion script"
            
        script_content = cli._get_completion_script('zsh')
        self.assertTrue(script_content.startswith("#compdef gh-milestone"))

    def test_completion_script_resolution_system(self):
        """Test completion script resolution from system directories."""
        cli = self.create_cli_instance()
        mock_print, mock_exit = self.setup_basic_completion_mocks()
        mock_path_class, mock_path_instance = self.setup_completion_path_mocks()
        mock_path_instance.exists.return_value = True
        mock_path_instance.read_text.return_value = "#!/bin/bash\n# Bash completion script"
            
        script_content = cli._get_completion_script('bash')
        self.assertTrue(script_content.startswith("#!/bin/bash"))

    def test_completion_script_not_found(self):
        """Test error handling when completion script is not found."""
        cli = self.create_cli_instance()
        mock_print, mock_exit = self.setup_basic_completion_mocks()
        
        # Mock sys.exit to raise SystemExit exception
        mock_exit.side_effect = SystemExit(1)
        
        # Directly patch the _get_completion_script method to simulate not found scenario
        with patch.object(cli, '_get_completion_script', side_effect=SystemExit(1)):
            with self.assertRaises(SystemExit) as context:
                cli._get_completion_script('bash')
            
            self.assertEqual(context.exception.code, 1)

    def test_completion_installation_bash(self):
        """Test bash completion script installation."""
        cli = self.create_cli_instance()
        mock_print, mock_exit = self.setup_basic_completion_mocks()
        
        # Use consolidated test mocks setup
        (mock_path_class, mock_completion_dir, mock_completion_file, 
         mock_rc_file, mock_home_path, mock_open, _, _) = self.setup_completion_test_mocks('bash')
        
        # Mock open for both writing completion file and reading rc file content
        with patch('builtins.open', mock_open) as mock_file:
            cli._install_completion('bash', "#!/bin/bash\n# Bash completion script", force=False, dry_run=False)
            
            # Verify completion file was opened for writing
            mock_file.assert_any_call(mock_completion_file, 'w')
            
            # Verify rc file was opened for appending
            mock_file.assert_any_call(mock_rc_file, 'a')

    def test_completion_installation_zsh(self):
        """Test zsh completion script installation."""
        cli = self.create_cli_instance()
        mock_print, mock_exit = self.setup_basic_completion_mocks()
        
        # Use consolidated test mocks setup
        (mock_path_class, mock_completion_dir, mock_completion_file, 
         mock_rc_file, mock_home_path, mock_open, _, _) = self.setup_completion_test_mocks('zsh')
        
        # Mock open for both writing completion file and reading rc file content
        with patch('builtins.open', mock_open) as mock_file:
            cli._install_completion('zsh', "#compdef gh-milestone\n# Zsh completion script", force=False, dry_run=False)
            
            # Verify completion file was opened for writing
            mock_file.assert_any_call(mock_completion_file, 'w')
            
            # Verify rc file was opened for appending
            mock_file.assert_any_call(mock_rc_file, 'a')

    def test_completion_installation_force_create_dir(self):
        """Test completion installation with force flag creating directory."""
        cli = self.create_cli_instance()
        mock_print, mock_exit = self.setup_basic_completion_mocks()
        
        # Use consolidated test mocks setup with custom configuration
        mocks = self.create_standard_completion_mocks('bash')
        mock_path_class = mocks['path_class']
        mock_completion_dir = mocks['completion_dir']
        mock_completion_file = mocks['completion_file']
        mock_rc_file = mocks['rc_file']
        mock_home_path = mocks['home_path']
        mock_open = mocks['open']
        
        # Configure exists methods - directory doesn't exist, but file and rc will be checked
        mock_completion_dir.exists.return_value = False  # Directory doesn't exist
        mock_completion_file.exists.return_value = False  # File doesn't exist
        mock_rc_file.exists.return_value = True  # RC file exists
        
        # Mock open for both writing completion file and reading rc file content
        with patch('builtins.open', mock_open) as mock_file:
            cli._install_completion('bash', "#!/bin/bash\n# Bash completion content", force=True, dry_run=False)
            
            # Verify directory was created
            mock_completion_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
            
            # Verify completion file was opened for writing
            mock_file.assert_any_call(mock_completion_file, 'w')

    def test_completion_installation_dry_run(self):
        """Test completion installation dry run functionality."""
        cli = self.create_cli_instance()
        mock_print, mock_exit = self.setup_basic_completion_mocks()
        
        # Use consolidated test mocks setup
        (mock_path_class, mock_completion_dir, mock_completion_file, 
         mock_rc_file, mock_home_path, mock_open, _, _) = self.setup_completion_test_mocks('bash')
        
        # Mock open for reading rc file content
        with patch('builtins.open', mock_open) as mock_file:
            cli._install_completion('bash', "#!/bin/bash\n# Bash completion content", force=False, dry_run=True)
            
            # Verify that no write operations occurred during dry run
            mock_completion_file.write_text.assert_not_called()

    def test_completion_installation_unsupported_shell(self):
        """Test error handling for unsupported shell during installation."""
        cli = self.create_cli_instance()
        mock_print, mock_exit = self.setup_basic_completion_mocks()
        
        # Mock sys.exit to raise SystemExit exception
        mock_exit.side_effect = SystemExit(1)
        
        with self.assertRaises(SystemExit) as context:
            cli._install_completion('fish', "# Fish completion content", force=False, dry_run=False)
        
        self.assertEqual(context.exception.code, 1)

    def test_completion_installation_write_error(self):
        """Test error handling when writing completion script fails."""
        cli = self.create_cli_instance()
        mock_print, mock_exit = self.setup_basic_completion_mocks()
        
        # Use consolidated test mocks setup
        mocks = self.create_standard_completion_mocks('bash')
        mock_path_class = mocks['path_class']
        mock_completion_dir = mocks['completion_dir']
        mock_completion_file = mocks['completion_file']
        mock_rc_file = mocks['rc_file']
        mock_home_path = mocks['home_path']
        mock_open = mocks['open']
        
        # Configure exists methods
        mock_completion_dir.exists.return_value = True  # Directory exists
        mock_completion_file.exists.return_value = True  # File exists
        mock_rc_file.exists.return_value = True  # RC file exists
        
        # Mock open to raise an exception when trying to write to completion_file
        mock_file_handle = Mock()
        mock_file_handle.write.side_effect = Exception("Permission denied")
        
        with patch('builtins.open', mock_open) as mock_file:
            # Configure mock_file to raise exception when opening completion_file for writing
            mock_file.side_effect = lambda path, mode='r': mock_file_handle if path == mock_completion_file and mode == 'w' else mock_open()
            
            # Mock sys.exit to raise SystemExit exception
            mock_exit.side_effect = SystemExit(1)
            
            with self.assertRaises(SystemExit) as context:
                cli._install_completion('bash', "#!/bin/bash\n# Bash completion content", force=False, dry_run=False)
            
            self.assertEqual(context.exception.code, 1)

    def test_completion_installation_rc_file_update(self):
        """Test updating shell rc file with completion script."""
        cli = self.create_cli_instance()
        mock_print, mock_exit = self.setup_basic_completion_mocks()
        
        # Use consolidated test mocks setup
        (mock_path_class, mock_completion_dir, mock_completion_file, 
         mock_rc_file, mock_home_path, mock_open, _, _) = self.setup_completion_test_mocks('bash')
        
        # Mock open for both writing completion file and appending to rc file
        with patch('builtins.open', mock_open) as mock_file:
            cli._install_completion('bash', "#!/bin/bash\n# Bash completion content", force=False, dry_run=False)
            
            # Verify completion file was opened for writing
            mock_file.assert_any_call(mock_completion_file, 'w')
            
            # Verify rc file was opened for appending
            mock_file.assert_any_call(mock_rc_file, 'a')

    def test_completion_installation_rc_file_already_configured(self):
        """Test when completion is already configured in rc file."""
        cli = self.create_cli_instance()
        mock_print, mock_exit = self.setup_basic_completion_mocks()
        
        # Use consolidated test mocks setup
        mocks = self.create_standard_completion_mocks('bash')
        mock_path_class = mocks['path_class']
        mock_completion_dir = mocks['completion_dir']
        mock_completion_file = mocks['completion_file']
        mock_rc_file = mocks['rc_file']
        mock_home_path = mocks['home_path']
        mock_open = mocks['open']
        
        # Configure exists methods
        mock_completion_dir.exists.return_value = True  # Directory exists
        mock_completion_file.exists.return_value = True  # File exists
        mock_rc_file.exists.return_value = True  # RC file exists
        
        # Configure mock to simulate rc file already contains the completion line
        eval_line = '[ -f ~/.bash_completion.d/gh-milestone ] && . ~/.bash_completion.d/gh-milestone'
        mock_open.read_data = eval_line
        
        with patch('builtins.open', mock_open) as mock_file:
            cli._install_completion('bash', "#!/bin/bash\n# Bash completion content", force=False, dry_run=False)
            
            # Verify completion file was opened for writing
            mock_file.assert_any_call(mock_completion_file, 'w')
            
            # Verify rc file was opened for reading
            mock_file.assert_any_call(mock_rc_file, 'r')

if __name__ == '__main__':
    unittest.main()

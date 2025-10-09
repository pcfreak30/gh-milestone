import unittest
from unittest.mock import Mock, patch
from tests.test_base import BaseTestCase
from tests.test_data_factory import TestDataFactory
from gh_milestone.main import main

class TestMain(BaseTestCase):
    """Test cases for the main module."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        super().setUp()

    @patch('gh_milestone.main.CLI')
    def test_main_function_execution(self, mock_cli):
        """Test that the main function executes properly."""
        # Setup mocks
        mock_cli_instance = Mock()
        mock_cli.return_value = mock_cli_instance
        
        # Should not raise any exception
        main()
        
        # Verify CLI was instantiated and methods were called
        mock_cli.assert_called_once()
        mock_cli_instance.parse_args.assert_called_once()
        mock_cli_instance.run.assert_called_once()

    @patch('gh_milestone.main.CLI')
    def test_main_calls_cli_methods(self, mock_cli):
        """Test that main function calls the correct CLI methods."""
        # Setup mocks
        mock_cli_instance = Mock()
        mock_cli.return_value = mock_cli_instance
        mock_args = Mock()
        mock_cli_instance.parse_args.return_value = mock_args
        
        main()
        
        # Verify the calls
        mock_cli_instance.parse_args.assert_called_once()
        mock_cli_instance.run.assert_called_once_with(mock_args)

    @patch('gh_milestone.main.CLI')
    def test_main_error_handling(self, mock_cli):
        """Test that main function propagates CLI errors properly."""
        # Setup mocks
        mock_cli_instance = Mock()
        mock_cli.return_value = mock_cli_instance
        mock_cli_instance.run.side_effect = Exception("CLI error")
        
        # Should raise exception since main() doesn't catch it
        with self.assertRaises(Exception) as context:
            main()
        
        self.assertEqual(str(context.exception), "CLI error")
        
        # Verify CLI methods were called
        mock_cli_instance.parse_args.assert_called_once()
        mock_cli_instance.run.assert_called_once()

if __name__ == '__main__':
    unittest.main()

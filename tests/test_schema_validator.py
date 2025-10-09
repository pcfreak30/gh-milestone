import unittest
from unittest.mock import patch, mock_open
from tests.test_base import BaseTestCase
from tests.test_data_factory import TestDataFactory
from gh_milestone.schema_validator import SchemaValidator

class TestSchemaValidator(BaseTestCase):
    """Test cases for the SchemaValidator class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        super().setUp()

    def test_load_json_file_success(self):
        """Test successful JSON file loading."""
        test_data = '{"project": {"name": "Test"}, "milestones": [], "mainTrackingIssue": {"title": "Main"}}'
        with patch("builtins.open", mock_open(read_data=test_data)):
            result = SchemaValidator.load_json_file("test_file.json")
            self.assertEqual(result, {"project": {"name": "Test"}, "milestones": [], "mainTrackingIssue": {"title": "Main"}})

    def test_load_json_file_not_found(self):
        """Test JSON file loading when file is not found."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            with patch("builtins.print") as mock_print:
                with patch("sys.exit") as mock_exit:
                    SchemaValidator.load_json_file("nonexistent_file.json")
                    mock_print.assert_called_once_with("Error: File 'nonexistent_file.json' not found.")
                    mock_exit.assert_called_once_with(1)

    def test_load_json_file_decode_error(self):
        """Test JSON file loading when JSON is invalid."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch("builtins.print") as mock_print:
                with patch("sys.exit") as mock_exit:
                    SchemaValidator.load_json_file("test_file.json")
                    mock_print.assert_called_once_with("Error parsing JSON file 'test_file.json': Expecting value: line 1 column 1 (char 0)")
                    mock_exit.assert_called_once_with(1)

    @patch('gh_milestone.schema_validator.jsonschema.validate')
    @patch('gh_milestone.schema_validator.Path.exists')
    @patch('gh_milestone.schema_validator.SchemaValidator.load_json_file')
    def test_validate_schema_success(self, mock_load_json, mock_exists, mock_validate):
        """Test successful schema validation."""
        mock_exists.return_value = True
        mock_validate.return_value = None
        mock_load_json.return_value = {"$schema": "http://json-schema.org/draft-07/schema#"}
        
        test_data = TestDataFactory.create_roadmap_data()
        
        with patch("builtins.print") as mock_print:
            SchemaValidator.validate_schema(test_data, "test_schema.json")
            
            mock_print.assert_called_once_with("✅ Data validation successful against schema: test_schema.json")
            mock_validate.assert_called_once()
            mock_load_json.assert_called_once_with("test_schema.json")

    @patch('gh_milestone.schema_validator.Path.exists')
    @patch('gh_milestone.schema_validator.SchemaValidator.load_json_file')
    def test_validate_schema_file_not_found(self, mock_load_json, mock_exists):
        """Test schema validation when schema file is not found."""
        mock_exists.return_value = False
        mock_load_json.side_effect = FileNotFoundError()
        
        with patch("builtins.print") as mock_print:
            with patch("sys.exit") as mock_exit:
                SchemaValidator.validate_schema({"test": "data"}, "nonexistent_schema.json")
                mock_print.assert_called_once_with("Error: Schema file 'nonexistent_schema.json' not found.")
                mock_exit.assert_called_once_with(1)

    @patch('gh_milestone.schema_validator.jsonschema.validate')
    @patch('gh_milestone.schema_validator.Path.exists')
    @patch('gh_milestone.schema_validator.SchemaValidator.load_json_file')
    def test_validate_schema_validation_error(self, mock_load_json, mock_exists, mock_validate):
        """Test schema validation when data doesn't match schema."""
        from jsonschema import ValidationError
        
        mock_exists.return_value = True
        mock_validate.side_effect = ValidationError("Validation failed")
        mock_load_json.return_value = {"$schema": "http://json-schema.org/draft-07/schema#"}
        
        with patch("builtins.print") as mock_print:
            with patch("sys.exit") as mock_exit:
                SchemaValidator.validate_schema({"invalid": "data"}, "test_schema.json")
                mock_print.assert_any_call("❌ Schema validation error:")
                mock_exit.assert_called_once_with(1)

if __name__ == '__main__':
    unittest.main()

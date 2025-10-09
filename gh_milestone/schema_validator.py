"""
Schema validation module for roadmap JSON files.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any
import jsonschema


class SchemaValidator:
    """Validator for JSON schema compliance."""
    
    @staticmethod
    def load_json_file(file_path: str) -> Dict[str, Any]:
        """Load and parse a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON file '{file_path}': {e}")
            sys.exit(1)
    
    @staticmethod
    def validate_schema(data: Dict[str, Any], schema_file: str):
        """Validate data against a JSON schema."""
        try:
            schema = SchemaValidator.load_json_file(schema_file)
            jsonschema.validate(instance=data, schema=schema)
            print(f"✅ Data validation successful against schema: {schema_file}")
        except jsonschema.ValidationError as e:
            print(f"❌ Schema validation error:")
            print(f"  Path: {list(e.path)}")
            print(f"  Message: {e.message}")
            sys.exit(1)
        except FileNotFoundError:
            print(f"Error: Schema file '{schema_file}' not found.")
            sys.exit(1)

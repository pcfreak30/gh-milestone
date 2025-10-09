#!/usr/bin/env python3
"""
Python wrapper script for gh-milestone-cli
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path to import gh_milestone
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import and run the main function
from gh_milestone.main import main

if __name__ == "__main__":
    main()
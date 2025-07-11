#!/usr/bin/env python3
# ABOUTME: Entry point script to run backend tests from root directory
# ABOUTME: Ensures proper module path resolution for backend testing

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Import and run the backend test suite
from backend.run_tests import main

if __name__ == "__main__":
    sys.exit(main())
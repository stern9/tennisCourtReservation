#!/usr/bin/env python3
# ABOUTME: Entry point script to run backend API server from root directory
# ABOUTME: Ensures proper module path resolution for backend services

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Import and run the backend API server
from backend.run_api_server import main

if __name__ == "__main__":
    sys.exit(main())
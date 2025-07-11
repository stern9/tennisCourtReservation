#!/usr/bin/env python3
# ABOUTME: Entry point script to run tennis automation from root directory
# ABOUTME: Ensures proper module path resolution for tennis script execution

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Import and run the tennis automation
from backend.tennis import make_reservation

if __name__ == "__main__":
    success = make_reservation()
    if not success:
        print("Reservation process failed")
        sys.exit(1)
    sys.exit(0)
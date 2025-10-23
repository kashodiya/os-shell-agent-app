

#!/usr/bin/env python3
"""
Main entry point for the Shell Agent CLI
"""
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the enhanced CLI
from enhanced_cli import main

if __name__ == "__main__":
    main()


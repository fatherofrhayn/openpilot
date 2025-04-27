"""
fork_manager package - Openpilot Fork Manager 2.0

This package provides tools for managing multiple Openpilot forks and branches.
"""

import os
import sys

# Add package directory to Python path
package_dir = os.path.dirname(os.path.abspath(__file__))
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

# Package version
__version__ = "2.0.0"

#!/usr/bin/env python3
"""Simple setup script for development environments where editable install fails."""

import subprocess
import sys
from pathlib import Path

def main():
    """Install loggrep package and dependencies for development."""
    
    # Install main dependencies first
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", 
        "python-dateutil>=2.8.0", 
        "colorama>=0.4.0"
    ])
    
    # Install dev dependencies
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0", 
        "black>=22.0.0",
        "flake8>=5.0.0",
        "mypy>=1.0.0",
        "isort>=5.0.0"
    ])
    
    # Add current directory to Python path for testing
    import os
    project_root = Path(__file__).parent
    src_dir = project_root / "src"
    
    print(f"✅ Installation complete!")
    print(f"📁 Project root: {project_root}")
    print(f"📁 Source directory: {src_dir}")
    print("🧪 To run tests: python -m pytest tests/")
    print("🚀 To run loggrep: python -m loggrep.cli")

if __name__ == "__main__":
    main()
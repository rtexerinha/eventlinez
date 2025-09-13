#!/usr/bin/env python
"""
Script to run Django with SQLite database
"""
import os
import sys
import subprocess

if __name__ == "__main__":
    # Set environment variable to use SQLite
    os.environ["USE_SQLITE"] = "true"

    # Get command line arguments
    args = sys.argv[1:]
    if not args:
        args = ["runserver", "0.0.0.0:8000"]

    # Run Django command with SQLite
    cmd = ["python", "manage.py"] + args
    print(f"Running Django with SQLite: {' '.join(cmd)}")
    subprocess.run(cmd)

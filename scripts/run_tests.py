#!/usr/bin/env python
"""
Simplified test runner for Django project.
Runs pytest on tests/ folder with proper settings.
"""

import os
import subprocess
import sys
from pathlib import Path


def setup_environment():
    """Set working dir and env vars."""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.testing")


def run_tests():
    setup_environment()
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests",
    ]

    print(f"Running tests with: {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def main():
    return_code = run_tests()

    if return_code == 0:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED!")

    return return_code


if __name__ == "__main__":
    sys.exit(main())

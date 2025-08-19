#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Copyright (c) 2025 Ruotolo Vincenzo. All rights reserved.
#
# This software is proprietary and licensed, not sold. See the LICENSE.md file
# in the project root for the full license terms.
#
# Unauthorized copying, distribution, modification, or resale of this file,
# via any medium, is strictly prohibited without prior written permission.
# -----------------------------------------------------------------------------
"""
clean.py

Python equivalent of the Bash script to clean unused Docker resources.
"""

import subprocess


def run_cmd(description: str, cmd: list[str]):
    """Run a shell command with a description header."""
    print(description)
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {e.cmd} (exit {e.returncode})")
    print()  # blank line


def main():
    print("Clean residuals docker images and containers\n")

    run_cmd("Pruning containers...", ["docker", "container", "prune", "-f"])
    run_cmd("Pruning images...", ["docker", "image", "prune", "-f"])
    run_cmd("Pruning system...", ["docker", "system", "prune", "-f"])


if __name__ == "__main__":
    main()

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
push.py

Python equivalent of the original Bash script for generating config,
loading env vars, tagging, pushing, and removing Docker images.
"""

import os
import sys
import subprocess
from pathlib import Path
import shlex

import generate_config


TARGET_CONFIG = ".env"
TARGET_CONFIG_PATH = "config/" + TARGET_CONFIG


def run(cmd: list[str], check: bool = True) -> None:
    """Run a command, streaming output, raising if it fails."""
    print(f"$ {' '.join(shlex.quote(c) for c in cmd)}")
    subprocess.run(cmd, check=check)


def load_env_file(env_path: Path) -> None:
    """Load variables from a .env file into os.environ."""
    if not env_path.exists():
        print(f"[ERROR] env file not found: {env_path}")
        sys.exit(1)

    with env_path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ[key.strip()] = val.strip()


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} ROOT_DIR [TARGET_ARCH]")
        sys.exit(1)

    root_dir = Path(sys.argv[1]).resolve()
    target_arch = sys.argv[2] if len(sys.argv) > 2 else None

    # Step 1: run generate_config API directly
    config_path = root_dir / "config" / "env.yaml"
    config = generate_config.load_yaml_config(str(config_path))
    env_vars = generate_config.generate_config(config, target_arch)
    if env_vars is None:
        print("Configuration generation failed. Exiting.")
        raise SystemExit(1)

    env_path = root_dir / "config" / ".env"
    generate_config.write_env_config(env_vars, filename=str(env_path))

    # Step 2: source .env (emulate by loading env vars)
    env_file = root_dir / TARGET_CONFIG_PATH
    load_env_file(env_file)

    docker_image = os.environ.get("DOCKER_IMAGE")
    docker_tag = os.environ.get("DOCKER_IMAGE_TAG")

    if not docker_image or not docker_tag:
        print(f"[ERROR] DOCKER_IMAGE and DOCKER_IMAGE_TAG must be set in {TARGET_CONFIG}")
        sys.exit(1)

    docker_image_lc = docker_image.lower()

    print(
        f"\nPush image: {docker_image}:{docker_tag} "
        f"-> Registry Container: ghcr.io/{docker_image_lc}:{docker_tag}\n"
    )

    # Step 3: Docker operations
    print(
        f"Tagging image: {docker_image}:{docker_tag} "
        f"-> {docker_image_lc}:{docker_tag}"
    )
    run(["docker", "tag", f"{docker_image}:{docker_tag}", f"ghcr.io/{docker_image_lc}:{docker_tag}"])

    print(
        f"Pushing image: {docker_image_lc}:{docker_tag} "
        f"-> ghcr.io/{docker_image_lc}:{docker_tag}"
    )
    run(["docker", "push", f"ghcr.io/{docker_image_lc}:{docker_tag}"])

    print(f"Removing image: {docker_image_lc}:{docker_tag}")
    run(["docker", "rmi", f"ghcr.io/{docker_image_lc}:{docker_tag}"])


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed with exit code {e.returncode}: {e.cmd}")
        sys.exit(e.returncode)

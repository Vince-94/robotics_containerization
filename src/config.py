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
config.py

Read and display project, image, and container configuration info from .env.
"""

import os
import sys
from pathlib import Path


TARGET_CONFIG = ".env"
TARGET_CONFIG_PATH = "config/" + TARGET_CONFIG


def load_env_file(env_path: Path) -> dict[str, str]:
    """Load environment variables from a .env-like file into a dictionary."""
    env_vars = {}
    with env_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            env_vars[key.strip()] = val.strip().strip('"').strip("'")
    return env_vars


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} ROOT_DIR")
        sys.exit(1)

    root_dir = Path(sys.argv[1]).resolve()

    # Load .env
    env_file = root_dir / TARGET_CONFIG_PATH
    if not env_file.exists():
        print(f"[ERROR] Config file not found: {env_file}")
        sys.exit(1)

    env = load_env_file(env_file)
    os.environ.update(env)  # optional: make vars available to subprocesses

    # Print summary
    print(f"""Configuration loaded from: {env_file}

Project info
- Name:                 {env.get("PROJECT_REPO", "")}
- Author:               {env.get("REPO_AUTHOR", "")}
- Extra volumes:        {env.get("VOLUMES", "")}

Image info
- Base image:           {env.get("BASE_IMAGE", "")}
- Build stage:          {env.get("BUILD_STAGE", "")}
- Architecture:         source: {env.get("SOURCE_ARCH", "")} -> target: {env.get("TARGET_ARCH", "")}
- Dockerfile name:      {env.get("DOCKERFILE", "")}
- Docker image:         {env.get("DOCKER_IMAGE", "")}:{env.get("DOCKER_IMAGE_TAG", "")}
- Docker container:     {env.get("DOCKER_CONTAINER", "")}

Container info
- User:                 {env.get("CONTAINER_USR", "")} (uid: {env.get("CONTAINER_UID", "")}, gid: {env.get("CONTAINER_GID", "")})
- Password:             {env.get("CONTAINER_PSW", "")}
- Home path:            {env.get("CONTAINER_HOME", "")}
- Workspace path:       {env.get("CONTAINER_WS", "")}
- Docker run command:   {env.get("CONTAINER_RUN_CMD", "")}
""")


if __name__ == "__main__":
    main()

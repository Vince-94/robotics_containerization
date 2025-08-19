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
build.py

Usage:
    ./build.py [--target-arch aarch64]
"""
from __future__ import annotations
import shlex
import shlex as _shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional
import platform
import click

import generate_config


TARGET_CONFIG = ".env"
TARGET_CONFIG_PATH = "config/" + TARGET_CONFIG


def run_generate_config(root_dir: Path, target_arch: Optional[str]) -> None:
    """
    Run the generate_config API directly instead of as a subprocess.
    """
    # Load YAML config
    config_path = root_dir / "config" / "env.yaml"
    config = generate_config.load_yaml_config(str(config_path))
    env_vars = generate_config.generate_config(config, target_arch or platform.machine())
    if env_vars is None:
        print("Configuration generation failed. Exiting.")
        raise SystemExit(1)

    env_path = root_dir / "config" / ".env"
    generate_config.write_env_config(env_vars, filename=str(env_path))


def parse_env_file(env_path: Path) -> Dict[str, str]:
    """
    Parse a simple KEY=VALUE env file emitted by your generator.
    Keeps values as raw strings; arrays will look like "('a' 'b')".
    """
    if not env_path.is_file():
        raise FileNotFoundError(f"Expected env file not found: {env_path}")

    env: Dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # we assume simple KEY=VALUE with no exported spacing complications
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        env[key.strip()] = val.strip()
    return env


def normalize_arch(a: str) -> str:
    a = a.strip().lower()
    if a in ("arm64",):
        return "aarch64"
    if a.startswith("armv7") or a == "armv7l":
        return "armv7"
    return a


def choose_platform_option(target_arch: str, source_arch: str) -> Optional[str]:
    """
    Return a docker --platform argument (string) if we need crossbuild, otherwise None.
    Handles aarch64 / arm normalization.
    """
    targ = normalize_arch(target_arch)
    src = normalize_arch(source_arch)

    # Only handle the common cases you use:
    if targ in ["develop", "x86_64"]:
        return "--platform=linux/amd64"
    elif targ in ["deploy", "arm", "aarch64"]:
        return "--platform=linux/arm64"
    elif targ == "armv7":
        return "--platform=linux/arm/v7"

    # default: no platform (caller can extend)
    return None


def make_build_args(env: Dict[str, str], keys: Dict[str, str]) -> list[str]:
    """
    Build a list of docker --build-arg '<KEY>=<VALUE>' entries for docker CLI.
    `keys` is a mapping of key -> env_key (env file variable name).
    """
    out: list[str] = []
    for build_key, env_key in keys.items():
        if env_key not in env:
            raise KeyError(f"Required variable {env_key} not found in {TARGET_CONFIG}")
        val = env[env_key]
        out += ["--build-arg", f"{build_key}={val}"]
    return out


@click.command()
@click.argument("root_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path), required=True)
@click.argument("target_arch", type=str, required=False, default=platform.machine())
def build(root_dir: Path, target_arch: Optional[str]) -> None:
    """Build docker image using generated .env (click version).

    ROOT_DIR must be a directory containing src/generate_config.py.
    """
    # root_dir is already validated by click
    try:
        run_generate_config(root_dir, target_arch)
    except subprocess.CalledProcessError as e:
        click.echo(f"generate_config.py failed: {e}", err=True)
        raise SystemExit(3)
    except FileNotFoundError as e:
        click.echo(f"generate_config.py missing: {e}", err=True)
        raise SystemExit(4)

    env_file = root_dir / TARGET_CONFIG_PATH
    try:
        env = parse_env_file(env_file)
    except FileNotFoundError as e:
        click.echo(f"Missing env file: {e}", err=True)
        raise SystemExit(4)

    # required keys we will use (fail early if missing)
    required = [
        "DOCKERFILE",
        "DOCKER_IMAGE",
        "DOCKER_IMAGE_TAG",
        "BUILD_STAGE",
        "BASE_IMAGE",
        "CONTAINER_USR",
        "CONTAINER_PSW",
        "CONTAINER_UID",
        "CONTAINER_GID",
        "TARGET_ARCH",
        "SOURCE_ARCH",
    ]
    for k in required:
        if k not in env:
            click.echo(f"Missing required var '{k}' in {TARGET_CONFIG}", err=True)
            raise SystemExit(5)

    DOCKERFILE = env["DOCKERFILE"]
    DOCKER_IMAGE = env["DOCKER_IMAGE"]
    DOCKER_IMAGE_TAG = env["DOCKER_IMAGE_TAG"]
    BUILD_STAGE = env["BUILD_STAGE"]
    BASE_IMAGE = env["BASE_IMAGE"]

    click.echo(
        f"Build dockerfile: {DOCKERFILE} -> image: {DOCKER_IMAGE}:{DOCKER_IMAGE_TAG}"
    )
    click.echo(f"- base image: {BASE_IMAGE}")
    click.echo(f"- stage: {BUILD_STAGE}")

    # Build args mapping: docker build expects keys (ARG name) -> env var name
    build_arg_map = {
        "CONTAINER_USR": "CONTAINER_USR",
        "CONTAINER_PSW": "CONTAINER_PSW",
        "CONTAINER_UID": "CONTAINER_UID",
        "CONTAINER_GID": "CONTAINER_GID",
    }

    # Print args and build the list
    try:
        build_args_list = make_build_args(env, build_arg_map)
    except KeyError as e:
        click.echo(f"Build args error: {e}", err=True)
        raise SystemExit(6)

    click.echo("- args:")
    for k, envname in build_arg_map.items():
        click.echo(f"  - {k}: {env.get(envname)}")

    platform_opt = choose_platform_option(env["TARGET_ARCH"], env["SOURCE_ARCH"])
    click.echo(f"- architecture: {env['SOURCE_ARCH']} -> {env['TARGET_ARCH']}")
    click.echo(f"- platform: {platform_opt or ''}")

    docker_cmd = [
        "docker",
        "build",
        "--pull",
        "--rm",
        "--build-arg",
        f"BASE_IMAGE={BASE_IMAGE}",
        *build_args_list,
        "-f",
        str(root_dir / "docker" / DOCKERFILE),
        "--target",
        BUILD_STAGE,
        "-t",
        f"{DOCKER_IMAGE}:{DOCKER_IMAGE_TAG}",
    ]

    if platform_opt:
        docker_cmd.append(platform_opt)

    docker_cmd.append(str(root_dir))

    click.echo("\nDocker build command:")
    click.echo(" ".join(shlex.quote(x) for x in docker_cmd))
    click.echo()

    try:
        subprocess.run(docker_cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"docker build failed: {e}", err=True)
        raise SystemExit(7)


if __name__ == "__main__":
    build()

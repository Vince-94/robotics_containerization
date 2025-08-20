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
run.py

Replacement for the bash run launcher.

Usage:
    ./run.py /path/to/project [--target-arch aarch64]
"""
from __future__ import annotations
import shlex
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
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
    if not env_path.is_file():
        raise FileNotFoundError(f"Expected env file not found: {env_path}")
    env: Dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        key, val = s.split("=", 1)
        env[key.strip()] = val.strip()
    return env


def parse_bash_array(value: str) -> List[str]:
    """
    Parse a bash-style array string like "('a' 'b c')" or "()".
    Returns a Python list of strings.
    """
    v = value.strip()
    if not v:
        return []
    # remove surrounding parentheses if present
    if v.startswith("(") and v.endswith(")"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        # use shlex.split to respect quotes/spaces
        return shlex.split(inner)
    # otherwise, fallback: try splitting on commas or spaces
    try:
        return shlex.split(v)
    except Exception:
        return [v]


def normalize_arch(a: str) -> str:
    if not a:
        return ""
    s = a.strip().lower()
    if s in ("arm64",):
        return "aarch64"
    if s in ("arm", "armv7l") or s.startswith("armv7"):
        return "arm"
    return s


def choose_platform_option(target_arch: str, source_arch: str) -> Optional[List[str]]:
    targ = normalize_arch(target_arch)
    src = normalize_arch(source_arch)

    if targ in ["develop", "x86_64"]:
        return "--platform=linux/amd64"
    if targ in ["deploy", "arm", "aarch64"]:
        return "--platform=linux/arm64"
    elif targ == "armv7":
        return "--platform=linux/arm/v7"

    return None


def docker_image_exists(image: str, tag: str) -> bool:
    full = f"{image}:{tag}"
    res = subprocess.run(["docker", "image", "inspect", full], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return res.returncode == 0


def container_running(container_name: str) -> bool:
    # returns True if any container with that name is running
    res = subprocess.run(["docker", "ps", "-q", "-f", f"name={container_name}"], capture_output=True, text=True)
    return bool(res.stdout.strip())


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("root_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path), required=True)
@click.argument("target_arch", type=str, required=False, default=platform.machine())
def run(root_dir: Path, target_arch: Optional[str]) -> None:
    """
    Run container using generated .env
    """
    # root_dir is already a Path due to path_type=Path
    root_dir = root_dir.resolve()
    if not root_dir.is_dir():
        click.echo(f"Error: root_dir is not a directory: {root_dir}", err=True)
        sys.exit(2)

    # 1) run generator
    try:
        run_generate_config(root_dir, target_arch)
    except subprocess.CalledProcessError as e:
        click.echo(f"generate_config.py failed: {e}", err=True)
        sys.exit(3)
    except FileNotFoundError as e:
        click.echo(str(e), err=True)
        sys.exit(4)

    # 2) parse .env (expected location root_dir/config/.env)
    env_file = root_dir / TARGET_CONFIG_PATH
    try:
        env = parse_env_file(env_file)
    except FileNotFoundError as e:
        click.echo(f"Missing env file: {e}", err=True)
        sys.exit(5)

    docker_image = env["DOCKER_IMAGE"]
    docker_image_tag = env["DOCKER_IMAGE_TAG"]
    container_user = env["CONTAINER_USR"]
    container_uid = env["CONTAINER_UID"]
    container_gid = env["CONTAINER_GID"]
    container_cmd = env["CONTAINER_RUN_CMD"]
    container_ws = env["CONTAINER_WS"]
    container_name = env["DOCKER_CONTAINER"]

    # helpful defaults: allow DISPLAY/HOSTNAME from host env if not present in config
    env.setdefault("DISPLAY", os.environ.get("DISPLAY", ""))
    env.setdefault("HOSTNAME", os.environ.get("HOSTNAME", "localhost"))

    # required keys
    required = [
        "DOCKER_IMAGE", "DOCKER_IMAGE_TAG", "DOCKER_CONTAINER", "LOCAL_WS_PATH",
        "CONTAINER_WS", "CONTAINER_HOME", "VOLUMES", "TARGET_ARCH", "SOURCE_ARCH",
        "CONTAINER_UID", "CONTAINER_USR", "CONTAINER_GID", "CONTAINER_RUN_CMD",
    ]
    missing = [k for k in required if k not in env]
    if missing:
        click.echo(f"Missing required vars in {TARGET_CONFIG}: " + ", ".join(missing), err=True)
        raise SystemExit(6)

    # 3) Check if image exists
    if not docker_image_exists(docker_image, docker_image_tag):
        click.echo(f"❌ Error: Docker image {docker_image}:{docker_image_tag} not found.", err=True)
        sys.exit(7)

    # 4) Check if container is running
    if container_running(container_name):
        click.echo(f"Container {env['DOCKER_CONTAINER']} already running. Joining the container...")
        subprocess.run([
            "docker", "exec", "-it",
            "-w", env["CONTAINER_WS"],
            container_name,
            "/bin/bash", "-c", "/entrypoint.sh ; /bin/bash"
        ], check=True)
        sys.exit(0)

    # 5) Build docker run command
    click.echo(
        f"Run docker container: {container_name} -> {docker_image}:{docker_image_tag}"
    )

    docker_volumes = [
        f"-v{env['LOCAL_WS_PATH']}:{env['CONTAINER_WS']}:rw"
    ]
    click.echo(f"- main volume: {env['LOCAL_WS_PATH']} -> {env['CONTAINER_WS']}")

    # extra volumes
    extra_volumes = env.get("VOLUMES", [])
    if extra_volumes != "()":
        click.echo("- extra volumes:")
        for vol in parse_bash_array(extra_volumes):
            fname = Path(vol).name
            docker_volumes.append(f"-v{vol}:{env['CONTAINER_HOME']}/{fname}:rw")
            click.echo(f"  - {vol} -> {env['CONTAINER_HOME']}/{fname}")

    # platform option
    platform_opt = choose_platform_option(env["TARGET_ARCH"], env["SOURCE_ARCH"])
    click.echo(f"- architecture: {env['SOURCE_ARCH']} -> {env['TARGET_ARCH']}")
    click.echo(f"- platform: {platform_opt or ''}")
    click.echo(f"- user: {container_user} (UID: {container_uid}, GID: {container_gid})")
    click.echo(f"- command: {container_cmd}")
    click.echo(f"- workspace: {container_ws}")

    # 6) Assemble final docker run
    docker_run = [
        "docker", "run", "-it", "--rm", "--privileged",
        "--cap-add", "IPC_LOCK",
        "--ulimit", "memlock=-1:-1",
        "--device", "/dev:/dev",
        "--network", "host",
        "-e", f"LOCAL_USER_ID={container_uid}",
        "-e", f"USER={container_user}",
        "-e", f"UID={container_uid}",
        "-e", f"GROUPS={container_gid}",
        "-e", f"DISPLAY={env['DISPLAY']}",
        "-e", "QT_X11_NO_MITSHM=1",
        "-e", "XAUTHORITY=/tmp/.docker.xauth",
        "-p", "14556:14556/udp",
        "-p", "8888-8890:8888-8890/udp",
        "-v", "/etc/localtime:/etc/localtime:ro",
        "-v", "/tmp/.X11-unix:/tmp/.X11-unix",
        "-v", "/tmp/.docker.xauth:/tmp/.docker.xauth",
        "-v", "/dev/shm:/dev/shm",
        *docker_volumes,
        (platform_opt or []),
        "-h", env["HOSTNAME"],
        "-w", env["CONTAINER_WS"],
        "--name", container_name,
        f"{docker_image}:{docker_image_tag}",
        container_cmd,
    ]

    click.echo("\nDocker run command:")
    click.echo(" ".join(shlex.quote(x) for x in docker_run))

    subprocess.run(docker_run, check=True)


if __name__ == "__main__":
    run()

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
import platform
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import click
import shlex


# CONSTANTS
SOURCE_CONFIG = "env.yaml"
TARGET_CONFIG = ".env"

# PATHS
CURRENT_DIR = Path(__file__).resolve().parent
ROBOTICS_CONTAINER_PATH = CURRENT_DIR.parent
ROOT_DIR = ROBOTICS_CONTAINER_PATH.parent
SOURCE_FILEPATH = ROBOTICS_CONTAINER_PATH / "config" / SOURCE_CONFIG
TARGET_FILEPATH = ROBOTICS_CONTAINER_PATH / "config" / TARGET_CONFIG


def bash_array_assignment(items: List[str]) -> str:
    quoted = " ".join(shlex.quote(str(it)) for it in items)
    return f"({quoted})"


def generate_config(config: Dict[str, Any], target_arch: str) -> Optional[Dict[str, str]]:
    repo_author = config["repo_author"]
    project_repo = config["project_repo"]
    volumes_list = config["volumes"]
    container_env = config["container_env"]
    ros2_distro = config["ros2_distro"]
    middleware = config["middleware"]
    target_platorm = config["target_platorm"]  # TODO unused
    docker_base_images = config["docker_base_images"]
    docker_file_image_container = config["docker_file_image_container"]

    # Check constraints
    supported_architectures = config["supported"]["architectures"]
    if target_arch not in supported_architectures:
        print(f"Unsupported architecture: {target_arch}, Supported architectures: {', '.join(supported_architectures)}")
        return

    supported_middlewares = config["supported"]["middlewares"]
    if middleware not in supported_middlewares:
        print(f"Unsupported middleware: {middleware}, Supported middlewares: {', '.join(supported_middlewares)}")
        return

    supported_ros2_distro = config["supported"]["ros2_distros"]
    if ros2_distro not in supported_ros2_distro:
        print(f"Unsupported ROS2 distribution: {ros2_distro}, Supported distributions: {', '.join(supported_ros2_distro)}")
        return

    # Repo env
    local_project_repo_path = ROOT_DIR / project_repo
    if not local_project_repo_path.is_dir():
        print(f"Directory does not exist: {local_project_repo_path}")
        return
    local_project_repo_path = str(local_project_repo_path)

    repo_env = {
        "REPO_AUTHOR": repo_author,
        "PROJECT_REPO": project_repo
    }

    # Volumes env
    for volume in volumes_list:
        if not Path(volume).is_dir():
            print(f"Directory does not exist: {volume}")
            return
    volumes_env = {
        "LOCAL_WS_PATH": local_project_repo_path,
        "VOLUMES": bash_array_assignment(volumes_list)
    }

    # Container env
    container_home = f"/home/{container_env['container_usr']}"
    container_ws = f"{container_home}/{project_repo}"
    container_env = {
        "CONTAINER_USR": container_env["container_usr"],
        "CONTAINER_PSW": container_env["container_psw"],
        "CONTAINER_UID": container_env["container_uid"],
        "CONTAINER_GID": container_env["container_gid"],
        "CONTAINER_HOME": container_home,
        "CONTAINER_WS": container_ws,
        "CONTAINER_RUN_CMD": config["container_run_cmd"],
    }

    # Base image env
    if middleware == "ros2":
        if target_arch in ["develop", "x86_64"]:
            base_image = docker_base_images["x86_full_image"]
            build_stage = "develop-stage"
            tag = "develop"
            arch = "x86_64"
        elif target_arch in ["deploy", "arm", "aarch64"]:
            base_image = docker_base_images["arm_base_image"]
            build_stage = "deploy-stage"
            tag = "deploy"
            arch = "arm"
        else:
            print(f"Unsupported architecture: {target_arch}, Supported architectures: {', '.join(supported_architectures)}")
            return

    elif middleware == "micro-ros":
        base_image = docker_base_images["microros_base_image"]
        if target_arch in ["develop"]:
            build_stage = "develop-stage"
            tag = "develop"
            arch = "x86_64"
        elif target_arch in ["deploy"]:
            build_stage = "deploy-stage"
            tag = "deploy"
            arch = "arm"
        else:
            print(f"Unsupported architecture: {target_arch}, Supported architectures: {', '.join(supported_architectures)}")
            return

    else:
        print(f"Unsupported middleware: {middleware}, Supported middlewares: ros2, micro-ros")
        return

    base_image_env = {
        "BASE_IMAGE": base_image.replace("ROS2_DISTRO", ros2_distro),
        "BUILD_STAGE": build_stage,
        "TARGET_ARCH": arch,
        "SOURCE_ARCH": platform.machine(),
    }

    # Image env
    dockerfile_name = docker_file_image_container["dockerfile"].replace("MIDDLEWARE", middleware)
    if not Path(ROBOTICS_CONTAINER_PATH / "docker" / dockerfile_name).resolve().is_file():
        print(f"Dockerfile does not exist: {dockerfile_name}")
        return

    docker_image_name = docker_file_image_container["docker_image"].replace("REPO_AUTHOR", repo_author).replace("PROJECT_REPO", project_repo).replace("ROS2_DISTRO", ros2_distro)
    docker_container_name = docker_file_image_container["docker_container"].replace("PROJECT_REPO", project_repo).replace("TAG", tag)

    image_env = {
        "DOCKERFILE": dockerfile_name,
        "DOCKER_IMAGE": docker_image_name,
        "DOCKER_CONTAINER": docker_container_name,
        "DOCKER_IMAGE_TAG": tag,
    }

    # Final env
    env_vars = repo_env | volumes_env | container_env | base_image_env | image_env

    return env_vars


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


def write_env_config(env_vars: Dict[str, str], filename: str = TARGET_CONFIG) -> None:
    with open(filename, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")


@click.command()
@click.option("--target_arch", type=str, required=True, help="Target architecture to override the OS architecture.")
def main(target_arch: str) -> None:
    config = load_yaml_config(SOURCE_FILEPATH)
    env_vars = generate_config(config, target_arch)
    if env_vars is None:
        print("Configuration generation failed. Exiting.")
        return
    write_env_config(env_vars=env_vars, filename=TARGET_FILEPATH)


if __name__ == "__main__":
    main()

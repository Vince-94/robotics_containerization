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
status.py

Port of the bash Docker status checks to Python.
Exits with non-zero code on fatal errors (Docker CLI missing, daemon down, missing buildx, missing qemu, etc.).
"""
from __future__ import annotations
import shutil
import subprocess
import sys
import os
from typing import Tuple


def run_cmd(description: str, cmd: list[str]):
    """Run a shell command with a description header."""
    print(f"{description}:")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {e.cmd} (exit {e.returncode})")
    print()  # blank line


def run(cmd: list[str], check: bool = False) -> Tuple[int, str, str]:
    """Run command and return (returncode, stdout, stderr)."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return 127, "", f"Command not found: {cmd[0]}"


def info(msg: str) -> None:
    print(msg)


def ok(msg: str) -> None:
    print(f"[OK] {msg}")


def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def err(msg: str) -> None:
    print(f"[ERROR] {msg}")


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def check_docker_cli() -> bool:
    if command_exists("docker"):
        code, out, _ = run(["docker", "--version"])
        if code == 0 and out:
            ok(f"Docker CLI found: {out}")
            return True
        else:
            warn(f"Docker CLI reported unexpected output (rc={code}).")
            return False
    else:
        err("Docker CLI not found.")
        return False


def check_docker_compose_plugin() -> None:
    # docker compose may exist as plugin/subcommand
    code, out, _ = run(["docker", "compose", "version"])
    if code == 0:
        ok(f"Docker Compose plugin found: {out}")
    else:
        warn("Docker Compose plugin not found.")


def is_root() -> bool:
    try:
        return os.geteuid() == 0
    except AttributeError:
        # Windows / non-POSIX fallback
        return False


def check_docker_daemon() -> bool:
    # prefer `systemctl is-active --quiet docker`
    cmd = ["systemctl", "is-active", "--quiet", "docker"]
    if not is_root():
        cmd = ["sudo"] + cmd

    rc, _, _ = run(cmd)
    if rc == 0:
        ok("Docker daemon is running.")
        return True

    # show status for debugging
    err("Docker daemon is not running.")
    status_cmd = (["systemctl", "status", "docker", "--no-pager"] if is_root() else ["sudo", "systemctl", "status", "docker", "--no-pager"])
    rc2, out2, err2 = run(status_cmd)
    # print captured output (could be long)
    if out2:
        print(out2)
    if err2:
        print(err2, file=sys.stderr)
    return False


def check_buildx() -> bool:
    code, out, _ = run(["docker", "buildx", "version"])
    if code == 0:
        ok(f"Docker Buildx found: {out}")
        return True
    else:
        err("Docker Buildx not found.")
        return False


def check_qemu() -> bool:
    # check for qemu-aarch64-static (as in your original)
    if command_exists("qemu-aarch64-static"):
        ok("QEMU for ARM is available (qemu-aarch64-static found).")
        return True
    else:
        err("QEMU for ARM (qemu-aarch64-static) is not available.")
        return False


def main() -> int:
    info("Check Docker status:")

    # Docker CLI
    if not check_docker_cli():
        return 1

    # Compose plugin (warn only)
    check_docker_compose_plugin()

    # Docker daemon
    if not check_docker_daemon():
        return 2

    # Buildx
    if not check_buildx():
        return 3

    # QEMU
    if not check_qemu():
        return 4

    print("")
    run_cmd("Resume", ["docker", "system", "df"])
    run_cmd("Images", ["docker", "images"])
    run_cmd("Volumes", ["docker", "volume", "ls"])
    run_cmd("Containers", ["docker", "ps", "-a"])
    run_cmd("Network", ["docker", "network", "ls"])

    info("\nDocker status check completed.")
    return 0


if __name__ == "__main__":
    rc = 0
    try:
        rc = main()
    except subprocess.CalledProcessError as e:
        err(f"Command failed: {e}")
        rc = 5
    except Exception as e:
        err(f"Unexpected error: {e}")
        rc = 6
    sys.exit(rc)

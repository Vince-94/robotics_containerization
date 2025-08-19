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
install.py

Idempotent installer for Docker/QEMU on Debian/Ubuntu.

Run as a normal user (the script uses `sudo` where required) or under root.
"""

from __future__ import annotations
import subprocess
import sys
import shutil
import os
import getpass
from pathlib import Path
from typing import Optional

DOCKER_GPG_URL = "https://download.docker.com/linux/ubuntu/gpg"
KEYRING_DIR = Path("/etc/apt/keyrings")
KEYRING_PATH = KEYRING_DIR / "docker.gpg"
SOURCES_LIST = Path("/etc/apt/sources.list.d/docker.list")


def run(cmd: list[str], check: bool = True, **kwargs) -> subprocess.CompletedProcess:
    """Run a command and print it. Raises on failure if check=True."""
    print("+", " ".join(shlex_quote(x) for x in cmd))
    return subprocess.run(cmd, check=check, **kwargs)


def shlex_quote(s: str) -> str:
    """Simple quoting for printing commands."""
    import shlex
    return shlex.quote(s)


def require_cmd(cmd_name: str) -> None:
    if shutil.which(cmd_name) is None:
        print(f"Error: required command '{cmd_name}' not found in PATH.", file=sys.stderr)
        sys.exit(2)


def detect_codename() -> str:
    """Return VERSION_CODENAME from /etc/os-release (or raise)."""
    os_release = Path("/etc/os-release")
    if not os_release.exists():
        raise RuntimeError("/etc/os-release not found; can't detect distribution codename.")
    text = os_release.read_text()
    for line in text.splitlines():
        if line.startswith("VERSION_CODENAME="):
            return line.split("=", 1)[1].strip().strip('"')
    # Try lsb_release fallback
    try:
        out = subprocess.run(["lsb_release", "-cs"], capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:
        raise RuntimeError("Could not determine distribution codename (VERSION_CODENAME).")


def detect_arch() -> str:
    out = subprocess.run(["dpkg", "--print-architecture"], capture_output=True, text=True, check=True)
    return out.stdout.strip()


def get_real_user() -> tuple[str, Path]:
    """Return the 'real' non-root user (SUDO_USER preferred) and its home dir."""
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        import pwd

        try:
            pw = pwd.getpwnam(sudo_user)
            return sudo_user, Path(pw.pw_dir)
        except KeyError:
            # fall back to getpass
            pass
    user = getpass.getuser()
    home = Path.home()
    return user, home


def main() -> int:
    try:
        require_cmd("curl")
        require_cmd("gpg")
        require_cmd("dpkg")
    except SystemExit:
        return 2

    # quick distro check (script tailored for Debian/Ubuntu)
    if not Path("/etc/debian_version").exists() and not Path("/etc/os-release").exists():
        print("This installer is intended for Debian/Ubuntu systems.", file=sys.stderr)
        return 3

    try:
        codename = detect_codename()
        arch = detect_arch()
    except Exception as e:
        print("Failed to detect system codename/arch:", e, file=sys.stderr)
        return 4

    print(f"Detected distribution codename: {codename}, architecture: {arch}")

    # 1) apt update & install prerequisites
    print("\n==> Installing prerequisites (ca-certificates, curl, gnupg)...")
    subprocess.run(["sudo", "apt", "update"], check=True)
    subprocess.run(
        ["sudo", "apt", "install", "-y", "ca-certificates", "curl", "gnupg", "lsb-release"],
        check=True,
    )

    # 2) ensure keyring dir exists
    print("\n==> Creating keyrings directory")
    subprocess.run(["sudo", "install", "-m", "0755", "-d", str(KEYRING_DIR)], check=True)

    # 3) download GPG key and dearmor into keyring with sudo
    print("\n==> Downloading Docker GPG key and installing into keyrings...")
    curl = subprocess.run(["curl", "-fsSL", DOCKER_GPG_URL], capture_output=True, check=True)
    subprocess.run(["sudo", "gpg", "--dearmor", "-o", str(KEYRING_PATH)], input=curl.stdout, check=True)
    subprocess.run(["sudo", "chmod", "a+r", str(KEYRING_PATH)], check=True)

    # 4) add APT source list
    print("\n==> Writing apt source list for docker")
    source_line = f'deb [arch="{arch}" signed-by={KEYRING_PATH}] https://download.docker.com/linux/ubuntu {codename} stable\n'
    # write using sudo tee (safe, no shell interpolation)
    proc = subprocess.run(
        ["sudo", "tee", str(SOURCES_LIST)],
        input=source_line.encode(),
        stdout=subprocess.DEVNULL,
        check=True,
    )

    # 5) apt update and install docker packages
    print("\n==> Installing Docker packages (docker-ce, docker-ce-cli, containerd.io, buildx, compose plugin)")
    subprocess.run(["sudo", "apt", "update"], check=True)
    subprocess.run(
        [
            "sudo",
            "apt",
            "install",
            "-y",
            "docker-ce",
            "docker-ce-cli",
            "containerd.io",
            "docker-buildx-plugin",
            "docker-compose-plugin",
        ],
        check=True,
    )

    # 6) set permissions on ~/.docker for the real user
    user, home = get_real_user()
    docker_dir = home / ".docker"
    print(f"\n==> Setting permissions/ownership for user's docker dir: {docker_dir} (user={user})")
    # create dir if missing (chown/chmod will create it if needed)
    subprocess.run(["sudo", "mkdir", "-p", str(docker_dir)], check=True)
    subprocess.run(["sudo", "chown", "-R", f"{user}:{user}", str(docker_dir)], check=True)
    subprocess.run(["sudo", "chmod", "-R", "g+rwx", str(docker_dir)], check=True)

    print("\n==> Autoremoving old packages (apt autoremove)")
    subprocess.run(["sudo", "apt", "autoremove", "-y"], check=True)

    # 7) create docker group if needed and add user to it
    print("\n==> Ensuring 'docker' group exists and user is a member")
    g = subprocess.run(["getent", "group", "docker"], stdout=subprocess.DEVNULL)
    if g.returncode != 0:
        print("Group 'docker' does not exist — creating it.")
        subprocess.run(["sudo", "groupadd", "docker"], check=True)
    else:
        print("Group 'docker' already exists — skipping creation.")

    # add user to group (idempotent)
    print(f"Adding user '{user}' to 'docker' group (may require logout/login to take effect).")
    subprocess.run(["sudo", "usermod", "-aG", "docker", user], check=True)
    print("Note: You may need to log out and back in (or run `newgrp docker`) for group changes to apply.")

    # 8) x11 utils
    print("\n==> Installing X11 utils (x11-xserver-utils)")
    subprocess.run(["sudo", "apt", "install", "-y", "x11-xserver-utils"], check=True)

    # 9) QEMU + binfmt support
    print("\n==> Installing QEMU user static, binfmt-support and qemu utils")
    subprocess.run(["sudo", "apt", "install", "-y", "qemu-user-static", "binfmt-support", "qemu-system", "qemu-utils"], check=True)

    print("\nAll done. Please log out and log back in (or run `newgrp docker`) to activate docker group membership.")
    return 0


if __name__ == "__main__":
    import sys

    try:
        rc = main()
    except subprocess.CalledProcessError as e:
        print("Command failed:", e, file=sys.stderr)
        rc = e.returncode or 1
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        rc = 1
    sys.exit(rc)

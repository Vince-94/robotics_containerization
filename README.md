# Robotics Containar

- [Robotics Containar](#robotics-containar)
  - [Description](#description)
  - [Requirements](#requirements)
  - [How to use](#how-to-use)
  - [Tiers](#tiers)
    - [ROS2 development](#ros2-development)
    - [ROS2 deployment](#ros2-deployment)
    - [micro-ROS development](#micro-ros-development)
    - [micro-ROS deployment](#micro-ros-deployment)
  - [Credits \& Acknowledgements](#credits--acknowledgements)
    - [Upstream projects \& core stacks](#upstream-projects--core-stacks)
    - [Container tooling \& runtimes](#container-tooling--runtimes)
    - [Linux distributions \& packaging](#linux-distributions--packaging)
    - [Python ecosystem \& libraries](#python-ecosystem--libraries)
    - [Project contributors](#project-contributors)
    - [License \& third-party licenses](#license--third-party-licenses)
    - [Reporting omissions or suggesting credits](#reporting-omissions-or-suggesting-credits)


## Description

Robotics Container is a small, practical toolkit that packages repeatable ROS2 & micro-ROS development and deployment environments using Docker.

It provides:
- a easy-to-use CLI for various actions
- a single YAML configuration file
- editable Dockerfiles
- cross-arch build support (amd64, arm64)
- reproducible packaging flow
so you can deliver a ready-to-run product to clients or CI.


## Requirements
- OS:
  - Linux: full support
  - Windows: limited in simulation and GUI
  - Mac: experimental
- Python 3.8 or greater


## How to use

Refer to [cheatsheet](docs/rct_cheatsheet.md) page.


## Tiers

| Features                 | **Tier 1** | **Tier 2** | **Tier 3** |
| ------------------------ | ---------- | ---------- | ---------- |
| Dockerfile customization | x          | x          | x          |
| ROS2 development         | x          | x          | x          |
| ROS2 deployment          |            | x          | x          |
| User Customization       |            | x          | x          |
| Extra volumes            |            | x          | x          |
| micro-ROS development    |            |            | x          |
| micro-ROS deployment     |            |            | x          |

### ROS2 development
- Base images: `osrf/ros:<ROS2_DISTRO>-desktop-full`
- Simulation support in Gazebo/Ignition

### ROS2 deployment
- Base images: `arm64v8/ros:<ROS2_DISTRO>-ros-base`
- Only the necessary runtime dependencies, without development tools

### micro-ROS development
- Base images: `microros/base:<ROS2_DISTRO>`
- Tools, libraries, and environments for building, testing, and debugging micro-ROS applications
- Cross-Compilation & Emulation
  - QEMU
  - cross-compilers
  - ARM support

### micro-ROS deployment
- Base images: `microros/base:<ROS2_DISTRO>`
- Only the necessary runtime dependencies, without development tools


## Credits & Acknowledgements

Thank you to the many projects, communities and people that make this toolkit possible. This project builds on a large ecosystem of open-source software — please consult the licenses of the individual projects for full terms.

### Upstream projects & core stacks
- **ROS 2** — for the ROS 2 distributions and official Docker images used as bases.
- **micro-ROS** — for embedded / RTOS tooling and images supporting MCU workflows.

### Container tooling & runtimes
- **Docker** — for image builds and multi-arch support.
- **QEMU / binfmt** (e.g. `multiarch/qemu-user-static`) — for local emulation of other architectures when cross-building.

### Linux distributions & packaging
- **Debian / Ubuntu** — for base distributions, package repositories and many system packages used in images.

### Python ecosystem & libraries
- **Python (CPython)** and the standard library.  
- **Click** — CLI utilities and command parsing.  
- **Cython** — compilation of Python code for distribution.  
- **colcon**, **vcstool**, **rosdep** — ROS build & dependency tooling.  
- Useful Python libraries referenced or recommended: `pyserial`, `empy`, `lark-parser`, etc.

### Project contributors
- **Ruotolo Vincenzo** — project author, primary maintainer.  
- Thanks to early testers and colleagues who provided feedback, bug reports and real-world test cases.

### License & third-party licenses
This project is distributed under the license in `LICENSE.md` at the project root. Third-party components used by this project are governed by their own licenses (Debian/Ubuntu packages, ROS packages, Python packages, Docker images). **Before redistributing derived images or binaries**, please review upstream license terms and comply with their requirements.

### Reporting omissions or suggesting credits
If we missed a library, contributor, or other project that should be acknowledged, please open an issue or send a pull request — we will add it promptly.

# Robotics Containar

- [Robotics Containar](#robotics-containar)
  - [Description](#description)
  - [Pre-requisite](#pre-requisite)
  - [How to use](#how-to-use)
    - [Initialization](#initialization)
    - [Configuration](#configuration)
    - [Building](#building)
    - [Running](#running)
    - [Push to GitHub register](#push-to-github-register)
    - [Check configuration](#check-configuration)
    - [Introspection](#introspection)
    - [Clen up](#clen-up)
  - [Tiers](#tiers)
    - [ROS2 development](#ros2-development)
    - [ROS2 deployment](#ros2-deployment)
    - [micro-ROS development](#micro-ros-development)
    - [micro-ROS deployment](#micro-ros-deployment)


## Description

This repo is intendend to contenairize ROS2 applications with Docker.


## Pre-requisite
Install common dependencies
```sh
sudo add-apt-repository universe
sudo apt update
sudo apt install -y git
```


## How to use

### Initialization
Enable `RCT` (Robotic Container Tool):
```sh
source rct.sh init
```
The initalization performs the following actions:
- installing docker (if not already present)
- check docker status
- enabling `rct` cli command

It is possible to get the list of all possible commands with:
```sh
rct help
```

### Configuration
Before starting to operate, you must configure the environment, through the configuration file [env.yaml](config/env.yaml). This file is divided into 2 sections:
- Configuration: Variables that can be set freely according to the user requirements; some have placeholders and must be filled by the user.
- Constants: Variables used for abstraction, that shouldn't be modified; modification of them usually imply a modification of the logic to reflect the changes accordingly.

Furthermore, it is possible to customize dockerfiles in order to install dependencies directly in the images before building. To do that, go into the dockerfile of reference in the `docker` folder, and add the dependencies in the block highlited just below the line `TODO: Insert dependencies within this block`. Take into account also the stage (develop or deploy) of reference.

### Building
Build the dockerimage:
```sh
rct build <TARGET>
```

It will generate a docker image with the following signature: `<AUTHOR_NAME>/<WS_NAME>-<ROS2_DISTRO>-image:<TAG>`

### Running
Create/Join the container:
```sh
rct run <TARGET>
```
This will create a container with the following signature: `<AUTHOR_NAME>-<TAG>-container`

> [!NOTE]
> Executing in another terminal the same command, will end up into joining the same container (docker exec).

### Push to GitHub register
It is possible to push to GitHub register, the created docker image:
```sh
rct push <TARGET>
```

### Check configuration
Show actual environment setup:
```sh
rct config
```

### Introspection
Introspect docker images/containers:
```sh
rct status
```

### Clen up
To clean up residual images/containers:
```sh
rct clean
```


## Tiers

| Features              | **Tier 1** | **Tier 2** | **Tier 3** |
| --------------------- | ---------- | ---------- | ---------- |
| ROS2 development      | x          | x          | x          |
| ROS2 deployment       |            | x          | x          |
| User Customization    |            | x          | x          |
| Extra volumes         |            | x          | x          |
| micro-ROS development |            |            | x          |
| micro-ROS deployment  |            |            | x          |

### ROS2 development
- Base images: `osrf/ros:ROS2_DISTRO-desktop-full`
- Simulation support in Gazebo/Ignition

### ROS2 deployment
- Base images: `arm64v8/ros:ROS2_DISTRO-ros-base`
- Only the necessary runtime dependencies, without development tools

### micro-ROS development
- Base images: `microros/base:ROS2_DISTRO`
- Tools, libraries, and environments for building, testing, and debugging micro-ROS applications
- Cross-Compilation & Emulation
  - QEMU
  - cross-compilers
  - ARM support

### micro-ROS deployment
- Base images: `microros/base:ROS2_DISTRO`
- Only the necessary runtime dependencies, without development tools

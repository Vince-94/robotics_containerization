#!/bin/bash
# -----------------------------------------------------------------------------
# Copyright (c) 2025 Ruotolo Vincenzo. All rights reserved.
#
# This software is proprietary and licensed, not sold. See the LICENSE.md file
# in the project root for the full license terms.
#
# Unauthorized copying, distribution, modification, or resale of this file,
# via any medium, is strictly prohibited without prior written permission.
# -----------------------------------------------------------------------------
set -e

# Source
source ~/.bashrc

# (Optional) Comment/Uncomment or add/remove git congiguration
git config --global core.editor "code --wait"

# TODO Source ROS2
source /opt/ros/${ROS_DISTRO}/setup.bash

if [ -f /opt/micro_ros_setup/install/local_setup.bash ]; then
  	source /opt/micro_ros_setup/install/local_setup.bash
fi

if [[ -d "../install" ]]; then
	source $CONTAINER_WS/install/local_setup.bash
fi


# User check
if ! [[ $USER == $CONTAINER_USR ]] && [[ $UID == $CONTAINER_UID ]]; then
	echo "User is not set correctly!"
	if ! [[ $USER == $CONTAINER_USR ]]; then
		echo "Username mismatch: $USER is not $CONTAINER_USR"
	else
		echo "UID mismatch: $UID is not $CONTAINER_UID"
	fi
	exit
fi


if [[ -n "$CI" ]]; then
    exec /bin/bash
else
    exec "$@"
fi

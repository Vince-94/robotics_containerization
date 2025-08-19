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

# Tool Name variable
TOOL_NAME="rct"

# Colors
CYAN="\033[1;36m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
GREEN="\033[1;32m"
MAGENTA="\033[1;35m"
BLUE="\033[1;34m"
WHITE="\033[1;37m"
NC="\033[0m" # No Color

echo -en "${RED}"
echo "###########################"
echo "# Robotics Container Tool #"
echo "###########################"
echo -en "${NC}"

CURRENT_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
SRC_PATH=$CURRENT_DIR/src
USR_LOCAL_BIN="/usr/local/bin"


#! init
if [[ $1 == "init" ]]; then
    # Check docker installation
    if ! $SRC_PATH/status.py; then
        echo "Docker not installed."
        $SRC_PATH/install.py
    fi

    # Create command line tool
    if [ ! -L "$USR_LOCAL_BIN/$TOOL_NAME" ]; then
        sudo ln -s $CURRENT_DIR/$TOOL_NAME.sh $USR_LOCAL_BIN/$TOOL_NAME
        sudo chmod +x $USR_LOCAL_BIN/$TOOL_NAME
        echo "Symbolic link created."
    fi

    echo "Environment Setup Tool initialized."


#! build
elif [[ $1 == "build" ]]; then
    $SRC_PATH/build.py $CURRENT_DIR $2


#! push
elif [[ $1 == "push" ]]; then
    $SRC_PATH/push.py $CURRENT_DIR $2


#! run
elif [[ $1 == "run" ]]; then
    $SRC_PATH/run.py $CURRENT_DIR $2


#! clean
elif [[ $1 == "clean" ]]; then
    $SRC_PATH/clean.py


#! config
elif [[ $1 == "config" ]]; then
    $SRC_PATH/config.py $CURRENT_DIR


#! status
elif [[ $1 == "status" ]]; then
    $SRC_PATH/status.py


#! help
elif [[ $1 == "help" ]]; then
    echo -en "${CYAN}"
    python3 src/help.py $2 --help
    echo -en "\n${YELLOW}"
    echo "To see details about a specific command, type:"
    echo "  rpt help <CMD>"


#! default
else
    echo -en "${CYAN}"
    python3 src/help.py
    echo -en "\n${YELLOW}"
    echo "To see details about a specific command, type:"
    echo "  rpt help <CMD>"

fi

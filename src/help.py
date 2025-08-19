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
import click


@click.group()
def cli():
    """Robotics Container Tool Command Line Interface"""


@cli.command()
@click.option("--target", required=False, help="Target architecture")
def build(target: str = None):
    """Build docker image"""
    pass


@cli.command()
@click.option("--target", required=False, help="Target architecture")
def push(target: str = None):
    """Push docker image to GitHub registry"""
    pass


@cli.command()
@click.option("--target", required=False, help="Target architecture")
def run(target: str = None):
    """Create/Join docker container"""
    pass


@cli.command()
def clean():
    """Clean residual images/containers"""
    pass


@cli.command()
def config():
    """Current setup configuration"""
    pass


@cli.command()
def status():
    """Status of the docker installation"""
    pass


@cli.command(name="helpme")
def help_command():
    """Display this help message"""
    click.echo(cli.get_help())


if __name__ == "__main__":
    cli()

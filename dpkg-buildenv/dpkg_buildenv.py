#!/usr/bin/env python3

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------- #
#                                    Common                                    #
# ---------------------------------------------------------------------------- #
def prerequisite_check():

    # Check the user can run docker without sudo
    result = subprocess.run(
        "docker info", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    if result.returncode != 0:
        exit(
            """\
You must allow docker to run as non-root user
To do this follow the steps in the official docker documentation: https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user
Run the following:
sudo usermod -aG docker $USER
newgrp docker"""
        )

    # Check correct directory
    if not os.path.isfile("./debian/control"):
        sys.exit(
            f"Could not find /debian/control file. Are you in the correct directory?"
        )


def delete_images():
    find_cmd = "docker images '*buildenv' --format {{.Repository}}"
    find_result = (
        subprocess.check_output(find_cmd, shell=True).decode("utf-8").replace("\n", " ")
    )

    if find_result != "":
        logging.info(f"Deleting images: {find_result}")
        delete_cmd = f"docker rmi {find_result}; docker image prune --force"
        logging.info(f"Docker delete command: {delete_cmd}")
        subprocess.run(delete_cmd, shell=True, check=True)
    else:
        logging.info("No images to delete")


def generate_image_name() -> str:
    path = os.getcwd()
    directories = os.path.split(path)
    image_name = directories[-1].lower() + "-buildenv"
    return image_name


def get_uid() -> int:
    uid = os.getuid()
    if uid == 0:
        uid = os.environ.get("SUDO_UID")
    return uid


# ---------------------------------------------------------------------------- #


# ---------------------------------------------------------------------------- #
#                                     Build                                    #
# ---------------------------------------------------------------------------- #
def get_build_arguments(distribution: str, sources: str) -> str:

    build_args = ""

    # ---------------------------------- UserID ---------------------------------- #
    build_args += f'--build-arg UID="{get_uid()}"'

    # ---------------------------------- Sources --------------------------------- #
    try:
        with open(f"/etc/dpkg-buildenv/sources.list.d/{sources}.sources") as file:
            additional_sources = file.read().replace("\n", "\\n")
            build_args += f' --build-arg ADDITIONAL_SOURCES="{additional_sources}"'
    except FileNotFoundError:
        if sources != "default":
            print(
                f"Error file not found: /etc/dpkg-buildenv/sources.list.d/{sources}.sources"
            )
            exit(-1)

    # ------------------------------- Distribution ------------------------------- #
    if distribution:
        build_args += f" --build-arg DISTRIBUTION={distribution}"

    return build_args


def build_image(repository_name: str, no_cache: str = "", build_arguments: str = ""):
    build_cmd = f"""\
DOCKER_BUILDKIT=1
docker image build
--tag {repository_name}
--file /usr/share/dpkg-buildenv/Dockerfile
--network host
{no_cache}
{build_arguments}
.\
""".replace(
        "\n", " "
    )

    logging.info(f"Docker build command: {build_cmd}")
    subprocess.run(build_cmd, shell=True, check=True)


# ---------------------------------------------------------------------------- #


# ---------------------------------------------------------------------------- #
#                                      Run                                     #
# ---------------------------------------------------------------------------- #
def run_container(repository_name: str, command: str = "", interactive: str = ""):
    # ------------------------ Handle docker run arguments ----------------------- #
    # If the user hasn't supplied a command then assume build command.
    # Delete built_packages to clear out any old packages then move new ones over.
    if command == "":
        command = f"""\
dpkg-buildpackage && \
mv-debs && \
dpkg-buildpackage --target=clean\
""".replace(
            "\n", " "
        )

    # Regardless of command origin (user provided or assumed), prepend the
    # command with "/bin/bash -c".
    command = f"/bin/bash -c '{command}'"

    # If interactive mode is specified then remove any commands
    if interactive != "":
        command = ""

    deb_build_options = os.environ.get("DEB_BUILD_OPTIONS", "")

    run_cmd = f"""\
docker run
--mount type=bind,src=${{PWD}},dst=/workspaces/code
--user {get_uid()}:$(id -g {get_uid()})
--network host
--tty
--rm
--env DEB_BUILD_OPTIONS={deb_build_options}
{interactive}
{repository_name}
{command}\
""".replace(
        "\n", " "
    )

    logging.info(f"Docker run command: {run_cmd}")
    try:
        result = subprocess.run(run_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Build failed!")
        sys.exit(e.returncode)


def move_built_packages():
    make_dir_cmd = f"mkdir --parents {args.destination}"
    subprocess.run(make_dir_cmd, shell=True, check=True)

    mv_debs_cmd = f"mv built_packages/*.deb {args.destination}"
    subprocess.run(mv_debs_cmd, shell=True, check=True)

    del_src_dir_cmd = f"rm -r built_packages/"
    subprocess.run(del_src_dir_cmd, shell=True, check=True)


def kill_container(repository_name):
    get_container_id_cmd = (
        f"docker ps --all --quiet --filter ancestor={repository_name}"
    )
    get_container_id_result = (
        subprocess.check_output(get_container_id_cmd, shell=True)
        .decode("utf-8")
        .replace("\n", " ")
    )
    if get_container_id_result != "":
        kill_container_cmd = f"docker kill {get_container_id_result}"
        subprocess.run(kill_container_cmd, shell=True, check=True)


# ---------------------------------------------------------------------------- #


# ---------------------------------------------------------------------------- #
#                                     Main                                     #
# ---------------------------------------------------------------------------- #
def dpkg_buildenv_parse_args(argv: List[str]):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-nc",
        "--no-cache",
        help="Do not use cache when building the image.",
        action="store_const",
        default="",
        const="--no-cache",
    )
    parser.add_argument(
        "-s",
        "--sources",
        help="Select a sources file stored at /etc/dpkg-buildenv/sources.list.d/<SOURCE>.list.",
        default="default",
    )
    parser.add_argument(
        "-d",
        "--distribution",
        help="Select a linux distribution for the docker parent image (e.g.debian:11).",
        default=None,
    )
    parser.add_argument(
        "-dst",
        "--destination",
        help="Chose a destination directory to store built debian packages.",
        default=None,
    )
    parser.add_argument(
        "--get-build-arguments",
        # Help suppressed as this option is generally only used by tools such as Jenkins
        help=argparse.SUPPRESS,
        action="store_true",
    )
    exclusive_group_parser = parser.add_mutually_exclusive_group()
    exclusive_group_parser.add_argument(
        "-i",
        "--interactive",
        help="Open an interactive terminal to the container.",
        action="store_const",
        default="",
        const="--interactive",
    )
    exclusive_group_parser.add_argument(
        "command",
        help="Command to execute in the container.",
        nargs="?",
        default="",
    )
    exclusive_group_parser.add_argument(
        "-di",
        "--delete-images",
        help="Delete all build environment images generated by this tool",
        action="store_true",
    )
    args = parser.parse_args(argv)

    return args


def main(argv: List[str]):
    try:
        args = dpkg_buildenv_parse_args(argv)

        if args.delete_images:
            delete_images()
            sys.exit()

        build_arguments = get_build_arguments(args.distribution, args.sources)
        if args.get_build_arguments:
            print(build_arguments)
            sys.exit()

        prerequisite_check()
        repository_name = generate_image_name()
        build_image(repository_name, args.no_cache, build_arguments)
        run_container(repository_name, args.command, args.interactive)

        if args.destination:
            move_built_packages()

    except KeyboardInterrupt:
        kill_container(repository_name)
        sys.exit(130)


if __name__ == "__main__":
    main(sys.argv[1:])

# ---------------------------------------------------------------------------- #

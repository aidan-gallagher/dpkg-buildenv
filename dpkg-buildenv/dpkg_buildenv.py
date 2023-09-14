#!/usr/bin/env python3

import argparse
import logging
import os
import subprocess
import sys

logging.basicConfig(level=logging.INFO)


parser = argparse.ArgumentParser()
parser.add_argument(
    "-nc",
    "--no-cache",
    help="Do not use cache when building the image. [Docker build argument]",
    action="store_const",
    default="",
    const="--no-cache",
)
parser.add_argument(
    "-it",
    "--interactive-tty",
    help="Open an interactive terminal to the container. [Docker run argument]",
    action="store_const",
    default="",
    const="--interactive --tty",
)
parser.add_argument(
    "command",
    help="Command to execute in the container. [Docker run argument]",
    nargs="?",
    default="",
)
parser.add_argument(
    "-d",
    "--delete-images",
    help="Delete all build environment images generated by this tool",
    action="store_true",
)
args = parser.parse_args()


def dpkg_directory_check():
    if not os.path.isfile("./debian/control"):
        sys.exit(
            f"Could not find /debian/control file. Are you in the correct directory?"
        )


def delete_images():
    find_cmd = "docker images *buildenv --format {{.Repository}}"
    find_result = (
        subprocess.check_output(find_cmd, shell=True).decode("utf-8").replace("\n", " ")
    )

    if find_result != "":
        logging.info(f"Deleting images: {find_result}")
        delete_cmd = f"docker rmi {find_result}"
        logging.info(f"Docker delete command: {delete_cmd}")
        subprocess.run(delete_cmd, shell=True, check=True)
    else:
        logging.info("No images to delete")


def get_repository_name() -> str:
    path = os.getcwd()
    directories = os.path.split(path)
    repository_name = directories[-1].lower() + "-buildenv"
    logging.info(f"Creating image: {repository_name}")
    return repository_name


def build_image(repository_name):
    build_cmd = f"""\
DOCKER_BUILDKIT=1 
docker image build 
--tag {repository_name} 
--file /usr/share/dpkg-buildenv/Dockerfile 
--network host 
--build-arg UID=$(id -u) 
{args.no_cache} 
.
""".replace(
        "\n", ""
    )

    logging.info(f"Docker build command: {build_cmd}")
    subprocess.run(build_cmd, shell=True, check=True)


def run_container(repository_name):
    # ------------------------ Handle docker run arguments ----------------------- #
    # If the user hasn't supplied a command then assume build command
    if args.command == "":
        args.command = f"""\
dpkg-buildpackage; 
mkdir -p built_packages; 
mv ../*.deb ./built_packages/; 
dh_clean
""".replace(
            "\n", ""
        )

    # Regardless of command origin (user provided or assumed), prepend the
    # command with /bin/bash -c
    args.command = f"/bin/bash -c '{args.command}'"

    # If interactive mode is specified then remove any commands
    if args.interactive_tty != "":
        args.command = ""

    # ----------------------------- Run the container ---------------------------- #
    run_cmd = f"""\
docker run 
--mount type=bind,src=${{PWD}},dst=/workspaces/code 
--user $(id -u):$(id -g) 
--network host 
--rm 
{args.interactive_tty} 
{repository_name} 
{args.command}
""".replace(
        "\n", ""
    )

    logging.info(f"Docker run command: {run_cmd}")
    subprocess.run(run_cmd, shell=True, check=True)


if __name__ == "__main__":

    if args.delete_images is True:
        delete_images()
        sys.exit()

    dpkg_directory_check()
    repository_name = get_repository_name()
    build_image(repository_name)
    run_container(repository_name)

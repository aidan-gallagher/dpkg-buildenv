FROM debian:11
USER root

# ---------------------------------------------------------------------------- #
# Prevent apt from asking the user questions like which time zone.
ARG DEBIAN_FRONTEND=noninteractive
# ---------------------------------------------------------------------------- #


# --------------------- Add docker user & set working dir -------------------- #
# Create docker user and enable sudo permissions.
# If UID already exists then skip. `sudo dpkg-buildenv` will skip as UID will = 0.
ARG UID=1000
RUN id -u $UID || \
    (useradd --shell /bin/bash --uid $UID --create-home docker && \
    echo "docker:docker" | chpasswd && \
    apt-get update --yes && \
    apt-get install --yes sudo && \
    echo "docker ALL = (root) NOPASSWD: ALL\n" > /etc/sudoers.d/docker)
WORKDIR /workspaces/code
# ---------------------------------------------------------------------------- #


# ----------------- Parent directory permissions work around ----------------- #
# dpkg-buildpackage deposits debs (and temp files) in the parent directory.
# Currently there is no way to specify a different directory (https://groups.google.com/g/linux.debian.bugs.dist/c/1KiGKfuFH3Y).
# Non root users do not always have permission to write to the parent directory (depending on where the workspace is mounted).
# Change parent directories of known mount location to have write permissions for all users.

# Jenkins mounts the directory at /var/lib/jenkins/workspace/DANOS_{REPO}_PR-XXX.
# VSCode mounts the directory at /workspaces/{REPO}
RUN mkdir -p /var/lib/jenkins/workspace/ && \
    chmod -R a+w /var/lib/jenkins/workspace/ && \
    mkdir -p /workspaces && \
    chmod -R a+w /workspaces
# ---------------------------------------------------------------------------- #


# --------------------------- Add convenience alias -------------------------- #
# If the user is in interactive mode and runs `dpkg-buildpackage` the generated
# .debs are placed in the parent directory which isn't mounted and therefore not
# avilable to the host.
RUN echo 'alias mv-debs="mkdir --parents ./built_packages;  mv ../*.deb ./built_packages/"' >> ~/.bashrc
# ---------------------------------------------------------------------------- #


# --------------------------- Install mk-build-deps -------------------------- #
RUN apt-get update && \
    apt-get install --yes --fix-missing --no-install-recommends devscripts equivs
# ---------------------------------------------------------------------------- #


# ------------------------ Copy over dependency files ------------------------ #
# Copy over the /debian/control file which contains the Build-Depends section.
# If it exists, copy over the developer-packages.txt file which contains optional
# recommended packages for the developer (gitlint, flake8, autopep8, etc).
# [t] is a necessary work around to allow conditional copying https://stackoverflow.com/a/46801962/13365272.
COPY ./debian/control ./developer-packages.tx[t] ./*.deb /tmp/
# ---------------------------------------------------------------------------- #


# ------------------------- Add additional apt repos ------------------------- #
ARG ADDITIONAL_SOURCES=""
RUN echo "$ADDITIONAL_SOURCES" > /etc/apt/sources.list.d/dpkg-buildenv.sources
# ---------------------------------------------------------------------------- #


# ---------------------------- Add local apt repo ---------------------------- #
RUN dpkg-scanpackages /tmp > /tmp/Packages && \
    echo "deb [trusted=yes] file:///tmp ./" > /etc/apt/sources.list.d/local.list
# ---------------------------------------------------------------------------- #


# ---------------- Install Debian build/packaging dependencies --------------- #
# Install application's build/packaging dependencies.
RUN apt-get update && \
    mk-build-deps /tmp/control && \
    apt-get install --yes --fix-missing --no-install-recommends ./*build-deps*.deb
# ---------------------------------------------------------------------------- #


# ------------------ Install optional developer dependencies ----------------- #
# "2>/dev/null" will prevent cat from printing an error if the file doesn't exit.
RUN apt-get update && \
    apt-get install --yes --no-install-recommends $(cat /tmp/developer-packages.txt 2>/dev/null)
# ---------------------------------------------------------------------------- #

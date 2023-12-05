# Debian Package Build Environment (dpkg-buildenv)
![alt text](./dpkg-buildenv/Documentation/dpkg-buildenv-logo.png "Logo")
[![dpkg-buildenv](https://github.com/aidan-gallagher/dpkg-buildenv/actions/workflows/dpkg-buildenv.yml/badge.svg)](https://github.com/aidan-gallagher/dpkg-buildenv/actions/workflows/dpkg-buildenv.yml)
## Introduction

See the [man page](./dpkg-buildenv/Documentation/dpkg-buildenv.manpage.md) for more information.


The [Debian wiki](https://wiki.debian.org/SystemBuildTools#Package_build_tools) has a list of similar tools.


# Installation

1. Download [dpkg-buildenv debian package]( 
https://github.com/aidan-gallagher/dpkg-buildenv/releases/download/v1.0.0/dpkg-buildenv_1.0.0_all.deb)

2. Install dpkg-buildenv
```
sudo apt install ~/Downloads/dpkg-buildenv_1.0.0_all.deb
```

3.  Configure docker to run as non-root user. See [official docker documentation](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user) for more details.
```
sudo usermod -aG docker $USER
newgrp docker
```

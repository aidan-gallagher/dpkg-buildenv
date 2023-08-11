import subprocess
import dpkg_buildenv as uut


class Test:
    def setup_method(self, test_method):
        # This method is called before every test_* function.
        # It monkey patches the process calls subprocess.check_output()/run().
        # Instead of running these commands as a process they are logged in self.cli_commands.
        self.cli_commands = []

        def run_mock(command, **kwargs):
            self.cli_commands.append(command)
            return "".encode("utf-8")

        subprocess.check_output = subprocess.run = run_mock

    def test_delete_images(self):
        uut.delete_images()
        assert (
            self.cli_commands.pop()
            == "docker images *buildenv --format {{.Repository}}"
        )

    def test_build_image(self):
        uut.build_image("test_name")
        assert (
            self.cli_commands.pop()
            == "DOCKER_BUILDKIT=1 docker image build --tag test_name --file /usr/share/dpkg-buildenv/Dockerfile --network host --build-arg UID=$(id -u)  ."
        )

        uut.args.no_cache = "--no-cache"
        uut.build_image("test_name")
        assert (
            self.cli_commands.pop()
            == "DOCKER_BUILDKIT=1 docker image build --tag test_name --file /usr/share/dpkg-buildenv/Dockerfile --network host --build-arg UID=$(id -u) --no-cache ."
        )

    def test_run_container(self):
        uut.run_container("test_name")
        assert (
            self.cli_commands.pop()
            == "docker run --mount type=bind,src=${PWD},dst=/workspaces/code --user $(id -u):$(id -g) --network host --rm  test_name /bin/bash -c 'dpkg-buildpackage; mkdir -p built_packages; mv ../*.deb ./built_packages/; dh_clean'"
        )

        uut.args.command = "echo I'm a test command"
        uut.run_container("test_name")
        assert (
            self.cli_commands.pop()
            == "docker run --mount type=bind,src=${PWD},dst=/workspaces/code --user $(id -u):$(id -g) --network host --rm  test_name /bin/bash -c 'echo I'm a test command'"
        )

        uut.args.interactive_tty = "--interactive --tty"
        uut.run_container("test_name")
        assert (
            self.cli_commands.pop()
            == "docker run --mount type=bind,src=${PWD},dst=/workspaces/code --user $(id -u):$(id -g) --network host --rm --interactive --tty test_name "
        )

    def test_setup_local_apt_repository(self):
        uut.setup_local_apt_repository("./made/up/path")
        assert (
            self.cli_commands.pop(0)
            == "mkdir --parents ./dpkg-buildenv/input_packages/ && cp ./made/up/path ./dpkg-buildenv/input_packages/"
        )

        assert (
            self.cli_commands.pop(0)
            == "dpkg-scanpackages . /dev/null | gzip --fast --stdout > Packages.gz"
        )

        assert (
            self.cli_commands.pop(0)
            == "mkdir --parents ./dpkg-buildenv/sources.list.d/ && cp /etc/dpkg-buildenv/sources.list.d/local.list ./dpkg-buildenv/sources.list.d/"
        )

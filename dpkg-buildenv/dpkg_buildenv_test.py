import subprocess
import dpkg_buildenv as uut


# main(["--no-cache"])


class Test:
    def setup_method(self, test_method):
        # This method is called before every test_* function.
        # It monkey patches the process calls subprocess.check_output()/run().
        # Instead of running these commands as a process they are logged in self.cli_commands.
        self.cli_commands = []

        def run_mock(command, **kwargs):
            self.cli_commands.append(command)
            return "test".encode("utf-8")

        subprocess.check_output = subprocess.run = run_mock

        def get_uid_mock():
            return 1000

        uut.get_uid = get_uid_mock

    def test_delete_images(self):
        uut.delete_images()
        assert (
            self.cli_commands.pop(0)
            == "docker images '*buildenv' --format {{.Repository}}"
        )
        assert self.cli_commands.pop(0) == "docker rmi test; docker image prune --force"

    def test_build_image(self):
        uut.build_image("test_name")
        assert (
            self.cli_commands.pop(0)
            == "DOCKER_BUILDKIT=1 docker image build --tag test_name --file /usr/share/dpkg-buildenv/Dockerfile --network host   ."
        )

        uut.build_image("test_name", "--no-cache")
        assert (
            self.cli_commands.pop(0)
            == "DOCKER_BUILDKIT=1 docker image build --tag test_name --file /usr/share/dpkg-buildenv/Dockerfile --network host --no-cache  ."
        )

    def test_run_container(self):
        uut.run_container("test_name")
        assert (
            self.cli_commands.pop(0)
            == "docker run --mount type=bind,src=${PWD},dst=/workspaces/code --user 1000:$(id -g 1000) --network host --tty --rm --env DEB_BUILD_OPTIONS=  test_name /bin/bash -c 'dpkg-buildpackage && mv-debs && dpkg-buildpackage --target=clean'"
        )

        uut.run_container("test_name", "echo I'm a test command")
        assert (
            self.cli_commands.pop(0)
            == "docker run --mount type=bind,src=${PWD},dst=/workspaces/code --user 1000:$(id -g 1000) --network host --tty --rm --env DEB_BUILD_OPTIONS=  test_name /bin/bash -c 'echo I'm a test command'"
        )

        uut.run_container("test_name", "", "--interactive")
        assert (
            self.cli_commands.pop(0)
            == "docker run --mount type=bind,src=${PWD},dst=/workspaces/code --user 1000:$(id -g 1000) --network host --tty --rm --env DEB_BUILD_OPTIONS= --interactive test_name "
        )

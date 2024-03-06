import os
import io
import time
import docker
import tarfile
import tempfile

from pathlib import Path
from docker.errors import ImageNotFound, BuildError, APIError, ContainerError


DEFAULT_PYTHON_VERSION = '3.11'
DEFAULT_DOCKER_TAG = 'crew-python-runner'
DOCKER_FOLDER = '/app'


docker_file = """
FROM python:{version}

WORKDIR /app
COPY . /app
CMD ["tail", "-f", "/dev/null"]
"""


class RunnerError(Exception):
    pass


def get_code_temp_file(code):
    temp_file = tempfile.NamedTemporaryFile(mode='w+t', delete=False, suffix='.py')
    temp_file.write(code)
    temp_file.flush()
    # as delete is false, closing will not remove the file
    temp_file.close()
    return Path(temp_file.name)


def create_tar_from_code(code):
    """Create a tar archive containing the specified file."""
    code_file = get_code_temp_file(code)
    with open(code_file, 'rb') as f:
        file_data = f.read()
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
        tarinfo = tarfile.TarInfo(name=code_file.name)
        tarinfo.size = len(file_data)
        tarinfo.mtime = time.time()
        tar.addfile(tarinfo, io.BytesIO(file_data))
    tar_stream.seek(0)
    return [tar_stream, code_file]


class PythonResult:
    def __init__(self, error, result):
        self.error_code = error
        # convert to
        try:
            result = result.decode()
        except (UnicodeError, AttributeError):
            pass
        self.output = result


class DockerController:
    def __init__(self, version=DEFAULT_PYTHON_VERSION):
        self.version = version
        self.client = docker.from_env()
        self.runner = self.start_runner()

    def create_docker_image(self):
        # init the python version
        print('* Creating docker image. This may be slow.')
        formatted_docker_file = io.BytesIO(str.encode(docker_file.format(version=self.version)))
        # from docs: The first item is the Image object for the image that was built.
        return self.client.images.build(fileobj=formatted_docker_file, tag=DEFAULT_DOCKER_TAG)[0]

    def get_image(self):
        try:
            return self.client.images.get(DEFAULT_DOCKER_TAG)
        except ImageNotFound:
            pass
        return self.create_docker_image()

    def start_runner(self):
        try:
            image = self.get_image()
            return self.client.containers.run(image, detach=True, auto_remove=True)
        except (BuildError, APIError, ContainerError) as ex:
            raise RunnerError(ex)

    def run_python_code(self, code):
        # copy the file to the docker image
        tar, filepath = create_tar_from_code(code)
        self.runner.put_archive(DOCKER_FOLDER, tar)
        # run the code in python
        docker_filepath = f'{DOCKER_FOLDER}/{filepath.name}'
        exit_code, output = self.runner.exec_run(f'python {docker_filepath}')
        # delete the file in the container
        self.runner.exec_run(f'rm {docker_filepath}')
        # delete the file here
        os.remove(filepath)
        return PythonResult(exit_code, output)


controller = DockerController()

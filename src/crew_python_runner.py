import os
import io
import time
import docker
import tarfile
import tempfile

from pathlib import Path
from docker.errors import ImageNotFound, BuildError, APIError, ContainerError

from crewai_tools import tool

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


def get_code_temp_file(code: str):
    temp_file = tempfile.NamedTemporaryFile(mode='w+t', delete=False, suffix='.py')
    temp_file.write(code)
    temp_file.flush()
    # as delete is false, closing will not remove the file
    temp_file.close()
    return Path(temp_file.name)


def create_tar_from_code(code: str):
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
    def __init__(self, error: int, result):
        self.error_code = error
        # convert to string from bytecode if required
        try:
            result = result.decode()
        except (UnicodeError, AttributeError):
            pass
        # strip ending \n if it exists
        self.output = result.rstrip()

    def __repr__(self):
        return f'{self.error_code}: {self.output}'


class DockerRunner:
    def __init__(self, version=DEFAULT_PYTHON_VERSION):
        self.version = version
        self.client = docker.from_env()
        self.runner = self.start_runner()

    def create_docker_image(self):
        # init the python version. this may involve a download
        # Convert to "file like object" for the docker setup
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

    def run_python(self, code: str) -> PythonResult:
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


runner = DockerRunner()


@tool('pythonrunner')
def pythonrunner(python_code: str) -> str:
    """
    This tool can run Python code. Pass the code and this tool will run it as a file on the command line.
    The returned value will be the output of the python code, so if you pass print('Hello') it will give you back Hello.
    This tool will put your code into a file and then run the file as python -c your_code_file.py in a virtual machine.
    Pass this tool the python code as you would expect it to look in a file. You will have to indent the code properly.
    If the code has an error, you will get the expected Python error code.
    If the code has no output, you will get an empty string.
    """
    # check for extra arguments and tell the llm where it went wrong
    result = runner.run_python(python_code)
    return result.output

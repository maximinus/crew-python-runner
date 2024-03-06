# crew-python-runner

Allows crew.ai agents to run python code in dockerised containers.

LLM code should not be run locally on your system, but we would like the ability of crew.ai agents to run Python code so they can see that it works.

crew_python_runner will take your agents code and run it in a Docker instance, so you can be sure that nothing bad will happen to your code.


# Installation

You will need Docker installed on your system

    pip install crew_python_runner

 
 # Setup

 On importing, a docker container will start running in the background. The first time this happens, it may have to download the docker image that it uses (python:3.11) so it is suggested you run the command

    python -c "import crew_python_runner"

This will ensure the image is pulled. Alternatively, pull the image from docker

    docker image pull python:3.11

# Usage

To use on it's own:

    from crew_python_runner import runner
    result = runner.run_python('print("Hello, World!"))

This returns a class with 2 variables, *error_code*, an integer, and *output*, a string of the python output. In this case *error_code* will be 0 (meaning no error) and *output* will be *Hello, World!*.

To use as a crew.ai tool:

    from crew_python_runner import python_tool

    # this is just an example
    programmer = Agent(
        role='Senior Python Programmer',
        goal='Write simple, well crafted and bug-free Python code',
        backstory='You a skilled Python programmer with a passion for writing working Python code',
        tools=[python_tool])

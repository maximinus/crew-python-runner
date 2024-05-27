# crew-python-runner

Allows crew.ai agents to run python code in dockerized containers.

LLM code should not be run locally on your system, but we would like the ability of crew.ai agents to run Python code so they can see that it works.

`crew_python_runner` will take your agents code and run it in a Docker instance, so you can be sure that nothing bad will happen to your code.


## Installation

You will need Docker installed on your system

    pip install crew_python_runner

Note that crew_python_runner has a dependency on `crewai[tools]`, which has quite a lot of dependencies; this is likely not an issue if you have crewai already in your virtual environment.

 
 ## Setup

 On importing, a docker container will start running in the background. The first time this happens, it may have to download the docker image that it uses (python:3.11) so it is suggested you run the command

    python -c "import crew_python_runner"

Before using the library, as otherwise you may see a delay in usage. Alternatively, pull the image from docker yourself on the command line

    docker image pull python:3.11


## Usage

To use as a crew.ai tool:

    from crew_python_runner import python_runner

    # this is just an example - setup your agent however you like
    programmer = Agent(
        role='Senior Python Programmer',
        goal='Write simple, well crafted and bug-free Python code',
        backstory='You are a skilled Python programmer with a passion for writing working Python code',
        tools=[python_runner])


If you want to test it yourself:

    from crew_python_runner import runner
    result = runner.run_python('print("Hello, World!"))

This returns a class with 2 variables, *error_code*, an integer, and *output*, a string of the python output. In this case *error_code* will be 0 (meaning no error) and *output* will be *Hello, World!*.


## Future Enhancements

* Another tool giving coder agents the ability to *pip install* packages.
* The tool will auto-restart the docker instance if it falls over (which could be because of rogue code).
* The ability to log all code and results.

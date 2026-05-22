from ...tool import tool


@tool
async def run_python(code: str) -> dict:
    """Execute Python code in a sandboxed environment.

    Args:
        code: Python code to execute

    Returns:
        Execution result with stdout and return value
    """
    import io
    import sys

    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()

    result = None
    error = None

    try:
        exec_globals = {"__builtins__": __builtins__}
        exec(code, exec_globals)
        result = exec_globals.get("result")
    except Exception as e:
        error = str(e)
    finally:
        sys.stdout = old_stdout

    return {
        "stdout": captured_output.getvalue(),
        "result": result,
        "error": error,
    }


@tool
async def run_shell(command: str) -> dict:
    """Execute a shell command.

    Args:
        command: Shell command to execute

    Returns:
        Command output with stdout, stderr, and return code
    """
    import subprocess

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Command timed out",
            "returncode": -1,
        }

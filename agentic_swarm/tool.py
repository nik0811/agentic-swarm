from collections.abc import Callable

from .tools.base import Tool


def tool(func: Callable = None, *, name: str = None, description: str = None):
    """Decorator to convert a function into a Tool."""

    def decorator(f):
        return Tool(f, name=name, description=description)

    if func is not None:
        return decorator(func)
    return decorator

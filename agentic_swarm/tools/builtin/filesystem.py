from typing import List
from ...tool import tool
import os


@tool
async def read_file(path: str) -> str:
    """Read contents of a file.
    
    Args:
        path: Path to the file
    
    Returns:
        File contents
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@tool
async def write_file(path: str, content: str) -> dict:
    """Write content to a file.
    
    Args:
        path: Path to the file
        content: Content to write
    
    Returns:
        Status of write operation
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return {"status": "written", "path": path, "bytes": len(content)}


@tool
async def list_directory(path: str) -> List[str]:
    """List contents of a directory.
    
    Args:
        path: Path to the directory
    
    Returns:
        List of file and directory names
    """
    return os.listdir(path)


@tool
async def file_exists(path: str) -> bool:
    """Check if a file exists.
    
    Args:
        path: Path to check
    
    Returns:
        True if file exists
    """
    return os.path.exists(path)

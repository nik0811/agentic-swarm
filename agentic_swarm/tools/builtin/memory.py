from typing import List, Optional
from ...tool import tool


@tool
async def memory_store(content: str, metadata: dict = None) -> str:
    """Store content in long-term archival memory.
    
    Args:
        content: Content to store
        metadata: Optional metadata
    
    Returns:
        Memory ID
    """
    import uuid
    return str(uuid.uuid4())


@tool
async def memory_search(query: str, limit: int = 5) -> List[dict]:
    """Search archival memory.
    
    Args:
        query: Search query
        limit: Maximum results to return
    
    Returns:
        List of matching memories
    """
    return []


@tool
async def memory_recall(n: int = 10) -> List[dict]:
    """Get the last n messages from recall memory.
    
    Args:
        n: Number of messages to retrieve
    
    Returns:
        List of recent messages
    """
    return []

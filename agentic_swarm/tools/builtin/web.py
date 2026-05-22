from typing import List, Dict, Any
from ...tool import tool


@tool
async def web_search(query: str, max_results: int = 10) -> List[dict]:
    """Search the web for information.
    
    Args:
        query: Search query
        max_results: Maximum number of results
    
    Returns:
        List of search results with title, url, snippet
    """
    return [
        {
            "title": f"Result for: {query}",
            "url": f"https://example.com/search?q={query}",
            "snippet": f"This is a placeholder result for '{query}'",
        }
    ]


@tool
async def web_fetch(url: str) -> dict:
    """Fetch content from a URL.
    
    Args:
        url: URL to fetch
    
    Returns:
        Response with status, headers, and content
    """
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30)
            return {
                "status": response.status_code,
                "headers": dict(response.headers),
                "content": response.text[:10000],
            }
    except ImportError:
        return {
            "status": 0,
            "error": "httpx not installed",
            "content": "",
        }
    except Exception as e:
        return {
            "status": 0,
            "error": str(e),
            "content": "",
        }


@tool
async def api_call(
    url: str,
    method: str = "GET",
    headers: Dict[str, str] = None,
    body: Any = None,
) -> dict:
    """Make an HTTP API request.
    
    Args:
        url: API endpoint URL
        method: HTTP method (GET, POST, PUT, DELETE)
        headers: Request headers
        body: Request body (for POST/PUT)
    
    Returns:
        Response with status and data
    """
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=body if body else None,
                timeout=30,
            )
            return {
                "status": response.status_code,
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
            }
    except ImportError:
        return {"status": 0, "error": "httpx not installed"}
    except Exception as e:
        return {"status": 0, "error": str(e)}

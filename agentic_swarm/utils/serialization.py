import json
from datetime import datetime
from typing import Any
from pydantic import BaseModel


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)


def serialize(obj: Any) -> str:
    """Serialize an object to JSON string."""
    if isinstance(obj, BaseModel):
        return obj.model_dump_json()
    return json.dumps(obj, cls=DateTimeEncoder, default=str)


def deserialize(data: str) -> Any:
    """Deserialize a JSON string to Python object."""
    return json.loads(data)


def safe_serialize(obj: Any) -> str:
    """Serialize with fallback to str() for non-serializable objects."""
    try:
        return serialize(obj)
    except (TypeError, ValueError):
        return str(obj)

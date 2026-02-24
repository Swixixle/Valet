"""
Types for the Senate datasource adapter.
"""
from typing import TypedDict, Optional

class Senator(TypedDict):
    id: str
    name: str
    # Add other fields as needed

class VoteEvent(TypedDict, total=False):
    event_id: str
    senator_id: str
    bill_id: str
    vote: str
    timestamp: Optional[str]
    source_file: Optional[str]

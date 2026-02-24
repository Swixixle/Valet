from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

class AuditStatus(Enum):
    VERIFIED = "VERIFIED"
    NO_RECORD = "NO_RECORD"
    AMBIGUOUS = "AMBIGUOUS"
    INVALID_DATA = "INVALID_DATA"

@dataclass
class AuditResult:
    status: AuditStatus
    checks: List[Dict[str, Any]] = field(default_factory=list)
    anomalies: Optional[List[Dict[str, Any]]] = None

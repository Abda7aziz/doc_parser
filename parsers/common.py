from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class Segment:
    doc_id: str
    text: str
    page: Optional[int] = None
    section: Optional[str] = None
    kind: str = "text"
    meta: Optional[Dict] = None

def clean_text(s: str) -> str:
    if s is None:
        return ""
    s = s.replace("\u200f", "").replace("\u200e", "")
    return s.strip()

import re
from typing import Optional

def is_senate_vote_query(text: str) -> bool:
    if not text:
        return False
    text_lc = text.lower()
    vote_keywords = [
        "how did", "vote", "voted", "roll call", "voting record", "on bill", "hr", "s."
    ]
    if not any(kw in text_lc for kw in vote_keywords):
        return False
    # Must also contain a senator-like or bill-like token
    if extract_bill_id(text) or extract_senator_name(text):
        return True
    return False

def extract_bill_id(text: str) -> Optional[str]:
    # Accepts B1, HR123, H.R. 123, S1, S.1, etc.
    m = re.search(r"\b([A-Z]{1,3}|H\.R\.|S\.)\s?(\d+)\b", text)
    if m:
        prefix = m.group(1).replace(".", "").upper()
        number = m.group(2)
        return f"{prefix}{number}"
    # Accepts just B1
    m = re.search(r"\bB(\d+)\b", text)
    if m:
        return f"B{m.group(1)}"
    return None

def extract_senator_name(text: str) -> Optional[str]:
    # Try 'Senator <Name>'
    m = re.search(r"Senator ([A-Z][a-z]+(?: [A-Z][a-z]+)*)", text)
    if m:
        return m.group(1)
    # Fallback: last capitalized word sequence near 'voted'
    voted_idx = text.lower().find("voted")
    if voted_idx != -1:
        before = text[:voted_idx]
        caps = re.findall(r"([A-Z][a-z]+(?: [A-Z][a-z]+)*)", before)
        if caps:
            return caps[-1]
    return None

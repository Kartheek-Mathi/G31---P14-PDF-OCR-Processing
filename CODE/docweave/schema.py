from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import re
import unicodedata

RELATIONS = {
    "MANAGED_BY": ("Service", "Team"),
    "USES": ("Service", "Protocol"),
    "STORES_IN": ("Service", "Archive"),
    "REQUIRES": ("Service", "Policy"),
    "LOCATED_IN": ("Service", "Facility"),
    "REPORTS_TO": ("Team", "Council"),
    "RETENTION": ("Archive", "Duration"),
    "ALERTS": ("Service", "Team"),
}
LABELS = sorted(RELATIONS) + ["NO_RELATION"]

def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).split())

def entity_key(text: str) -> str:
    return normalize(text).casefold()

def digest(*parts: object, length: int = 24) -> str:
    return sha256("\x1f".join(map(str, parts)).encode()).hexdigest()[:length]

@dataclass(frozen=True)
class Chunk:
    id: str
    document_id: str
    page: int
    text: str
    method: str

@dataclass(frozen=True)
class Triple:
    id: str
    subject: str
    predicate: str
    object: str
    chunk_id: str
    quote: str
    confidence: float
    method: str

    def to_dict(self) -> dict:
        return asdict(self)

ENTITY_PATTERN = re.compile(
    r"\b[A-Z][A-Za-z0-9-]*(?: [A-Z][A-Za-z0-9-]*){0,2} "
    r"(?:Service|Team|Archive|Policy|Facility|Protocol|Council)\b|\b\d+ days\b"
)

def entities(text: str) -> list[str]:
    return list(dict.fromkeys(m.group(0) for m in ENTITY_PATTERN.finditer(text)))

def entity_type(name: str) -> str:
    return "Duration" if re.fullmatch(r"\d+ days", name) else name.rsplit(" ", 1)[-1]

def masked(text: str) -> str:
    """Mask detected entity values; never use gold annotations during inference."""
    return ENTITY_PATTERN.sub(lambda m: f" <{entity_type(m.group(0)).lower()}> ", text).lower()

def make_triple(chunk: Chunk, relation: str, confidence: float, method: str) -> Triple | None:
    if relation not in RELATIONS:
        return None
    found = entities(chunk.text)
    left, right = RELATIONS[relation]
    sources = [e for e in found if entity_type(e) == left]
    targets = [e for e in found if entity_type(e) == right]
    # Ambiguous endpoints are not silently selected.
    if len(sources) != 1 or len(targets) != 1 or sources[0] == targets[0]:
        return None
    return Triple(digest(chunk.id, sources[0], relation, targets[0]), sources[0],
                  relation, targets[0], chunk.id, chunk.text, float(confidence), method)

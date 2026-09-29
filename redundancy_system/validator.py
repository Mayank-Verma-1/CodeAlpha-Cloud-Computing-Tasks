"""
validator.py
------------
Core logic for Task 1 (Data Redundancy Removal System).

Responsibilities covered:
  1. Classify incoming data as "redundant" or "false positive"
  2. Validate new data against existing data before it is stored
  3. Prevent true duplicates from ever reaching the database
  4. Only pass unique, verified entries on to the database layer
  5. Keep the check efficient (blocking / indexing instead of a full scan)

Classification rules
---------------------
- EXACT DUPLICATE   : normalized record hash already exists       -> REJECT
- REDUNDANT         : similarity to an existing record >= 0.90     -> REJECT
                       (same real-world entity, just reworded/typo'd)
- FALSE POSITIVE    : similarity between 0.60 and 0.90             -> ACCEPT
                       (looked suspicious at first glance, e.g. same
                       city/category, but it is actually a distinct record)
- UNIQUE            : similarity < 0.60                             -> ACCEPT
"""

import hashlib
import json
from difflib import SequenceMatcher

REDUNDANT_THRESHOLD = 0.90
FALSE_POSITIVE_THRESHOLD = 0.60


def normalize(record: dict) -> dict:
    """Lowercase/trim every string field so 'John Doe' == ' john doe '."""
    return {
        k: (v.strip().lower() if isinstance(v, str) else v)
        for k, v in record.items()
    }


def compute_hash(record: dict) -> str:
    """Deterministic fingerprint of the normalized record (for O(1) exact-dup check)."""
    normalized = normalize(record)
    canonical = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def compute_block_key(record: dict, key_field: str = "name") -> str:
    """
    Cheap 'blocking' key so we never compare a new record against the
    entire database -- only against records that could plausibly match.
    Here we use the first 3 characters of the chosen field.
    """
    value = str(record.get(key_field, "")).strip().lower()
    return value[:3] if value else "___"


def similarity(a: dict, b: dict) -> float:
    """Average field-by-field text similarity between two normalized records."""
    a, b = normalize(a), normalize(b)
    keys = set(a.keys()) | set(b.keys())
    if not keys:
        return 0.0
    scores = []
    for k in keys:
        va, vb = str(a.get(k, "")), str(b.get(k, ""))
        scores.append(SequenceMatcher(None, va, vb).ratio())
    return sum(scores) / len(scores)


class ValidationResult:
    def __init__(self, status: str, accepted: bool, reason: str, matched_record=None, score: float = 0.0):
        self.status = status              # 'duplicate' | 'redundant' | 'false_positive' | 'unique'
        self.accepted = accepted          # True -> safe to insert
        self.reason = reason
        self.matched_record = matched_record
        self.score = score

    def __repr__(self):
        return f"<ValidationResult {self.status} accepted={self.accepted} score={self.score:.2f}>"


class RedundancyValidator:
    """Validates a new record against what's already in the cloud database."""

    def __init__(self, db, key_field: str = "name"):
        self.db = db
        self.key_field = key_field

    def validate(self, record: dict) -> ValidationResult:
        record_hash = compute_hash(record)
        block_key = compute_block_key(record, self.key_field)

        # 1) Fast path: exact duplicate check via hash index
        if self.db.exists_by_hash(record_hash):
            return ValidationResult(
                status="duplicate",
                accepted=False,
                reason="Exact match already exists in the database.",
                score=1.0,
            )

        # 2) Fuzzy check, but only against records in the same block
        #    (huge efficiency win vs. comparing against every row)
        candidates = self.db.fetch_candidates(block_key)
        best_score, best_match = 0.0, None
        for cand in candidates:
            cand_data = json.loads(cand["data"])
            score = similarity(record, cand_data)
            if score > best_score:
                best_score, best_match = score, cand_data

        if best_score >= REDUNDANT_THRESHOLD:
            return ValidationResult(
                status="redundant",
                accepted=False,
                reason=f"{best_score:.0%} similar to an existing record -- treated as redundant.",
                matched_record=best_match,
                score=best_score,
            )

        if best_score >= FALSE_POSITIVE_THRESHOLD:
            return ValidationResult(
                status="false_positive",
                accepted=True,
                reason=f"{best_score:.0%} similar to an existing record, but distinct enough "
                       f"to be a genuine new entry (flagged for optional review).",
                matched_record=best_match,
                score=best_score,
            )

        return ValidationResult(
            status="unique",
            accepted=True,
            reason="No meaningfully similar record found.",
            score=best_score,
        )

    def submit(self, record: dict) -> ValidationResult:
        """
        Full pipeline required by Task 1:
        validate -> reject duplicates/redundant -> append only unique/verified data.
        """
        result = self.validate(record)
        if result.accepted:
            record_hash = compute_hash(record)
            block_key = compute_block_key(record, self.key_field)
            status = "verified" if result.status == "unique" else "verified-flagged"
            self.db.insert(record, record_hash, block_key, status=status)
        return result

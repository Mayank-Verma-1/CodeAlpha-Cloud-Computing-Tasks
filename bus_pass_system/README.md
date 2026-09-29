# Task 1 — Data Redundancy Removal System

A small Python system that classifies incoming records as **redundant**,
**false positive**, or **unique**, validates each one against what's
already stored, and only appends unique/verified entries to the (cloud)
database.

## Files
- `database.py` — SQLite-backed stand-in for a cloud database. Indexed by
  record hash (exact-match lookup) and by a "block key" (for fast fuzzy
  lookup without scanning the whole table).
- `validator.py` — the core engine: hashing, normalization, similarity
  scoring, and the classify/validate/submit pipeline.
- `main.py` — demo script that runs 8 sample incoming records through the
  pipeline and prints a report.

## How it maps to the task requirements

| Requirement | Where it's handled |
|---|---|
| Classify data as redundant or false positive | `validator.py` → `RedundancyValidator.validate()` returns one of `duplicate` / `redundant` / `false_positive` / `unique` based on similarity thresholds |
| Validate new data against existing data | `validate()` checks the incoming record's hash and similarity against records already in the DB before any insert |
| Prevent duplicate data from being added | Exact matches (`duplicate`) and near-matches above 90% similarity (`redundant`) are rejected — `submit()` never calls `db.insert()` for these |
| Append only unique and verified data | `submit()` only inserts when `result.accepted` is `True` (status `unique` or `false_positive`) |
| Ensure accuracy/efficiency | Two indexes (`record_hash`, `block_key`) mean exact checks are O(1) and fuzzy checks only compare against a small "block" of plausibly-matching rows, not the whole table |

## Classification thresholds
- **Duplicate** — normalized hash already exists → rejected
- **Redundant** — similarity ≥ 90% → rejected (same entity, reworded/typo'd)
- **False positive** — similarity 60–90% → accepted (looked suspicious, but is a genuinely distinct record) and flagged for optional human review
- **Unique** — similarity < 60% → accepted normally

These thresholds are constants at the top of `validator.py` and can be
tuned per dataset.

## Run it
```bash
python3 main.py
```
This resets `cloud_data.db`, feeds 8 sample records through the system, and
prints which were accepted/rejected and why, followed by the final
database contents.

## Extending to a real cloud deployment
Swap `CloudDatabase` in `database.py` for a client against your actual
cloud DB (e.g. `boto3` for DynamoDB, `psycopg2` for a managed Postgres
instance) — keep the same `insert` / `exists_by_hash` / `fetch_candidates`
method signatures and `validator.py` needs no changes.

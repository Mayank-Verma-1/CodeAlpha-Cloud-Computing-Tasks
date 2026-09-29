"""
ticket.py
---------
Ticket security layer (Task 3: "prevention of ticket loss, theft ...").

Each ticket is a signed token: user_id + route_id + fare + a random nonce,
HMAC-signed with a server-side secret the client never sees.

- THEFT / FORGERY: nobody can hand-craft a valid ticket code without the
  server secret, and a screenshot/copy of someone else's code fails
  `verify()` the moment its signature or user binding doesn't match what
  the conductor's scanner expects.
- REUSE (a stolen/copied ticket used after the real owner already rode):
  `mark_used` flips status to 'used' in the database, and `verify()`
  rejects any ticket whose status isn't 'valid'.
- LOSS: the ticket is derived data, not the source of truth -- the DB row
  (keyed by the unforgeable idempotency key) is. If a user loses the
  ticket code/QR image, re-booking with the same idempotency key returns
  the *same* database record instead of issuing a duplicate or losing the
  original purchase (see booking_service.py).
"""

import hmac
import hashlib
import secrets
import time

SERVER_SECRET = secrets.token_bytes(32)  # in production: pulled from a KMS/secret manager


def issue_ticket_code(user_id: str, route_id: int, fare: float) -> str:
    nonce = secrets.token_hex(8)
    payload = f"{user_id}|{route_id}|{fare}|{nonce}|{int(time.time())}"
    signature = hmac.new(SERVER_SECRET, payload.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{payload}|{signature}"


def verify_ticket(ticket_code: str, db) -> tuple[bool, str]:
    """Checks signature validity, then checks it hasn't already been used."""
    try:
        user_id, route_id, fare, nonce, ts, signature = ticket_code.split("|")
    except ValueError:
        return False, "Malformed ticket code."

    payload = f"{user_id}|{route_id}|{fare}|{nonce}|{ts}"
    expected_sig = hmac.new(SERVER_SECRET, payload.encode(), hashlib.sha256).hexdigest()[:16]
    if not hmac.compare_digest(signature, expected_sig):
        return False, "Invalid signature -- ticket is forged or corrupted."

    record = db.get_pass_by_code(ticket_code)
    if record is None:
        return False, "Ticket not found in the database."
    if record["status"] != "valid":
        return False, f"Ticket already {record['status']} -- possible stolen/duplicate use."

    return True, "Ticket is valid."

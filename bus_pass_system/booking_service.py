"""
booking_service.py
-------------------
The booking API (Task 3 core). Stateless by design -- every call carries
everything it needs and all state lives in the database -- which is what
lets it scale horizontally across any number of autoscaled workers
(reliability/scalability requirement) instead of pinning a user to one
server the way session-based traditional booking sites often do.

book_ticket() is idempotent: calling it twice with the same
idempotency_key (e.g. a mobile app retrying after a dropped connection)
returns the original ticket instead of double-booking or double-charging.
"""

import time
from datetime import datetime, timezone

from pricing import PricingEngine
from ticket import issue_ticket_code


class BookingError(Exception):
    pass


class BookingService:
    def __init__(self, db):
        self.db = db
        self.pricing = PricingEngine(db)

    def book_ticket(self, user_id: str, route_id: int, idempotency_key: str, client_supplied_price=None):
        # Server-side price only -- a tampered/incorrect client price is ignored,
        # not even looked at, closing off the "incorrect pricing" failure mode.
        fare = self.pricing.quote(route_id)

        with self.db.lock:
            # Idempotency check FIRST: a retried request (network blip, user
            # double-tapping "Buy") returns the ticket already issued instead
            # of creating a duplicate purchase or losing the original one.
            existing = self.db.find_existing_booking(idempotency_key)
            if existing:
                return {"ticket": existing, "status": "already_booked", "fare_charged": existing["fare_charged"]}

            ticket_code = issue_ticket_code(user_id, route_id, fare)
            issued_at = datetime.now(timezone.utc).isoformat()

            record = self.db.reserve_seat_and_issue(
                user_id=user_id,
                route_id=route_id,
                fare_charged=fare,
                ticket_code=ticket_code,
                idempotency_key=idempotency_key,
                issued_at=issued_at,
            )

        if record is None:
            raise BookingError(f"Route {route_id} is sold out.")

        return {"ticket": record, "status": "booked", "fare_charged": fare}

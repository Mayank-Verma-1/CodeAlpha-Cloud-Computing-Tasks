"""
pricing.py
----------
Server-side pricing engine (Task 3: "prevention of ... incorrect pricing").

The fare is *never* accepted from the client -- it is always looked up
here, from the route record in the database, at booking time. A booking
request that includes its own "price" field is simply ignored, which
closes off the most common real-world booking-site bug: a tampered
client request under-paying for a ticket.
"""


class PricingError(Exception):
    pass


class PricingEngine:
    def __init__(self, db):
        self.db = db

    def quote(self, route_id: int) -> float:
        route = self.db.get_route(route_id)
        if route is None:
            raise PricingError(f"No such route: {route_id}")
        return round(float(route["fare"]), 2)

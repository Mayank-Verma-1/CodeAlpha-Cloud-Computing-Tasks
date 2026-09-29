"""
load_test.py
-------------
"Test and deploy the system to provide a seamless booking experience"
(Task 3, last bullet). Simulates a burst of concurrent booking requests
-- including retries (duplicate idempotency keys) and an oversold route
-- and verifies the system stays correct throughout, while the autoscaler
log shows capacity being provisioned up and back down.
"""

import random
import time
import uuid

from database import CloudDatabase
from booking_service import BookingService, BookingError
from autoscaler import AutoScaler
from ticket import verify_ticket


def run_load_test():
    db = CloudDatabase(db_path="bus_pass.db", reset=True)
    route_id = db.add_route("Central Station", "Airport", fare=2.50, capacity=50)
    service = BookingService(db)
    scaler = AutoScaler(min_workers=2, max_workers=16, scale_step=2, cooldown_sec=0.0)

    NUM_REQUESTS = 120  # far more than the 50-seat capacity -> forces overbooking attempts
    RETRY_RATE = 0.15   # 15% of requests are "network retries" reusing a prior key

    results = {"booked": 0, "already_booked": 0, "sold_out": 0, "errors": 0}
    issued_keys = []
    futures = []

    for i in range(NUM_REQUESTS):
        # Simulate a spike in traffic and let the autoscaler react to queue depth
        pending = NUM_REQUESTS - i
        scaler.observe_and_scale(pending)

        if issued_keys and random.random() < RETRY_RATE:
            key = random.choice(issued_keys)  # simulate a dropped-connection retry
        else:
            key = str(uuid.uuid4())
            issued_keys.append(key)

        user_id = f"user_{i % 40}"
        # An attacker/buggy client trying to pay less than the real fare --
        # the service must ignore this completely.
        tampered_price = 0.01

        futures.append(scaler.submit(_attempt_booking, service, user_id, route_id, key, tampered_price, results))

    for f in futures:
        f.result()

    scaler.shutdown()

    # --- Verification pass -----------------------------------------
    all_passes = db.all_passes()
    route = db.get_route(route_id)

    fares_correct = all(p["fare_charged"] == 2.50 for p in all_passes)
    no_overbooking = route["seats_sold"] <= route["capacity"]
    unique_tickets = len({p["ticket_code"] for p in all_passes}) == len(all_passes)

    # Spot-check ticket integrity/anti-theft verification on real + forged codes
    sample_ticket = all_passes[0]["ticket_code"]
    valid, reason = verify_ticket(sample_ticket, db)
    forged_ticket = sample_ticket[:-4] + "0000"  # tamper with the signature
    forged_valid, forged_reason = verify_ticket(forged_ticket, db)

    print("=" * 70)
    print("LOAD TEST REPORT")
    print("=" * 70)
    print(f"Requests sent           : {NUM_REQUESTS}")
    print(f"Tickets booked          : {results['booked']}")
    print(f"Idempotent retries caught: {results['already_booked']}")
    print(f"Correctly sold-out      : {results['sold_out']}")
    print(f"Unexpected errors       : {results['errors']}")
    print(f"Route capacity/sold     : {route['capacity']}/{route['seats_sold']}")
    print()
    print(f"[{'PASS' if no_overbooking else 'FAIL'}] No overbooking beyond capacity")
    print(f"[{'PASS' if fares_correct else 'FAIL'}] Every ticket charged the correct server-side fare (tampered price ignored)")
    print(f"[{'PASS' if unique_tickets else 'FAIL'}] Every issued ticket code is unique (no duplicates/loss)")
    print(f"[{'PASS' if valid else 'FAIL'}] Genuine ticket verifies successfully ({reason})")
    print(f"[{'PASS' if not forged_valid else 'FAIL'}] Tampered/forged ticket is correctly rejected ({forged_reason})")
    print()
    print("Autoscaler activity (dynamic server provisioning):")
    for entry in scaler.log[:10]:
        print(f"  {entry}")
    if len(scaler.log) > 10:
        print(f"  ... ({len(scaler.log) - 10} more scaling events)")

    db.close()


def _attempt_booking(service, user_id, route_id, key, tampered_price, results):
    try:
        result = service.book_ticket(user_id, route_id, key, client_supplied_price=tampered_price)
        results[result["status"]] = results.get(result["status"], 0) + 1
    except BookingError:
        results["sold_out"] += 1
    except Exception:
        results["errors"] += 1


if __name__ == "__main__":
    run_load_test()

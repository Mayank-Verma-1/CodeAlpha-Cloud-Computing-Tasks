"""
main.py
-------
Demo runner for Task 1: Data Redundancy Removal System.

Feeds a stream of incoming "cloud upload" records through the validator and
prints a report showing exactly how each was classified and whether it was
appended to the database -- proving all 5 task requirements are satisfied:

  1. Classifies data as redundant / false positive
  2. Validates new data against existing data
  3. Prevents duplicate data from entering the database
  4. Appends only unique and verified entries
  5. Keeps the database accurate & efficient
"""

from database import CloudDatabase
from validator import RedundancyValidator

INCOMING_RECORDS = [
    {"name": "Aarav Sharma", "email": "aarav.sharma@mail.com", "city": "Delhi"},
    {"name": "Aarav Sharma", "email": "aarav.sharma@mail.com", "city": "Delhi"},          # exact duplicate
    {"name": "aarav sharma", "email": "aarav.sharma@mail.com ", "city": "delhi"},          # duplicate (case/whitespace)
    {"name": "Aarav Sharma", "email": "aarav.sharma@mail.com", "city": "Mumbai"},          # redundant (near-dup, 1 field changed)
    {"name": "Aarti Sharma", "email": "aarti.sharma@mail.com", "city": "Pune"},             # false positive (similar name, different person)
    {"name": "Rohan Verma", "email": "rohan.verma@mail.com", "city": "Bengaluru"},          # unique
    {"name": "Rohan Verma", "email": "rohan.v99@mail.com", "city": "Bengaluru"},            # redundant (only the email changed slightly -> same person, blocked)
    {"name": "Sneha Iyer", "email": "sneha.iyer@mail.com", "city": "Chennai"},              # unique
]


def main():
    db = CloudDatabase(db_path="cloud_data.db", reset=True)
    validator = RedundancyValidator(db, key_field="name")

    print(f"{'#':<3} {'STATUS':<15} {'ACTION':<10} SCORE  RECORD")
    print("-" * 90)

    for i, record in enumerate(INCOMING_RECORDS, start=1):
        result = validator.submit(record)
        action = "INSERTED" if result.accepted else "REJECTED"
        print(f"{i:<3} {result.status:<15} {action:<10} {result.score:.2f}   {record}")
        if result.matched_record:
            print(f"    -> matched existing: {result.matched_record}  ({result.reason})")

    print("-" * 90)
    final_records = db.fetch_all()
    print(f"\nIncoming records processed : {len(INCOMING_RECORDS)}")
    print(f"Records stored in database : {db.count()}  (duplicates/redundant entries blocked)")
    print("\nFinal database contents:")
    for r in final_records:
        print(f"  id={r['id']:<3} status={r['status']:<16} data={r['data']}")

    db.close()


if __name__ == "__main__":
    main()

"""First-pass migration transform, written straight from spec/transform-spec.md.

Deliberately incomplete: the null, duplicate, and malformed-phone handling
that the spec waves at ("handle these cases sensibly") still needs to be
worked out interactively. See this task's README for how.
"""
import csv
import json


def normalize_phone(raw):
    return raw.replace("(", "").replace(")", "").replace("-", "").replace(" ", "").replace(".", "")


def parse_date(raw):
    return raw  # TODO: not actually normalized to ISO-8601 yet


def parse_customer_row(row):
    return {
        "customer_id": row["id"],
        "full_name": row["name"],
        "phone_e164": normalize_phone(row["phone"]),
        "signup_date": parse_date(row["signup"]),
    }


def migrate(csv_path):
    with open(csv_path, newline="") as f:
        return [parse_customer_row(row) for row in csv.DictReader(f)]


if __name__ == "__main__":
    # Run from this task's root folder: python migration/migrate.py
    print(json.dumps(migrate("data/legacy_customers_sample.csv"), indent=2))

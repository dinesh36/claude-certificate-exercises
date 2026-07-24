# Legacy CRM to New System: Row Transform Spec

Source: `data/legacy_customers_sample.csv` (columns: `id`, `name`, `phone`, `signup`)
Target: one JSON object per row (see `CLAUDE.md`'s "Conventions" section for the exact target schema).

## Field mapping

- `id` -> `customer_id`, unchanged.
- `name` -> `full_name`, unchanged.
- `phone` -> `phone_e164`. Normalize phone numbers to a consistent format.
- `signup` -> `signup_date`. Parse the signup date into a consistent format.

## Notes

- Some legacy rows are missing fields, and some customer IDs appear more than once across export batches. Handle these cases sensibly.

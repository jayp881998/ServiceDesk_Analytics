# Synthetic sample data — READ FIRST

**Do not commit any real Zendesk export here.** The original `data sample.txt` from the
real system contained genuine helpdesk PII (names, emails, addresses, ticket text) and
must never be published. This folder holds **only fabricated** JSON that mirrors the
Zendesk *shape* so the pipeline runs end to end without any real data.

## What to generate
Two files matching the fields in `docs/DATA_DICTIONARY.md`:

- `tickets_sample.json` — 30–100 tickets. Fabricated `id`, `created_at`/`updated_at`
  spread across dates, random `status`/`priority`/`type`, and a nested `metric_set`
  with plausible reply/resolution/on-hold times. Include `via`, `tags`, and a few
  `brand_id`/`group_id` values so the dimensions populate.
- `users_sample.json` — 10–20 users with fake names/emails (e.g. `Agent One`,
  `agent1@example.com`), roles (`agent`, `end-user`), and login timestamps.

## Rules
- Fake names only (`Alex Rivera`, `Sam Okafor`…), example.com emails, no real orgs.
- Keep field names and nesting identical to real Zendesk JSON so `OPENJSON` still parses.
- Enough variety that the 5 dashboards render (a range of statuses, dates, agents, channels).

A short Python (Faker) or hand-written generator is enough. The new-chat brief includes
instructions to build one.

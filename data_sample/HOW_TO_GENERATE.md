# Synthetic sample data

**Do not commit any real Zendesk export here.** This folder contains only fabricated
JSON that mirrors the Zendesk field structure so the pipeline runs end to end without
any real data.

## What's included

| File | Description |
|---|---|
| `tickets_sample.json` | 800 synthetic tickets, 2019–2026 |
| `users_sample.json` | 25 synthetic users (agents, admins, end-users) |
| `generate_sample.py` | Script that produced both files |

## Regenerating

```
python data_sample/generate_sample.py
```

Writes fresh `tickets_sample.json` and `users_sample.json` to this folder.
Default counts: 800 tickets, 25 users. Edit the constants at the top of the script
to change volume.

## Rules for any replacement data

- Fake names only (`Alex Rivera`, `Sam Okafor`), `@example.com` emails, no real orgs.
- Field names and nesting must be identical to real Zendesk JSON so `OPENJSON` still parses correctly.
- Include enough variety across `status`, `priority`, `channel`, `group_id`, and date range
  for all three dashboards to render meaningfully.

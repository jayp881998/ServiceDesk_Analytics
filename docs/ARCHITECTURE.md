# Architecture

The pipeline was delivered in four phases.

## Phase 1 — Data extraction (Python)

- **Auth** via environment variables (`.env`, gitignored): Zendesk email, API token, subdomain.
- **Tickets:** Zendesk *incremental* export endpoint with `include=metric_sets`, from a
  fixed `start_time` (2019) forward. Iterates `next_page` until `end_of_stream`.
- **Users:** cursor pagination (`page[size]=100`, `after_cursor`).
- **Reliability:** HTTP 429 handled by sleeping for the `retry-after` header value, then retrying.
- **Deduplication:** each ticket tracked by a unique `(id, updated_at)` key so re-runs never
  double-count.
- **Output:** JSON files for tickets and users; also normalized to a pandas DataFrame for inspection.

## Phase 2 — Warehouse load (SQL Server)

- Stored procedure loads the latest JSON via `OPENROWSET (BULK ... SINGLE_CLOB)`.
- **Validation:** `ISJSON` gate — the load aborts if either file is not valid JSON.
- **Parsing:** `OPENJSON ... WITH (...)` maps deeply nested Zendesk JSON (including
  `metric_set.*`, `via.source.*`, and `tags` via `CROSS APPLY`) into typed columns.
- **Tables:** `Tickets`, `Ticket_Metrics`, `Tags`, `Via`, `Users` — a fact table
  (tickets/metrics) with conformed dimensions (users/agents, via/channel, tags, date).
- **Idempotency:** rebuild/UPSERT logic keeps the warehouse current without duplicates.

## Phase 3 — Business intelligence (Power BI)

- SQL Server connected as the source; **star-schema** model with a dedicated measures table.
- **DAX** measures: SLA compliance, backlog aging, first-response time, resolution time,
  on-hold/wait time, reopen rate, agent productivity, tickets by hour.
- **5 dashboards** tailored to executives, operations, and agents; slicers, filters, RLS.

## Phase 4 — Automation & monitoring

- **Windows Task Scheduler** runs `extract_zendesk.py` on a schedule.
- **SQL Server Agent** runs the load stored procedure every **45 minutes**.
- **Power BI** scheduled refresh reads the updated warehouse.
- **Data quality:** `ISJSON` validation, deduplication, and reconciliation of dashboard
  numbers against Zendesk's native reports during testing.

## Data flow

```
Zendesk API → Python ETL (dedup, retries) → JSON → SQL Server (OPENJSON load, star schema)
→ Power BI (DAX semantic model, 5 dashboards) → scheduled refresh (Task Scheduler + SQL Agent)
```

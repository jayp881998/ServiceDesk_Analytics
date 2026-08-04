# Power BI — dashboards & model

This folder contains the visual outputs from the Power BI report built on top of the
SQL Server warehouse.

## Files

| File | Description |
|---|---|
| `model_star_schema.png` | Power BI model view — star schema with Tickets (fact), Dim_Date, Dim_User (Requester), Dim_User (Agent), Dim_Group, Ticket_Metrics, Via, and Tags |
| `dash_executive.png` | Executive Overview — KPI tiles, ticket volume by year, status mix, channel mix, priority and group breakdown |
| `dash_operations.png` | Operations Control — monthly trend, FRT/full-resolution histograms, backlog aging, SLA % by priority |
| `dash_agent.png` | Agent Performance — tickets handled, median FRT, reopen rate, and reply distribution per agent |
| `make_dashboards.py` | Python script that regenerates all four PNGs from the synthetic sample data |

## Dashboards

All three dashboards are built on the synthetic sample data (800 tickets, 2019–2026).

**Executive Overview** tracks total ticket volume, SLA compliance, open backlog, and
reopen rate — broken down by year, status, channel, priority, and support group.

**Operations Control** focuses on response and resolution times — monthly volume trend,
first-resolution and full-resolution histograms with median markers, backlog aging by
age bucket, and SLA compliance split by priority tier.

**Agent Performance** shows per-agent workload (tickets handled), median first resolution
time, reopen rate with a team average marker, and the reply-count distribution across
all tickets.

## Star schema

The model follows a standard star schema:

- **Fact:** `Tickets` joined 1:1 to `Ticket_Metrics`
- **Dimensions:** `Dim_Date`, `Dim_User` (two role-playing instances — Requester and Agent), `Dim_Group`
- **Satellites:** `Via` (channel/source, 1:1), `Tags` (bridge, 1:many)

See [`docs/DATA_DICTIONARY.md`](../docs/DATA_DICTIONARY.md) for the full field reference.

## Regenerating the PNGs

```
python powerbi/make_dashboards.py
```

Reads from `data_sample/tickets_sample.json` and `data_sample/users_sample.json`.

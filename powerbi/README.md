# Power BI — what to add here

Proof that turns the repo from "code" into "a shipped BI product." Add:

1. **`model_star_schema.png`** — screenshot of the Power BI model view (Tickets fact +
   Dim_Date, Calendar, Group, End_Users, Agent_User, Tags, Via, Metrics, Measures table).
   This single image proves the star schema and the DAX measures at a glance.
2. **Dashboard screenshots** — one PNG per view: Executive Overview, Operations Control,
   Agent Performance (SLA compliance, backlog aging, FRT/TTR, reopen rate, productivity).
   Built on the **synthetic** data so no real figures appear.
3. **`IT-Support-Analytics.pbix`** (optional) — the report file rebuilt on synthetic data.
   It's large and gitignored by default; either commit intentionally or link a download.
4. **`measures.md`** (optional) — list the key DAX measures with one-line definitions
   (Avg First Reply Time, Median Full Resolution Time, SLA %, Backlog Aging buckets,
   Reopen Rate, Tickets by Hour).

Embed `model_star_schema.png` and 2–3 dashboard shots in the repo README and in the
portfolio case study.

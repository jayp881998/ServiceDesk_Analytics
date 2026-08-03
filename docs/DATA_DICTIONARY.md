# Data dictionary

Tables created by `sql_scripts/update_procedure.sql` from the Zendesk JSON.

## Tickets (fact)
Core ticket record. Key columns:

| Column | Type | Source (JSON) |
|---|---|---|
| Id | INT (PK) | `$.id` |
| Created At | DATETIME2 | `$.created_at` |
| Updated At | DATETIME2 | `$.updated_at` |
| Type | NVARCHAR(50) | `$.type` |
| Subject | NVARCHAR(255) | `$.subject` |
| Priority | NVARCHAR(50) | `$.priority` |
| Status | NVARCHAR(50) | `$.status` |
| Requester Id | BIGINT | `$.requester_id` |
| Assignee Id | BIGINT | `$.assignee_id` |
| Group Id | BIGINT | `$.group_id` |
| Brand Id | BIGINT | `$.brand_id` |
| Custom Status Id | BIGINT | `$.custom_status_id` |
| Due At | DATETIME2 | `$.due_at` |

## Ticket_Metrics (fact measures)
Timing/quality metrics per ticket, from `$.metric_set.*`:

First Resolution Time, Full Resolution Time, Reply Time, Agent Wait Time, Requester Wait
Time, On Hold Time (each Business + Calendar), Reopens, Replies, Assigned At, Solved At,
Status Updated At, Ticket Id, Created At, Updated At, URL.

## Tags (dimension / bridge)
| Column | Type | Source |
|---|---|---|
| TicketID | NVARCHAR(100) | `$.id` |
| Tag | NVARCHAR(255) | `$.tags[*]` (CROSS APPLY) |

## Via (dimension — channel/source)
TicketID, Channel, Source_Channel, Source_Subject, Source_Ticket_Id, Rel,
Source_From_Name/Address, Source_To_Name/Address — from `$.via.*`.

## Users (dimension — requesters/agents)
Id (PK), Email, Name, Phone, Photo_Url, Role, plus login/activity fields.

> All values in `data_sample/` are synthetic. Real requester/agent PII from the source
> system is never included.

"""
Synthetic Zendesk sample generator.

Produces tickets_sample.json and users_sample.json whose SHAPE (field names and
nesting) matches the real Zendesk API output the pipeline consumes — so
sql_scripts/update_procedure.sql (OPENJSON) parses them exactly like production —
but every value is fabricated. No real names, emails, orgs, or ticket text.

Usage:
    python generate_sample.py                 # 500 tickets, 25 users
    python generate_sample.py 800 30          # custom counts

Stdlib only — no external packages required.
"""
import json, random, sys
from datetime import datetime, timedelta, timezone

random.seed(42)  # reproducible

N_TICKETS = int(sys.argv[1]) if len(sys.argv) > 1 else 500
N_USERS   = int(sys.argv[2]) if len(sys.argv) > 2 else 25

START = datetime(2019, 1, 1, tzinfo=timezone.utc)
NOW   = datetime.now(timezone.utc)

FIRST = ["Alex","Sam","Jordan","Taylor","Casey","Riley","Morgan","Jamie","Avery","Quinn",
         "Devon","Skyler","Rowan","Harper","Emerson","Blake","Reese","Parker","Sage","Drew"]
LAST  = ["Rivera","Okafor","Nguyen","Patel","Kowalski","Santos","Haddad","Larsen","Mori",
         "Costa","Ibrahim","Novak","Reyes","Fischer","Adeyemi","Sokolov","Cruz","Bauer"]
ROLES_AGENT = ["agent","admin"]
GROUPS = [(101,"IT Helpdesk"),(102,"Network Ops"),(103,"Application Support"),(104,"AV / Classroom Tech")]
BRANDS = [1930001, 1930002]
CHANNELS = ["email","web","chat","api","voice"]
TYPES = ["incident","question","problem","task", None]
PRIORITIES = ["low","normal","high","urgent", None]
STATUSES = ["new","open","pending","hold","solved","closed"]
STATUS_WEIGHTS = [3,8,10,4,30,45]  # most tickets end solved/closed
TAG_POOL = ["password","vpn","printer","email","login","onboarding","wifi","account",
            "software-install","hardware","classroom-av","access-request","outlook",
            "sso","mfa","network","laptop","offboarding"]
SUBJECTS = [
    "Unable to log into the portal","Password reset request","VPN will not connect",
    "Printer offline in lab","New hire account setup","MFA not sending codes",
    "Email not syncing on laptop","Software install request","Wi-Fi dropping in classroom",
    "Access request for shared drive","Account locked out","Projector not displaying",
    "Slow performance on workstation","Offboarding - disable account","SSO error on login",
]

def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def rand_dt(after, max_minutes):
    return after + timedelta(minutes=random.randint(1, max_minutes))

# ---------------- Users ----------------
users = []
agent_ids = []
n_agents = max(5, N_USERS // 4)
for i in range(N_USERS):
    uid = 500000000 + i
    fn, ln = random.choice(FIRST), random.choice(LAST)
    is_agent = i < n_agents
    role = random.choice(ROLES_AGENT) if is_agent else "end-user"
    if is_agent:
        agent_ids.append(uid)
    created = rand_dt(START, 60*24*300)
    users.append({
        "id": uid,
        "email": f"{fn.lower()}.{ln.lower()}{i}@example.com",
        "name": f"{fn} {ln}",
        "phone": None if random.random() < 0.6 else f"+1416555{random.randint(1000,9999)}",
        "photo_url": None,
        "role": role,
        "active": random.random() > 0.05,
        "last_login_at": None if random.random() < 0.1 else iso(rand_dt(created, 60*24*200)),
        "created_at": iso(created),
        "updated_at": iso(NOW - timedelta(days=random.randint(0, 120))),
    })
enduser_ids = [u["id"] for u in users if u["role"] == "end-user"] or [u["id"] for u in users]

# ---------------- Tickets ----------------
tickets = []
span_minutes = int((NOW - START).total_seconds() // 60)
for i in range(N_TICKETS):
    tid = 10000 + i
    created = START + timedelta(minutes=random.randint(0, span_minutes))
    status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
    priority = random.choices(PRIORITIES, weights=[4,10,5,2,2])[0]
    assignee = random.choice(agent_ids) if status not in ("new",) else (random.choice(agent_ids) if random.random()>0.3 else None)
    requester = random.choice(enduser_ids)
    group_id, _ = random.choice(GROUPS)
    channel = random.choices(CHANNELS, weights=[45,30,12,8,5])[0]

    # metric timings (business <= calendar), scaled loosely by priority
    scale = {"urgent":0.4,"high":0.7,"normal":1.0,"low":1.6,None:1.2}[priority]
    reply_b = int(random.randint(2, 240) * scale)
    reply_c = int(reply_b * random.uniform(1.1, 2.5))
    fr_b = int(random.randint(10, 600) * scale)
    fr_c = int(fr_b * random.uniform(1.1, 2.6))
    full_b = int(fr_b * random.uniform(1.0, 3.0))
    full_c = int(full_b * random.uniform(1.1, 2.6))
    onhold_b = random.choice([0,0,0,15,60,180])
    reopens = random.choices([0,0,0,1,2], weights=[70,0,0,25,5])[0]
    replies = random.randint(1, 9)

    assigned_at = rand_dt(created, max(2, reply_b))
    solved = status in ("solved","closed")
    solved_at = iso(rand_dt(created, max(5, full_c))) if solved else None
    latest_comment = rand_dt(created, max(5, full_c))

    subject = random.choice(SUBJECTS)
    tickets.append({
        "id": tid,
        "url": f"https://example.zendesk.com/api/v2/tickets/{tid}.json",
        "external_id": None,
        "created_at": iso(created),
        "updated_at": iso(latest_comment),
        "generated_timestamp": int(latest_comment.timestamp()),
        "type": random.choice(TYPES),
        "subject": subject,
        "raw_subject": subject,
        "description": f"[synthetic] {subject}. Reported via {channel}. Reference #{tid}.",
        "priority": priority,
        "status": status,
        "recipient": "support@example.com" if channel == "email" else None,
        "requester_id": requester,
        "submitter_id": requester,
        "assignee_id": assignee,
        "organization_id": None,
        "group_id": group_id,
        "forum_topic_id": None,
        "problem_id": None,
        "has_incidents": random.random() < 0.05,
        "is_public": True,
        "due_at": None,
        "custom_status_id": 900000 + STATUSES.index(status),
        "brand_id": random.choice(BRANDS),
        "allow_channelback": False,
        "allow_attachments": True,
        "from_messaging_channel": channel == "chat",
        "tags": random.sample(TAG_POOL, k=random.randint(1, 4)),
        "via": {
            "channel": channel,
            "source": {
                "from": {
                    "channel": channel,
                    "subject": subject,
                    "ticket_id": None,
                    "name": "End User" if channel != "api" else "Integration",
                    "address": "user@example.com" if channel == "email" else None,
                },
                "to": {"name": "IT Helpdesk", "address": "support@example.com"},
                "rel": None,
            },
        },
        "metric_set": {
            "agent_wait_time_in_minutes": {"business": random.randint(0, reply_b), "calendar": reply_c},
            "assigned_at": iso(assigned_at),
            "assignee_stations": random.randint(1, 4),
            "assignee_updated_at": iso(assigned_at),
            "first_resolution_time_in_minutes": {"business": fr_b, "calendar": fr_c},
            "full_resolution_time_in_minutes": {"business": full_b, "calendar": full_c},
            "group_stations": random.randint(1, 3),
            "initially_assigned_at": iso(assigned_at),
            "latest_comment_added_at": iso(latest_comment),
            "on_hold_time_in_minutes": {"business": onhold_b, "calendar": int(onhold_b*random.uniform(1,2))},
            "reopens": reopens,
            "replies": replies,
            "reply_time_in_minutes": {"business": reply_b, "calendar": reply_c},
            "requester_updated_at": iso(latest_comment),
            "requester_wait_time_in_minutes": {"business": random.randint(0, fr_b), "calendar": fr_c},
            "solved_at": solved_at,
            "status_updated_at": iso(latest_comment),
            "ticket_id": tid,
            "created_at": iso(created),
            "updated_at": iso(latest_comment),
            "url": f"https://example.zendesk.com/api/v2/ticket_metrics/{tid}.json",
        },
    })

with open("tickets_sample.json", "w", encoding="utf-8") as f:
    json.dump(tickets, f, indent=2)
with open("users_sample.json", "w", encoding="utf-8") as f:
    json.dump(users, f, indent=2)

print(f"Wrote tickets_sample.json ({len(tickets)} tickets) and users_sample.json ({len(users)} users).")
print(f"Agents: {len(agent_ids)} | End-users: {len(enduser_ids)} | Date span: 2019-01-01 to {NOW.date()}")

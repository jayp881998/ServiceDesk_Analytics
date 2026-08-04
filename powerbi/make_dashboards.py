"""Generate high-quality Power BI dashboard PNGs from synthetic sample data."""
import json, collections, statistics, math
from datetime import datetime, timezone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import numpy as np
from matplotlib.patches import FancyBboxPatch, Arc, Wedge
from matplotlib.lines import Line2D
import warnings
warnings.filterwarnings('ignore')

# ── palette ──────────────────────────────────────────────────────────────────
S = '#fcfcfb'        # surface
PAGE = '#f9f9f7'     # page
INK1 = '#0b0b0b'
INK2 = '#52514e'
MUTED = '#898781'
GRID = '#e1e0d9'
BASE = '#c3c2b7'

C1 = '#2a78d6'   # blue
C2 = '#eb6834'   # orange
C3 = '#1baf7a'   # aqua
C4 = '#eda100'   # yellow
C5 = '#e87ba4'   # magenta
C8 = '#e34948'   # red

GOOD = '#0ca30c'
WARN = '#fab219'
CRIT = '#d03b3b'
SERIOUS = '#ec835a'

# sequential blue steps
SEQ = ['#cde2fb','#9ec5f4','#6da7ec','#3987e5','#2a78d6','#256abf','#1c5cab']

matplotlib.rcParams.update({
    'font.family': ['Segoe UI', 'Arial', 'sans-serif'],
    'font.size': 10,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.spines.left': False,
    'axes.spines.bottom': False,
    'axes.facecolor': S,
    'figure.facecolor': S,
    'axes.grid': True,
    'grid.color': GRID,
    'grid.linewidth': 0.75,
    'grid.alpha': 1.0,
    'xtick.color': MUTED,
    'ytick.color': MUTED,
    'text.color': INK1,
    'axes.labelcolor': MUTED,
    'xtick.major.size': 0,
    'ytick.major.size': 0,
    'axes.axisbelow': True,
    'axes.titlepad': 10,
})

# ── load data ──────────────────────────────────────────────────────────────
import os, pathlib
BASE_DIR = pathlib.Path(__file__).parent.parent
with open(BASE_DIR / 'data_sample/tickets_sample.json') as f:
    tickets = json.load(f)
with open(BASE_DIR / 'data_sample/users_sample.json') as f:
    users = json.load(f)

agent_users = {u['id']: u['name'] for u in users if u['role'] in ('agent','admin')}

now_dt = datetime(2026, 8, 3, tzinfo=timezone.utc)

# ── derived stats ──────────────────────────────────────────────────────────
status_counts = collections.Counter(t['status'] for t in tickets)
priority_counts = collections.Counter(t['priority'] for t in tickets)
channel_counts = collections.Counter(t['via']['channel'] for t in tickets)
GNAMES = {101:'IT Helpdesk', 102:'Network Ops', 103:'App Support', 104:'AV/Classroom'}
group_counts = {GNAMES[k]: v for k, v in collections.Counter(t['group_id'] for t in tickets).items() if k in GNAMES}
year_counts = dict(sorted(collections.Counter(t['created_at'][:4] for t in tickets).items()))
monthly_counts = dict(sorted(collections.Counter(t['created_at'][:7] for t in tickets).items()))

open_tickets = [t for t in tickets if t['status'] in ('new','open','pending','hold')]
frt_hrs = [t['metric_set']['first_resolution_time_in_minutes']['calendar']/60 for t in tickets]
full_hrs = [t['metric_set']['full_resolution_time_in_minutes']['calendar']/60 for t in tickets]
reply_biz = [t['metric_set']['reply_time_in_minutes']['business'] for t in tickets]
reopens = [t['metric_set']['reopens'] for t in tickets]
replies_list = [t['metric_set']['replies'] for t in tickets]

# tiered SLA: urgent<=60m, high<=240m, normal<=480m, low<=1440m biz
def sla_ok(t):
    p = t['priority']
    thresholds = {'urgent':60,'high':240,'normal':480,'low':1440}
    th = thresholds.get(p, 480)
    return t['metric_set']['reply_time_in_minutes']['business'] <= th

sla_pass = sum(1 for t in tickets if sla_ok(t))
sla_pct = round(sla_pass / len(tickets) * 100, 1)

reopen_rate = round(sum(1 for r in reopens if r > 0) / len(tickets) * 100, 1)
med_frt = round(statistics.median(frt_hrs), 1)
med_full = round(statistics.median(full_hrs), 1)

# per-agent
agent_data = {}
agent_tickets_map = collections.defaultdict(list)
for t in tickets:
    if t['assignee_id'] in agent_users:
        agent_tickets_map[t['assignee_id']].append(t)

for uid, tlist in agent_tickets_map.items():
    name = agent_users[uid]
    parts = name.split()
    short = f"{parts[0]} {parts[-1][0]}."
    frt = [t['metric_set']['first_resolution_time_in_minutes']['calendar']/60 for t in tlist]
    rr = round(sum(1 for t in tlist if t['metric_set']['reopens']>0)/len(tlist)*100, 1)
    agent_data[uid] = {
        'name': short,
        'full_name': name,
        'count': len(tlist),
        'med_frt': round(statistics.median(frt), 1),
        'reopen_rate': rr,
    }

agents_sorted = sorted(agent_data.values(), key=lambda x: -x['count'])

# backlog aging
aging = {'0–7d':0,'8–30d':0,'31–90d':0,'90d+':0}
for t in open_tickets:
    created = datetime.fromisoformat(t['created_at'].replace('Z','+00:00'))
    age = (now_dt - created).days
    if age <= 7: aging['0–7d'] += 1
    elif age <= 30: aging['8–30d'] += 1
    elif age <= 90: aging['31–90d'] += 1
    else: aging['90d+'] += 1

# SLA by priority
sla_by_priority = {}
for p in ['urgent','high','normal','low']:
    pt = [t for t in tickets if t['priority']==p]
    ok = sum(1 for t in pt if sla_ok(t))
    sla_by_priority[p] = round(ok/len(pt)*100,1) if pt else 0

# top tags
all_tags = []
for t in tickets:
    all_tags.extend(t.get('tags',[]))
top_tags = collections.Counter(all_tags).most_common(8)


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def stat_tile(ax, value, label, color=INK1, prefix='', suffix=''):
    ax.set_facecolor(S)
    ax.set_xlim(0,1); ax.set_ylim(0,1)
    ax.axis('off')
    # light card border
    for spine in ax.spines.values():
        spine.set_visible(False)
    rect = FancyBboxPatch((0.04,0.04), 0.92, 0.92,
        boxstyle='round,pad=0.02', linewidth=1,
        edgecolor=GRID, facecolor='white')
    ax.add_patch(rect)
    val_str = f"{prefix}{value}{suffix}"
    ax.text(0.5, 0.58, val_str, ha='center', va='center',
            fontsize=28, fontweight='bold', color=color, transform=ax.transAxes)
    ax.text(0.5, 0.22, label, ha='center', va='center',
            fontsize=9.5, color=INK2, transform=ax.transAxes)

def style_ax(ax, title='', xlabel='', ylabel='', grid_axis='y'):
    ax.set_title(title, fontsize=11, fontweight='semibold', color=INK1, loc='left', pad=8)
    ax.set_xlabel(xlabel, fontsize=9, color=MUTED)
    ax.set_ylabel(ylabel, fontsize=9, color=MUTED)
    ax.tick_params(colors=MUTED, labelsize=8.5)
    ax.grid(True, axis=grid_axis, color=GRID, linewidth=0.75, alpha=1.0)
    ax.grid(False, axis='x' if grid_axis=='y' else 'y')
    ax.set_facecolor(S)
    for spine in ax.spines.values():
        spine.set_visible(False)

def bar_label(ax, bars, fmt='{:.0f}', color=INK2, fontsize=8.5, pad=3):
    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width()/2, h + pad,
                    fmt.format(h), ha='center', va='bottom',
                    fontsize=fontsize, color=color)

def hbar_label(ax, bars, fmt='{:.0f}', color=INK2, fontsize=8.5, pad=2):
    for bar in bars:
        w = bar.get_width()
        ax.text(w + pad, bar.get_y() + bar.get_height()/2,
                fmt.format(w), ha='left', va='center',
                fontsize=fontsize, color=color)

def footer(fig, text):
    fig.text(0.99, 0.012, text, ha='right', va='bottom',
             fontsize=7.5, color=MUTED, style='italic')


# ══════════════════════════════════════════════════════════════════
# 1. EXECUTIVE OVERVIEW
# ══════════════════════════════════════════════════════════════════
def make_executive():
    fig = plt.figure(figsize=(16, 10), facecolor=S)
    fig.subplots_adjust(left=0.05, right=0.97, top=0.90, bottom=0.07,
                        hspace=0.52, wspace=0.35)

    # header
    fig.text(0.05, 0.955, 'Executive Overview', fontsize=22,
             fontweight='bold', color=INK1, va='top')
    fig.text(0.05, 0.925, 'Helpdesk performance at a glance', fontsize=11,
             color=INK2, va='top')
    fig.text(0.97, 0.955, 'IT Support Analytics  ·  Zendesk → SQL Server → Power BI',
             fontsize=9, color=MUTED, ha='right', va='top')

    gs = fig.add_gridspec(3, 4, height_ratios=[1, 2.2, 2.2])

    # ── KPI row ──
    ax_k1 = fig.add_subplot(gs[0, 0])
    ax_k2 = fig.add_subplot(gs[0, 1])
    ax_k3 = fig.add_subplot(gs[0, 2])
    ax_k4 = fig.add_subplot(gs[0, 3])
    stat_tile(ax_k1, '800', 'Total Tickets', color=INK1)
    stat_tile(ax_k2, f'{sla_pct}%', 'SLA Compliance (FRT)', color=GOOD)
    stat_tile(ax_k3, '207', 'Open Backlog', color=WARN)
    stat_tile(ax_k4, f'{reopen_rate}%', 'Reopen Rate', color=CRIT)

    # ── Ticket Volume by Year ──
    ax_yr = fig.add_subplot(gs[1, :2])
    yrs = list(year_counts.keys())
    vals = list(year_counts.values())
    ax_yr.fill_between(yrs, vals, alpha=0.10, color=C1)
    ax_yr.plot(yrs, vals, color=C1, linewidth=2, marker='o',
               markersize=6, markerfacecolor=C1,
               markeredgecolor=S, markeredgewidth=2, solid_capstyle='round')
    style_ax(ax_yr, title='Ticket Volume by Year', xlabel='', ylabel='Tickets')
    ax_yr.set_xticks(yrs)
    ax_yr.set_xticklabels(yrs, rotation=0, fontsize=8.5)
    ax_yr.set_ylim(0, max(vals) * 1.25)
    # label min/max
    peak_i = vals.index(max(vals))
    ax_yr.text(yrs[peak_i], vals[peak_i]+4, str(vals[peak_i]),
               ha='center', fontsize=8, color=C1, fontweight='semibold')

    # ── Status Mix donut ──
    ax_st = fig.add_subplot(gs[1, 2])
    st_order = ['closed','solved','pending','open','hold','new']
    st_colors = [C3, '#4db89a', C4, C1, MUTED, C2]
    st_labels_clean = ['Closed','Solved','Pending','Open','Hold','New']
    st_vals = [status_counts.get(s, 0) for s in st_order]
    wedges, _ = ax_st.pie(st_vals, colors=st_colors, startangle=90,
                          wedgeprops={'width':0.55, 'linewidth':2, 'edgecolor':S})
    ax_st.set_title('Status Mix', fontsize=11, fontweight='semibold',
                    color=INK1, loc='left', pad=8)
    ax_st.legend(wedges, [f'{l} ({v})' for l,v in zip(st_labels_clean,st_vals)],
                 loc='lower center', bbox_to_anchor=(0.5,-0.22), ncol=2,
                 fontsize=7.5, frameon=False, labelcolor=INK2,
                 handlelength=1.2, handleheight=0.8)

    # ── Channel Mix horizontal bar ──
    ax_ch = fig.add_subplot(gs[1, 3])
    ch_order = sorted(channel_counts.items(), key=lambda x: x[1])
    ch_names = [x[0].title() for x in ch_order]
    ch_vals = [x[1] for x in ch_order]
    bars = ax_ch.barh(ch_names, ch_vals, color=C1, height=0.55,
                      linewidth=0)
    hbar_label(ax_ch, bars, fontsize=8.5)
    style_ax(ax_ch, title='Channel Mix', grid_axis='x')
    ax_ch.set_xlim(0, max(ch_vals)*1.25)
    ax_ch.invert_yaxis()

    # ── Tickets by Priority ──
    ax_pri = fig.add_subplot(gs[2, :2])
    pri_order = ['low','normal','high','urgent']
    pri_colors = [MUTED, C1, C4, CRIT]
    pri_vals = [priority_counts.get(p, 0) for p in pri_order]
    pri_labels = [p.capitalize() for p in pri_order]
    bars = ax_pri.bar(pri_labels, pri_vals, color=pri_colors,
                      width=0.55, linewidth=0)
    bar_label(ax_pri, bars, fontsize=8.5)
    style_ax(ax_pri, title='Tickets by Priority')
    ax_pri.set_ylim(0, max(pri_vals)*1.2)

    # ── Tickets by Group ──
    ax_grp = fig.add_subplot(gs[2, 2:])
    grp_order = ['IT Helpdesk','Network Ops','App Support','AV/Classroom']
    grp_vals = [group_counts.get(g, 0) for g in grp_order]
    grp_labels = ['IT Helpdesk','Network Ops','App Support','AV / Classroom']
    bars = ax_grp.bar(grp_labels, grp_vals, color=C3, width=0.55, linewidth=0)
    bar_label(ax_grp, bars, fontsize=8.5)
    style_ax(ax_grp, title='Tickets by Group')
    ax_grp.set_ylim(0, max(grp_vals)*1.2)
    ax_grp.tick_params(axis='x', labelsize=8)

    footer(fig, 'Built on synthetic sample data (800 tickets, 2019–2026). Not real data.')
    fig.savefig(pathlib.Path(__file__).parent / 'dash_executive.png',
                dpi=180, bbox_inches='tight', facecolor=S)
    plt.close(fig)
    print('OK dash_executive.png')


# ══════════════════════════════════════════════════════════════════
# 2. OPERATIONS CONTROL
# ══════════════════════════════════════════════════════════════════
def make_operations():
    fig = plt.figure(figsize=(16, 10), facecolor=S)
    fig.subplots_adjust(left=0.05, right=0.97, top=0.90, bottom=0.07,
                        hspace=0.58, wspace=0.38)

    fig.text(0.05, 0.955, 'Operations Control', fontsize=22,
             fontweight='bold', color=INK1, va='top')
    fig.text(0.05, 0.925, 'Response, resolution & backlog health', fontsize=11,
             color=INK2, va='top')
    fig.text(0.97, 0.955, 'IT Support Analytics  ·  Zendesk → SQL Server → Power BI',
             fontsize=9, color=MUTED, ha='right', va='top')

    gs = fig.add_gridspec(3, 4, height_ratios=[1, 2.4, 2.2])

    ax_k1 = fig.add_subplot(gs[0, 0])
    ax_k2 = fig.add_subplot(gs[0, 1])
    ax_k3 = fig.add_subplot(gs[0, 2])
    ax_k4 = fig.add_subplot(gs[0, 3])
    stat_tile(ax_k1, f'{med_frt}h', 'Median First Resolution', color=C1)
    stat_tile(ax_k2, f'{med_full}h', 'Median Full Resolution', color=INK1)
    stat_tile(ax_k3, '207', 'Open Backlog', color=WARN)
    stat_tile(ax_k4, f'{sla_pct}%', 'SLA Compliance', color=GOOD)

    # ── Monthly volume (full span) ──
    ax_mon = fig.add_subplot(gs[1, :])
    mon_keys = list(monthly_counts.keys())
    mon_vals = list(monthly_counts.values())
    x_idx = list(range(len(mon_keys)))
    ax_mon.fill_between(x_idx, mon_vals, alpha=0.10, color=C1)
    ax_mon.plot(x_idx, mon_vals, color=C1, linewidth=1.75,
                solid_capstyle='round', solid_joinstyle='round')
    # year boundary labels
    year_starts = {}
    for i, k in enumerate(mon_keys):
        yr = k[:4]
        if yr not in year_starts:
            year_starts[yr] = i
    ax_mon.set_xticks([year_starts[y] for y in year_starts])
    ax_mon.set_xticklabels(list(year_starts.keys()), fontsize=8.5)
    ax_mon.set_xlim(0, len(mon_keys)-1)
    style_ax(ax_mon, title='Monthly Ticket Volume (2019–2026)',
             ylabel='Tickets / month')
    ax_mon.set_ylim(0, max(mon_vals)*1.35)

    # ── FRT histogram ──
    ax_frt = fig.add_subplot(gs[2, 0])
    bins_frt = np.arange(0, 22, 2)
    counts_frt, edges_frt = np.histogram(frt_hrs, bins=bins_frt)
    ax_frt.bar(edges_frt[:-1], counts_frt, width=1.7, color=C1,
               linewidth=0, align='edge')
    ax_frt.axvline(med_frt, color=CRIT, linewidth=1.25, linestyle='--')
    ax_frt.text(med_frt+0.3, max(counts_frt)*0.85, f'Median\n{med_frt}h',
                fontsize=7.5, color=CRIT)
    style_ax(ax_frt, title='First Resolution (hrs)', xlabel='hours')
    ax_frt.set_xlim(0, 21)

    # ── Full resolution histogram ──
    ax_full = fig.add_subplot(gs[2, 1])
    bins_full = np.arange(0, 46, 3)
    counts_full, edges_full = np.histogram(full_hrs, bins=bins_full)
    ax_full.bar(edges_full[:-1], counts_full, width=2.7, color=C1,
                linewidth=0, align='edge')
    ax_full.axvline(med_full, color=CRIT, linewidth=1.25, linestyle='--')
    ax_full.text(med_full+0.5, max(counts_full)*0.85, f'Median\n{med_full}h',
                 fontsize=7.5, color=CRIT)
    style_ax(ax_full, title='Full Resolution (hrs)', xlabel='hours')
    ax_full.set_xlim(0, 45)

    # ── Backlog Aging ──
    ax_age = fig.add_subplot(gs[2, 2])
    age_labels = list(aging.keys())
    age_vals = list(aging.values())
    age_colors = [GOOD, C4, SERIOUS, CRIT]
    bars = ax_age.bar(age_labels, age_vals, color=age_colors, width=0.55, linewidth=0)
    bar_label(ax_age, bars, fontsize=8.5)
    style_ax(ax_age, title='Backlog Aging')
    ax_age.set_ylim(0, max(age_vals)*1.22)

    # ── SLA % by Priority ──
    ax_sla = fig.add_subplot(gs[2, 3])
    sla_labels = ['Urgent','High','Normal','Low']
    sla_vals_list = [sla_by_priority[p] for p in ['urgent','high','normal','low']]
    sla_colors = [CRIT, SERIOUS, C1, MUTED]
    bars = ax_sla.bar(sla_labels, sla_vals_list, color=sla_colors,
                      width=0.55, linewidth=0)
    bar_label(ax_sla, bars, fmt='{:.0f}%', fontsize=8.5)
    style_ax(ax_sla, title='SLA % by Priority')
    ax_sla.set_ylim(0, 115)
    ax_sla.axhline(100, color=GRID, linewidth=0.75)

    footer(fig, 'Built on synthetic sample data (800 tickets, 2019–2026). Not real data.')
    fig.savefig(pathlib.Path(__file__).parent / 'dash_operations.png',
                dpi=180, bbox_inches='tight', facecolor=S)
    plt.close(fig)
    print('OK dash_operations.png')


# ══════════════════════════════════════════════════════════════════
# 3. AGENT PERFORMANCE
# ══════════════════════════════════════════════════════════════════
def make_agent():
    fig = plt.figure(figsize=(16, 10), facecolor=S)
    fig.subplots_adjust(left=0.05, right=0.97, top=0.90, bottom=0.07,
                        hspace=0.52, wspace=0.40)

    fig.text(0.05, 0.955, 'Agent Performance', fontsize=22,
             fontweight='bold', color=INK1, va='top')
    fig.text(0.05, 0.925, 'Workload, responsiveness & quality by agent', fontsize=11,
             color=INK2, va='top')
    fig.text(0.97, 0.955, 'IT Support Analytics  ·  Zendesk → SQL Server → Power BI',
             fontsize=9, color=MUTED, ha='right', va='top')

    gs = fig.add_gridspec(3, 4, height_ratios=[1, 2.2, 2.2])

    avg_tickets = round(sum(a['count'] for a in agents_sorted) / len(agents_sorted))
    med_replies = statistics.median(replies_list)

    ax_k1 = fig.add_subplot(gs[0, 0])
    ax_k2 = fig.add_subplot(gs[0, 1])
    ax_k3 = fig.add_subplot(gs[0, 2])
    ax_k4 = fig.add_subplot(gs[0, 3])
    stat_tile(ax_k1, str(len(agents_sorted)), 'Active Agents', color=C1)
    stat_tile(ax_k2, str(avg_tickets), 'Avg Tickets / Agent', color=INK1)
    stat_tile(ax_k3, str(int(med_replies)), 'Median Replies / Ticket', color=C4)
    stat_tile(ax_k4, f'{reopen_rate}%', 'Reopen Rate', color=CRIT)

    names = [a['name'] for a in agents_sorted]
    counts = [a['count'] for a in agents_sorted]
    med_frts = [a['med_frt'] for a in agents_sorted]
    rrs = [a['reopen_rate'] for a in agents_sorted]
    names_rev = names[::-1]
    counts_rev = counts[::-1]
    med_frts_rev = med_frts[::-1]
    rrs_rev = rrs[::-1]

    # ── Tickets Handled ──
    ax_cnt = fig.add_subplot(gs[1, :2])
    bars = ax_cnt.barh(names_rev, counts_rev, color=C1, height=0.55, linewidth=0)
    hbar_label(ax_cnt, bars, fontsize=8.5)
    style_ax(ax_cnt, title='Tickets Handled', grid_axis='x')
    ax_cnt.set_xlim(0, max(counts)*1.22)
    ax_cnt.tick_params(axis='y', labelsize=9)

    # ── Median FRT by Agent ──
    ax_frt_a = fig.add_subplot(gs[1, 2:])
    bars = ax_frt_a.barh(names_rev, med_frts_rev, color=C1, height=0.55, linewidth=0)
    hbar_label(ax_frt_a, bars, fmt='{:.1f}h', fontsize=8.5)
    style_ax(ax_frt_a, title='Median First Resolution (hrs)', grid_axis='x')
    ax_frt_a.set_xlim(0, max(med_frts)*1.25)
    ax_frt_a.tick_params(axis='y', labelsize=9)

    # ── Reopen Rate by Agent ──
    ax_rr = fig.add_subplot(gs[2, :2])
    rr_colors = [CRIT if r > 35 else SERIOUS if r > 28 else C1 for r in rrs_rev]
    bars = ax_rr.barh(names_rev, rrs_rev, color=rr_colors, height=0.55, linewidth=0)
    hbar_label(ax_rr, bars, fmt='{:.1f}%', fontsize=8.5)
    ax_rr.axvline(reopen_rate, color=MUTED, linewidth=1, linestyle='--')
    ax_rr.text(reopen_rate+0.3, -0.6, f'Avg {reopen_rate}%', fontsize=7.5, color=MUTED)
    style_ax(ax_rr, title='Reopen Rate by Agent (%)', grid_axis='x')
    ax_rr.set_xlim(0, max(rrs)*1.25)
    ax_rr.tick_params(axis='y', labelsize=9)

    # ── Replies per Ticket histogram ──
    ax_rep = fig.add_subplot(gs[2, 2:])
    rep_counts = collections.Counter(replies_list)
    rep_keys = sorted(rep_counts.keys())
    rep_vals_hist = [rep_counts[k] for k in rep_keys]
    ax_rep.bar(rep_keys, rep_vals_hist, color=C3, width=0.7, linewidth=0)
    ax_rep.axvline(med_replies, color=CRIT, linewidth=1.25, linestyle='--')
    ax_rep.text(med_replies+0.15, max(rep_vals_hist)*0.9,
                f'Median {int(med_replies)}', fontsize=7.5, color=CRIT)
    style_ax(ax_rep, title='Replies per Ticket Distribution', xlabel='replies')
    ax_rep.set_xticks(rep_keys)
    ax_rep.set_xlim(min(rep_keys)-0.5, max(rep_keys)+0.5)

    footer(fig, 'Built on synthetic sample data (800 tickets, 2019–2026). Not real data.')
    fig.savefig(pathlib.Path(__file__).parent / 'dash_agent.png',
                dpi=180, bbox_inches='tight', facecolor=S)
    plt.close(fig)
    print('OK dash_agent.png')


# ══════════════════════════════════════════════════════════════════
# 4. STAR SCHEMA DIAGRAM
# ══════════════════════════════════════════════════════════════════
def make_star_schema():
    fig, ax = plt.subplots(figsize=(14, 9), facecolor=S)
    ax.set_facecolor(S)
    ax.set_xlim(0, 14); ax.set_ylim(0, 9)
    ax.axis('off')
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    HEADER_ALPHA = 0.92

    def draw_table(ax, x, y, w, h, title, rows, header_color, title_color='white',
                   pk_rows=None, fk_rows=None):
        """Draw a table box with header + rows."""
        row_h = 0.32
        box_h = 0.52 + len(rows) * row_h
        # shadow
        shadow = FancyBboxPatch((x+0.06, y-box_h-0.06), w, box_h,
            boxstyle='round,pad=0.06', facecolor='#d0cfc8', edgecolor='none', zorder=1)
        ax.add_patch(shadow)
        # body
        body = FancyBboxPatch((x, y-box_h), w, box_h,
            boxstyle='round,pad=0.06', facecolor='white',
            edgecolor='#d0cfc8', linewidth=1, zorder=2)
        ax.add_patch(body)
        # header
        header = FancyBboxPatch((x, y-0.52), w, 0.52,
            boxstyle='round,pad=0.06', facecolor=header_color, edgecolor='none',
            alpha=HEADER_ALPHA, zorder=3)
        ax.add_patch(header)
        # title
        ax.text(x + w/2, y - 0.26, title, ha='center', va='center',
                fontsize=10.5, fontweight='bold', color=title_color, zorder=4)
        # rows
        for i, row in enumerate(rows):
            ry = y - 0.52 - (i+0.5)*row_h
            # row separator (except last)
            if i < len(rows)-1:
                ax.plot([x+0.12, x+w-0.12], [y-0.52-(i+1)*row_h, y-0.52-(i+1)*row_h],
                        color=GRID, linewidth=0.6, zorder=3)
            badge = None
            label = row
            if row.startswith('PK '):
                badge = 'PK'; label = row[3:]
            elif row.startswith('FK '):
                badge = 'FK'; label = row[3:]
            if badge:
                bx = x + 0.16
                bc = '#e8a800' if badge=='PK' else '#6090d0'
                b_rect = FancyBboxPatch((bx-0.01, ry-0.1), 0.28, 0.22,
                    boxstyle='round,pad=0.03', facecolor=bc, edgecolor='none',
                    alpha=0.9, zorder=4)
                ax.add_patch(b_rect)
                ax.text(bx+0.13, ry+0.01, badge, ha='center', va='center',
                        fontsize=6, fontweight='bold', color='white', zorder=5)
                ax.text(bx+0.38, ry+0.01, label, ha='left', va='center',
                        fontsize=8.5, color=INK2, zorder=4)
            else:
                ax.text(x+0.18, ry+0.01, label, ha='left', va='center',
                        fontsize=8.5, color=INK2, zorder=4)

    def arrow(ax, x1, y1, x2, y2, label1='1', label2='*'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=BASE,
                                   lw=1.5, connectionstyle='arc3,rad=0.0'),
                    zorder=1)
        # cardinality labels
        dx = x2-x1; dy = y2-y1
        dist = math.sqrt(dx**2+dy**2)
        ux, uy = dx/dist, dy/dist
        off = 0.25
        ax.text(x1+ux*off, y1+uy*off, label1, ha='center', va='center',
                fontsize=9, color=MUTED, fontweight='bold', zorder=5)
        ax.text(x2-ux*off, y2-uy*off, label2, ha='center', va='center',
                fontsize=9, color=MUTED, fontweight='bold', zorder=5)

    # ── center: Tickets (FACT) ──
    draw_table(ax, 4.9, 7.1, 3.0, 0, 'Tickets  (FACT)',
               ['PK Id', 'FK Requester Id', 'FK Assignee Id',
                'FK Group Id', 'FK Created At (date)',
                'Status  ·  Priority  ·  Type',
                'Subject  ·  Brand Id'],
               header_color='#1e3a5f', title_color='white')

    # ── Dim_Date ──
    draw_table(ax, 0.4, 8.8, 2.8, 0, 'Dim_Date',
               ['PK Date', 'Year  ·  Quarter  ·  Month',
                'Week  ·  Day  ·  Hour'],
               header_color='#7a4a14', title_color='white')

    # ── Dim_User Requester ──
    draw_table(ax, 0.4, 6.0, 2.8, 0, 'Dim_User  (Requester)',
               ['PK Id', 'Name  ·  Email  ·  Role',
                'Active  ·  Last Login'],
               header_color='#4a2f7a', title_color='white')

    # ── Dim_User Agent ──
    draw_table(ax, 0.4, 3.65, 2.8, 0, 'Dim_User  (Agent)',
               ['PK Id', 'Name  ·  Role (agent/admin)'],
               header_color='#4a2f7a', title_color='white')

    # ── Dim_Group ──
    draw_table(ax, 0.4, 1.65, 2.8, 0, 'Dim_Group',
               ['PK Group Id', 'Group Name'],
               header_color='#7a1a2a', title_color='white')

    # ── Ticket_Metrics ──
    draw_table(ax, 9.7, 8.6, 3.7, 0, 'Ticket_Metrics',
               ['FK Ticket Id', 'First Resolution Time',
                'Full Resolution Time',
                'Reply / Wait Times',
                'Reopens  ·  Replies',
                'Solved At'],
               header_color='#1a5a3a', title_color='white')

    # ── Via (Channel) ──
    draw_table(ax, 9.7, 5.4, 3.7, 0, 'Via  (Channel)',
               ['PK Ticket Id', 'Channel  ·  Source'],
               header_color='#1a4a5a', title_color='white')

    # ── Tags (bridge) ──
    draw_table(ax, 9.7, 3.0, 3.7, 0, 'Tags  (bridge)',
               ['FK TicketID', 'Tag'],
               header_color='#5a4a1a', title_color='white')

    # ── arrows ──
    # Dim_Date → Tickets
    arrow(ax, 3.25, 7.95, 4.92, 6.78, '1', '*')
    # Requester → Tickets
    arrow(ax, 3.25, 5.35, 4.92, 6.35, '1', '*')
    # Agent → Tickets
    arrow(ax, 3.25, 3.2, 4.92, 6.10, '1', '*')
    # Group → Tickets
    arrow(ax, 3.25, 1.17, 4.92, 5.95, '1', '*')
    # Tickets → Metrics
    arrow(ax, 7.92, 6.78, 9.72, 7.98, '1', '1')
    # Tickets → Via
    arrow(ax, 7.92, 6.55, 9.72, 4.96, '1', '1')
    # Tickets → Tags
    arrow(ax, 7.92, 6.32, 9.72, 2.60, '1', '*')

    # title
    ax.text(7.0, 8.75, 'Star Schema — IT Support Analytics',
            ha='center', va='top', fontsize=15, fontweight='bold', color=INK1)
    ax.text(7.0, 8.42, 'Zendesk → SQL Server (zendesklog) → Power BI',
            ha='center', va='top', fontsize=9, color=MUTED)

    fig.savefig(pathlib.Path(__file__).parent / 'model_star_schema.png',
                dpi=180, bbox_inches='tight', facecolor=S)
    plt.close(fig)
    print('OK model_star_schema.png')


if __name__ == '__main__':
    make_star_schema()
    make_executive()
    make_operations()
    make_agent()
    print('All done.')

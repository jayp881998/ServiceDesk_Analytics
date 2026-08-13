import json, statistics
from collections import Counter, defaultdict
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import os
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","data_sample")+os.sep
tk=json.load(open(D+"tickets_sample.json"))
us=json.load(open(D+"users_sample.json"))
uname={u['id']:u['name'] for u in us}
GROUPS={101:"IT Helpdesk",102:"Network Ops",103:"App Support",104:"AV / Classroom"}

# palette
NAVY="#1F3B57"; ACC="#2E86C1"; GRN="#2E8B6F"; AMB="#E1A730"; RED="#C0504D"; GREY="#7F8C9A"
plt.rcParams.update({"font.family":"DejaVu Sans","axes.edgecolor":"#D5DCE3",
  "axes.grid":True,"grid.color":"#EBEFF3","axes.axisbelow":True,"axes.titleweight":"bold",
  "axes.titlecolor":NAVY,"text.color":"#33414F","axes.labelcolor":"#33414F",
  "xtick.color":"#5B6B7B","ytick.color":"#5B6B7B"})

def kpi(ax,val,label,color=NAVY):
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0,0),1,1,transform=ax.transAxes,facecolor="#F4F7FA",edgecolor="#E1E7ED",lw=1))
    ax.text(0.5,0.60,val,ha="center",va="center",fontsize=26,fontweight="bold",color=color,transform=ax.transAxes)
    ax.text(0.5,0.24,label,ha="center",va="center",fontsize=10.5,color="#5B6B7B",transform=ax.transAxes)

def header(fig,title,sub):
    fig.text(0.035,0.955,title,fontsize=21,fontweight="bold",color=NAVY)
    fig.text(0.035,0.925,sub,fontsize=11,color=GREY)
    fig.text(0.965,0.955,"IT Support Analytics  ·  Zendesk → SQL Server → Power BI",
             fontsize=9.5,color=GREY,ha="right")
    fig.text(0.965,0.017,"Built on synthetic sample data (800 tickets, 2019–2026). Not real Michener data.",
             fontsize=8.5,color="#9AA7B3",ha="right",style="italic")

# ---------- shared calcs ----------
byym=Counter(t['created_at'][:7] for t in tk)
months=sorted(byym)
status=Counter(t['status'] for t in tk)
chan=Counter(t['via']['channel'] for t in tk)
prio=Counter(str(t['priority']) for t in tk)
frt=[t['metric_set']['first_resolution_time_in_minutes']['business'] for t in tk]
ttr=[t['metric_set']['full_resolution_time_in_minutes']['business'] for t in tk]
backlog=sum(1 for t in tk if t['status'] not in('solved','closed'))
reopened=sum(1 for t in tk if (t['metric_set']['reopens'] or 0)>0)
tgt={'urgent':60,'high':240,'normal':480,'low':960,'None':480,None:480}
met=sum(1 for t in tk if t['metric_set']['first_resolution_time_in_minutes']['business']<=tgt.get(t['priority'],480))
sla=100*met/len(tk)

# =================== 1. EXECUTIVE OVERVIEW ===================
fig=plt.figure(figsize=(13,7.3),dpi=140); fig.patch.set_facecolor("white")
gs=GridSpec(3,4,figure=fig,left=0.05,right=0.965,top=0.87,bottom=0.07,hspace=0.55,wspace=0.28,height_ratios=[0.8,1.25,1.25])
header(fig,"Executive Overview","Helpdesk performance at a glance")
for i,(v,l,c) in enumerate([(f"{len(tk):,}","Total Tickets",NAVY),(f"{sla:.0f}%","SLA Compliance (FRT)",GRN),
      (f"{backlog}","Open Backlog",AMB),(f"{100*reopened/len(tk):.0f}%","Reopen Rate",RED)]):
    kpi(fig.add_subplot(gs[0,i]),v,l,c)
# volume trend by year
ax=fig.add_subplot(gs[1,:2]); byyear=Counter(t['created_at'][:4] for t in tk)
yy=sorted(byyear); ax.plot(yy,[byyear[y] for y in yy],marker="o",color=ACC,lw=2.4)
ax.fill_between(yy,[byyear[y] for y in yy],color=ACC,alpha=0.12); ax.set_title("Ticket Volume by Year"); ax.set_ylim(0)
# status donut
ax=fig.add_subplot(gs[1,2]); order=['new','open','pending','hold','solved','closed']
cols={'new':ACC,'open':AMB,'pending':"#C99A2E",'hold':GREY,'solved':GRN,'closed':"#1F6E57"}
ax.pie([status[s] for s in order],colors=[cols[s] for s in order],startangle=90,
       wedgeprops=dict(width=0.42,edgecolor="white")); ax.set_title("Status Mix")
ax.legend(order,loc="center",fontsize=7,frameon=False,ncol=2,bbox_to_anchor=(0.5,-0.18))
# channel bar
ax=fig.add_subplot(gs[1,3]); ch=chan.most_common()
ax.barh([c[0] for c in ch][::-1],[c[1] for c in ch][::-1],color=NAVY); ax.set_title("Channel Mix"); ax.grid(axis="y")
# priority bar
ax=fig.add_subplot(gs[2,:2]); po=['low','normal','high','urgent','None']
ax.bar(po,[prio[p] for p in po],color=[GREY,ACC,AMB,RED,"#CBD3DB"]); ax.set_title("Tickets by Priority")
# group volume
ax=fig.add_subplot(gs[2,2:]); g=Counter(t['group_id'] for t in tk)
gk=sorted(g); ax.bar([GROUPS[k] for k in gk],[g[k] for k in gk],color=GRN); ax.set_title("Tickets by Group"); ax.tick_params(axis='x',labelsize=8)
plt.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)),"dash_executive.png"),facecolor="white"); plt.close()

# =================== 2. OPERATIONS CONTROL ===================
fig=plt.figure(figsize=(13,7.3),dpi=140); fig.patch.set_facecolor("white")
gs=GridSpec(3,4,figure=fig,left=0.05,right=0.965,top=0.87,bottom=0.07,hspace=0.55,wspace=0.28,height_ratios=[0.8,1.25,1.25])
header(fig,"Operations Control","Response, resolution & backlog health")
for i,(v,l,c) in enumerate([(f"{statistics.median(frt)/60:.1f}h","Median First Resolution",ACC),
      (f"{statistics.median(ttr)/60:.1f}h","Median Full Resolution",NAVY),
      (f"{backlog}","Open Backlog",AMB),(f"{sla:.0f}%","SLA Compliance",GRN)]):
    kpi(fig.add_subplot(gs[0,i]),v,l,c)
# monthly volume trend (full)
ax=fig.add_subplot(gs[1,:]); ax.plot(months,[byym[m] for m in months],color=ACC,lw=1.6)
ax.fill_between(months,[byym[m] for m in months],color=ACC,alpha=0.10)
ax.set_title("Monthly Ticket Volume (2019–2026)")
step=max(1,len(months)//12); ax.set_xticks(months[::step]); ax.tick_params(axis='x',rotation=45,labelsize=7); ax.set_ylim(0)
# FRT distribution
ax=fig.add_subplot(gs[2,0]); ax.hist([f/60 for f in frt],bins=20,color=ACC,edgecolor="white"); ax.set_title("First Resolution (hrs)"); ax.set_xlabel("hours")
# TTR distribution
ax=fig.add_subplot(gs[2,1]); ax.hist([t/60 for t in ttr],bins=20,color=NAVY,edgecolor="white"); ax.set_title("Full Resolution (hrs)"); ax.set_xlabel("hours")
# backlog aging buckets (open tickets by age)
now=datetime(2026,8,1)
ages=[(now-datetime.strptime(t['created_at'],"%Y-%m-%dT%H:%M:%SZ")).days for t in tk if t['status'] not in('solved','closed')]
buck=Counter()
for a in ages:
    buck['0–7d' if a<=7 else '8–30d' if a<=30 else '31–90d' if a<=90 else '90d+']+=1
bo=['0–7d','8–30d','31–90d','90d+']
ax=fig.add_subplot(gs[2,2]); ax.bar(bo,[buck[b] for b in bo],color=[GRN,AMB,"#D9822B",RED]); ax.set_title("Backlog Aging"); ax.tick_params(axis='x',labelsize=8)
# SLA by priority
ax=fig.add_subplot(gs[2,3])
pl=['urgent','high','normal','low']
comp=[]
for p in pl:
    sub=[t for t in tk if t['priority']==p]
    m=sum(1 for t in sub if t['metric_set']['first_resolution_time_in_minutes']['business']<=tgt[p])
    comp.append(100*m/len(sub) if sub else 0)
ax.bar(pl,comp,color=[RED,AMB,ACC,GREY]); ax.set_title("SLA % by Priority"); ax.set_ylim(0,100); ax.tick_params(axis='x',labelsize=8)
plt.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)),"dash_operations.png"),facecolor="white"); plt.close()

# =================== 3. AGENT PERFORMANCE ===================
fig=plt.figure(figsize=(13,7.3),dpi=140); fig.patch.set_facecolor("white")
gs=GridSpec(3,4,figure=fig,left=0.05,right=0.965,top=0.87,bottom=0.07,hspace=0.55,wspace=0.30,height_ratios=[0.8,1.3,1.3])
header(fig,"Agent Performance","Workload, responsiveness & quality by agent")
ag=Counter(t['assignee_id'] for t in tk if t['assignee_id'])
top=ag.most_common(7); names=[uname.get(a,str(a)).split()[0]+" "+uname.get(a,"").split()[-1][0]+"." for a,_ in top]
for i,(v,l,c) in enumerate([(f"{len(ag)}","Active Agents",NAVY),
      (f"{sum(ag.values())//max(1,len(ag))}","Avg Tickets / Agent",ACC),
      (f"{statistics.median([t['metric_set']['replies'] for t in tk]):.0f}","Median Replies / Ticket",AMB),
      (f"{100*reopened/len(tk):.0f}%","Reopen Rate",RED)]):
    kpi(fig.add_subplot(gs[0,i]),v,l,c)
# tickets handled
ax=fig.add_subplot(gs[1,:2]); ax.barh(names[::-1],[c for _,c in top][::-1],color=NAVY); ax.set_title("Tickets Handled (Top Agents)")
# avg FRT per agent
ax=fig.add_subplot(gs[1,2:]); afrt=[]
for a,_ in top:
    vals=[t['metric_set']['first_resolution_time_in_minutes']['business'] for t in tk if t['assignee_id']==a]
    afrt.append(statistics.median(vals)/60)
ax.barh(names[::-1],afrt[::-1],color=ACC); ax.set_title("Median First Resolution by Agent (hrs)")
# reopen rate per agent
ax=fig.add_subplot(gs[2,:2]); aro=[]
for a,_ in top:
    sub=[t for t in tk if t['assignee_id']==a]
    r=sum(1 for t in sub if (t['metric_set']['reopens'] or 0)>0)
    aro.append(100*r/len(sub) if sub else 0)
ax.bar(names,aro,color=RED); ax.set_title("Reopen Rate by Agent (%)"); ax.tick_params(axis='x',rotation=25,labelsize=8)
# replies distribution
ax=fig.add_subplot(gs[2,2:]); ax.hist([t['metric_set']['replies'] for t in tk],bins=range(1,11),color=GRN,edgecolor="white",align='left')
ax.set_title("Replies per Ticket"); ax.set_xlabel("replies")
plt.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)),"dash_agent.png"),facecolor="white"); plt.close()
print("done")

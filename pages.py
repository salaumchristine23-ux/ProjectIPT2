BASE = """<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>GCAS · ICCT Colleges Cainta</title>
<link rel=preconnect href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel=stylesheet><style>
:root{--ink:#1b2733;--mut:#5b6b7a;--bg:#f3f5f8;--card:#fff;--line:#d8dee6;--navy:#12355b;--pri:#1f5fa8;--teal:#0f766e;--amber:#9a6700;--bad:#b42318;--r:8px}
@media(prefers-color-scheme:dark){:root{--ink:#e7edf3;--mut:#9aa9b8;--bg:#0f151c;--card:#17202a;--line:#2b3846;--navy:#0b2441;--pri:#5aa0ee;--teal:#34c0b1;--amber:#e3b341;--bad:#f97066}}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 Inter,'Segoe UI',system-ui,sans-serif;color:var(--ink);background:var(--bg)}
h1,h2{font-weight:600;letter-spacing:-.01em;line-height:1.25;margin:0 0 .6rem}h1{font-size:1.5rem}h2{font-size:1.15rem}
nav{background:var(--navy);color:#fff;padding:.75rem max(1rem,calc((100% - 1040px)/2));display:flex;gap:.25rem;align-items:center;flex-wrap:wrap;border-bottom:3px solid var(--teal)}
nav b{margin-right:auto;font-size:1.1rem;font-weight:700;color:#fff}nav b small{display:block;font-size:.75rem;font-weight:400;opacity:.8}
nav a{color:#fff;text-decoration:none;font-weight:500;padding:.4rem .8rem;border-radius:var(--r)}nav a:hover{background:rgba(255,255,255,.14)}nav form{margin:0 0 0 .5rem}
main{max-width:1040px;margin:1.4rem auto 3rem;padding:0 1rem}
section{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:1.25rem;margin-bottom:1.1rem;overflow-x:auto;box-shadow:0 1px 2px rgba(16,24,40,.05)}
section.hero{border-left:5px solid var(--pri)}.sub{color:var(--mut);margin:-.2rem 0 1rem}
table{border-collapse:collapse;width:100%}th{font-size:.82rem;font-weight:600;color:var(--mut);text-align:left;padding:.5rem;border-bottom:2px solid var(--line)}
td{padding:.65rem .5rem;border-bottom:1px solid var(--line);vertical-align:middle}tr:hover td{background:color-mix(in srgb,var(--pri) 5%,transparent)}
label{font-weight:500;font-size:.88rem;display:flex;flex-direction:column;gap:.25rem}
input,select,textarea{font:inherit;padding:.5rem .7rem;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--ink);max-width:100%}input:focus,select:focus{outline:2px solid var(--pri);border-color:var(--pri)}
button,.btn{font:600 .9rem Inter,system-ui,sans-serif;background:var(--pri);color:#fff;border:1px solid transparent;border-radius:6px;padding:.5rem 1rem;cursor:pointer;text-decoration:none;display:inline-block}
button:hover,.btn:hover{filter:brightness(1.1)}nav button{background:transparent;border-color:rgba(255,255,255,.5)}
button.x{background:transparent;color:var(--bad);border-color:var(--bad)}.btn{background:transparent;color:var(--pri);border-color:var(--pri)}
td form{display:inline-block;margin:.1rem}form.i{display:flex;gap:.7rem;flex-wrap:wrap;align-items:flex-end}
.f{background:color-mix(in srgb,var(--teal) 13%,var(--card));color:var(--ink);border:1px solid var(--teal);border-left-width:5px;border-radius:var(--r);padding:.7rem 1rem;margin-bottom:1rem}
.f.error{background:color-mix(in srgb,var(--bad) 11%,var(--card));border-color:var(--bad)}
.pill{display:inline-block;padding:.1rem .65rem;border-radius:999px;font-weight:600;font-size:.8rem;color:var(--pri);background:color-mix(in srgb,currentColor 13%,transparent)}
.pill.Confirmed{color:var(--teal)}.pill.Completed{color:var(--pri)}.pill.Cancelled{color:var(--mut)}.pill.No-Show{color:var(--bad)}.pill.Pending{color:var(--amber)}
.chips{display:flex;flex-wrap:wrap;gap:.5rem;margin:.8rem 0}.chips label{flex-direction:row;cursor:pointer;border:1px solid var(--line);border-radius:6px;padding:.35rem .85rem;background:var(--card)}
.chips input{position:absolute;opacity:0}.chips label:has(input:checked){background:var(--pri);color:#fff;border-color:var(--pri)}.chips label:has(input:focus-visible){outline:2px solid var(--pri);outline-offset:2px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.9rem}.tiles div{border:1px solid var(--line);border-top:4px solid var(--pri);border-radius:var(--r);padding:.8rem 1rem;background:var(--card)}
.tiles div:nth-child(2n){border-top-color:var(--teal)}.tiles b{display:block;font-size:1.8rem;font-weight:700;line-height:1.1}.tiles span{color:var(--mut);font-size:.85rem}
:focus-visible{outline:2px solid var(--pri);outline-offset:2px}@media(max-width:600px){section{padding:.9rem}}</style></head><body>
<nav><b>GCAS<small>ICCT Colleges Cainta · Guidance and Counseling Office</small></b>{% if session.uid %}{% if session.role=='student' %}<a href="/student">Appointments</a>{% elif session.role=='counselor' %}<a href="/counselor">Dashboard</a><a href="/counselor/records">Case records</a>{% else %}<a href="/admin">Administration</a><a href="/admin/reports">Reports</a>{% endif %}<a href="/profile">{{session.name}}</a>
<form method=post action="/logout">{{CSRF()}}<button>Log out</button></form>{% endif %}</nav><main>
{% for c,m in get_flashed_messages(with_categories=true) %}<div class="f {{c}}" role=status>{{m}}</div>{% endfor %}{% block b %}{% endblock %}</main></body></html>"""
def P(body): return "{% extends 'base.html' %}{% block b %}" + body + "{% endblock %}"
PAGES = {"base.html": BASE,
"login.html": P("""<section class=hero style="max-width:460px;margin:2rem auto"><h1>Log in to GCAS</h1><p class=sub>Guidance and Counseling Appointment System. Book or manage your consultations online.</p><form method=post class=i style="flex-direction:column;align-items:stretch">{{CSRF()}}
<label>Username <input name=username required autofocus></label><label>Password <input type=password name=password required></label><button>Log in</button></form>
<p>New student? <a href="/register">Register here</a></p></section>"""),
"register.html": P("""<section style="max-width:520px;margin:1rem auto"><h1>Student registration</h1><p class=sub>Provide an active mobile number. SMS confirmations and reminders are sent to it.</p><form method=post class=i style="flex-direction:column;align-items:stretch">{{CSRF()}}
<label>Full name <input name=full_name required></label><label>Student number <input name=student_no required></label><label>Program <input name=program required></label>
<label>Mobile number (09XXXXXXXXX) <input name=mobile required pattern="(09|\\+639)[0-9]{9}"></label><label>Username <input name=username required></label>
<label>Password (8+ characters) <input type=password name=password minlength=8 required></label><button>Register</button></form></section>"""),
"profile.html": P("""<section><h1>My profile</h1><form method=post class=i>{{CSRF()}}<label>Full name <input name=full_name value="{{u.full_name}}" required></label>
<label>Mobile <input name=mobile value="{{u.mobile or ''}}" required></label><label>New password <input type=password name=password minlength=8></label><button>Save changes</button></form>
<p>SMS alerts (confirmation, reminder, cancellation) go to this number. Keep it active.</p></section>"""),
"student.html": P("""<section class=hero><h1>{{"Reschedule appointment" if resched else "Book an appointment"}}</h1><p class=sub>Select a counselor and date to view available time slots.</p>{% if not counselors %}<p><b>No counselors are available yet.</b> The GCO administrator must first add a counselor account, and that counselor must set weekly hours.</p>{% endif %}<form class=i method=get>{% if resched %}<input type=hidden name=resched value="{{resched}}">{% endif %}
<label>Counselor <select name=counselor>{% for c in counselors %}<option value="{{c.user_id}}" {{'selected' if c.user_id==cid}}>{{c.full_name}} ({{avail[c.user_id].days}})</option>{% endfor %}</select></label>
<label>Date <input type=date name=date value="{{d}}" min="{{today}}"></label><button>Show open slots</button></form>
<table style="margin-top:1rem"><tr><th>Counselor<th>Available days<th>Hours</tr>{% for c in counselors %}<tr><td>{{c.full_name}}<td>{{avail[c.user_id].days}}<td>{{avail[c.user_id].hours or "—"}}</tr>{% endfor %}</table>
{% if slots is not none %}{% if slots %}<form method=post action="{{'/student/reschedule/%s'%resched if resched else '/student/book'}}">{{CSRF()}}<input type=hidden name=counselor value="{{cid}}"><input type=hidden name=date value="{{d}}">
<p class=chips>{% for t in slots %}<label><input type=radio name=time value="{{t}}" required> {{t}}</label> {% endfor %}</p>
{% if not resched %}<label>Concern <input name=concern required size=40></label>{% endif %} <button>{{'Reschedule' if resched else 'Book slot'}}</button></form>{% else %}<p class="f error"><b>Not available.</b> {{why}}</p>{% if nexts %}<p>Next available dates:</p><p class=chips>{% for n in nexts %}<a class=btn href="/student?counselor={{cid}}&date={{n}}{{'&resched='~resched if resched}}">{{n}}</a> {% endfor %}</p>{% endif %}{% endif %}{% endif %}</section>
<section><h2>My appointments</h2><table><tr><th>Date<th>Time<th>Counselor<th>Status<th></tr>{% for a in appts %}<tr><td>{{a.date}}<td>{{a.time}}<td>{{a.cname}}<td><span class="pill {{a.status}}">{{a.status}}</span>
<td>{% if a.status in ('Pending','Confirmed') %}<a class=btn href="/student?resched={{a.id}}&counselor={{a.counselor_id}}">Reschedule</a>
<form method=post action="/student/cancel/{{a.id}}" style="display:inline">{{CSRF()}}<button class=x>Cancel</button></form>{% endif %}</tr>{% else %}<tr><td colspan=5>No appointments yet. Select a counselor and date above to book.</tr>{% endfor %}</table></section>"""),
"counselor.html": P("""<section><h1>Appointments</h1><table><tr><th>Date<th>Time<th>Student<th>Concern<th>Status<th>Action</tr>{% for a in appts %}<tr><td>{{a.date}}<td>{{a.time}}<td><a href="/counselor/student/{{a.student_id}}">{{a.sname}}</a><td>{{a.concern}}<td><span class="pill {{a.status}}">{{a.status}}</span>
<td>{% if a.status=='Confirmed' %}{% if a.started %}<form method=post action="/counselor/mark/{{a.id}}" class=i>{{CSRF()}}<input name=notes placeholder="Session notes"><button name=status value="Completed">Attended</button><button class=x name=status value="No-Show">No-show</button></form>{% endif %}
<form method=post action="/counselor/cancel/{{a.id}}" style="display:inline">{{CSRF()}}<button class=x>Cancel</button></form>{% endif %}</tr>{% else %}<tr><td colspan=6>No appointments yet. Add weekly hours below so students can book.</tr>{% endfor %}</table></section>
<section><h2>Weekly schedule</h2><form method=post action="/counselor/schedule" class=i>{{CSRF()}}<select name=weekday>{% for n in ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'] %}<option value={{loop.index0}}>{{n}}</option>{% endfor %}</select>
<input type=time name=start_time required><input type=time name=end_time required><label>Slot min <input type=number name=slot_min value=30 min=15 max=120 style="width:5rem"></label><button>Add hours</button></form>
<table>{% for s in sched %}<tr><td>{{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][s.weekday]}}<td>{{s.start_time}}–{{s.end_time}}<td>{{s.slot_min}} min<td><form method=post action="/counselor/schedule/{{s.id}}/delete">{{CSRF()}}<button class=x>Remove</button></form></tr>{% endfor %}</table>
<h2>Block a date</h2><form method=post action="/counselor/timeoff" class=i>{{CSRF()}}<input type=date name=date required><button>Block date</button></form><p>{% for t in off %}{{t.date}} {% endfor %}</p></section>"""),
"records.html": P("""<section class=hero><h1>Case records</h1><form class=i><input name=q value="{{q}}" placeholder="Name or student number"><button>Search</button></form><table><tr><th>Student<th>No.<th>Program</tr>
{% for s in rows %}<tr><td><a href="/counselor/student/{{s.id}}">{{s.full_name}}</a><td>{{s.student_no}}<td>{{s.program}}</tr>{% else %}<tr><td colspan=3>No matching students.</tr>{% endfor %}</table></section>"""),
"student_case.html": P("""<section><h1>{{s.full_name}}</h1><p>{{s.student_no}} · {{s.program}}</p><table><tr><th>Date<th>Counselor<th>Status<th>Concern<th>Session notes</tr>
{% for a in hist %}<tr><td>{{a.date}} {{a.time}}<td>{{a.cname}}<td><span class="pill {{a.status}}">{{a.status}}</span><td>{{a.concern}}<td>{{a.notes or ''}}</tr>{% endfor %}</table></section>"""),
"admin.html": P("""<section class=hero><h1>Dashboard overview</h1><div class=tiles>{% for k,v in stats.items() %}<div><b>{{v}}</b><span>{{k}}</span></div>{% endfor %}</div></section>
<section><h2>Add counselor account</h2><form method=post action="/admin/counselor" class=i>{{CSRF()}}<input name=full_name id=cn placeholder="Full name" required><button type=button class=btn onclick="var F=['Maria','Angelica','Jose','Mark','Carmela','Paolo','Bianca','Ramon','Katrina','Joel','Liza','Miguel'],L=['Reyes','Santos','Dela Cruz','Garcia','Mendoza','Bautista','Villanueva','Ramos','Aquino','Castillo'],r=a=>a[Math.floor(Math.random()*a.length)],n=r(F)+' '+r(L);cn.value=n;if(!document.getElementById('un').value)un.value=n.toLowerCase().replace(/[^a-z]+/g,'.')">Random name</button><input name=username id=un placeholder="Username" required>
<input name=mobile placeholder="09XXXXXXXXX" required><input type=password name=password placeholder="Temp password (8+)" minlength=8 required><button>Create counselor</button></form></section>
<section><h2>Accounts</h2><table><tr><th>Name<th>Username<th>Role<th>Active<th></tr>{% for u in users %}<tr><td>{{u.full_name}}<td>{{u.username}}<td>
<form method=post action="/admin/user/{{u.id}}/role" class=i>{{CSRF()}}<select name=role>{% for r in ['student','counselor','admin'] %}<option {{'selected' if r==u.role}}>{{r}}</option>{% endfor %}</select><button>Set role</button></form>
<td>{{'Yes' if u.active else 'No'}}<td><form method=post action="/admin/user/{{u.id}}/toggle">{{CSRF()}}<button class=x>{{'Deactivate' if u.active else 'Activate'}}</button></form></tr>{% endfor %}</table></section>"""),
"reports.html": P("""<section><h1>Weekly report</h1><table><tr><th>Week<th>Total<th>Completed<th>No-show<th>Cancelled<th>No-show rate</tr>{% for w in weekly %}<tr><td>{{w.wk}}<td>{{w.total}}<td>{{w.done}}<td>{{w.ns}}<td>{{w.cx}}<td>{{w.rate}}%</tr>{% else %}<tr><td colspan=6>No data yet.</tr>{% endfor %}</table></section>
<section><h2>All appointments</h2><form class=i><select name=status><option value="">Any status</option>{% for s in ['Pending','Confirmed','Cancelled','Completed','No-Show'] %}<option {{'selected' if s==st}}>{{s}}</option>{% endfor %}</select><button>Filter</button></form>
<table><tr><th>Date<th>Student<th>Counselor<th>Status</tr>{% for a in appts %}<tr><td>{{a.date}} {{a.time}}<td>{{a.sname}}<td>{{a.cname}}<td><span class="pill {{a.status}}">{{a.status}}</span></tr>{% endfor %}</table>
<h2>SMS log</h2><table><tr><th>When<th>Kind<th>Status<th>Tries</tr>{% for m in logs %}<tr><td>{{m.created_at}}<td>{{m.kind}}<td>{{m.status}}<td>{{m.attempts}}</tr>{% endfor %}</table></section>""")}

#!/usr/bin/env python3
"""
render-dashboard.py — build a single self-contained dashboard.html from the markdown
artifacts of one feature plan.

The markdown files stay the source of truth: agents read and write them, this script only
ever READS them and writes one derived file (dashboard.html). Nothing here costs model
tokens — it is deterministic, stdlib-only Python 3.8+.

Usage:
    render-dashboard.py <plans/<slug>/  |  any file inside it>   [--out PATH] [--quiet]

Exits 0 and does nothing when the directory has no PLAN.md, so it is safe to wire into a
PostToolUse hook that fires on every markdown write.
"""

import html
import os
import re
import sys
import time

# --------------------------------------------------------------------------------------
# Markdown → HTML (deliberately a SUBSET: exactly what the feature-workflow templates use)
# --------------------------------------------------------------------------------------

COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
FENCE_RE = re.compile(r"^\s*```+\s*([\w+-]*)\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
BULLET_RE = re.compile(r"^(\s*)[-*+]\s+(.*)$")
ORDERED_RE = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
CHECKBOX_RE = re.compile(r"^\[([ xX])\]\s*(.*)$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
HR_RE = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")
TASK_ID_RE = re.compile(r"\btask-(\d{3})\b")
TC_ID_RE = re.compile(r"\bTC-(\d+)\b")


def esc(text):
    return html.escape(text, quote=True)


def inline(text, links=True):
    """Inline markdown → HTML. Code spans are protected from every other rule."""
    spans = []

    def stash(match):
        spans.append(match.group(1))
        return "\x00%d\x00" % (len(spans) - 1)

    text = re.sub(r"`([^`]+)`", stash, text)
    out = esc(text)
    out = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)[^)]*\)", r'<img src="\2" alt="\1">', out)
    out = re.sub(r"\[([^\]]+)\]\(([^)\s]+)[^)]*\)", r'<a href="\2">\1</a>', out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", out)
    out = re.sub(r"(?<![\w_])_([^_\n]+)_(?![\w_])", r"<em>\1</em>", out)
    if links:
        out = TASK_ID_RE.sub(r'<a class="xref" href="#task-\1">task-\1</a>', out)
        out = TC_ID_RE.sub(r'<a class="xref" href="#tc-\1">TC-\1</a>', out)
    for i, code in enumerate(spans):
        out = out.replace("\x00%d\x00" % i, "<code>%s</code>" % esc(code))
    return out


def _cells(row):
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [c.strip() for c in row.split("|")]


def _render_list(items, ordered):
    """items: list of (indent, text, checked) — checked is None when not a checkbox."""
    html_out = []
    tag = "ol" if ordered else "ul"

    def build(index, indent):
        parts = ['<%s>' % tag]
        while index < len(items):
            ind, text, checked = items[index]
            if ind < indent:
                break
            if ind > indent:
                sub, index = build(index, ind)
                parts[-1] = parts[-1][:-5] + sub + "</li>"
                continue
            body = inline(text)
            if checked is None:
                parts.append("<li>%s</li>" % body)
            else:
                parts.append('<li class="chk%s"><i></i><span>%s</span></li>'
                             % (" on" if checked else "", body))
            index += 1
        parts.append("</%s>" % tag)
        return "".join(parts), index

    rendered, _ = build(0, items[0][0] if items else 0)
    html_out.append(rendered)
    return "".join(html_out)


def md_to_html(md, row_anchor=False):
    """Block-level markdown → HTML.

    row_anchor: give every table row whose first cell is a TC id an anchor, so the rest of
    the dashboard can deep-link to a single testcase.
    """
    md = COMMENT_RE.sub("", md or "")
    lines = md.split("\n")
    out = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        fence = FENCE_RE.match(line)
        if fence:
            lang = fence.group(1)
            i += 1
            body = []
            while i < n and not FENCE_RE.match(lines[i]):
                body.append(lines[i])
                i += 1
            i += 1
            cls = ' class="lang-%s"' % esc(lang) if lang else ""
            out.append("<pre%s><code>%s</code></pre>" % (cls, esc("\n".join(body))))
            continue

        if not line.strip():
            i += 1
            continue

        heading = HEADING_RE.match(line)
        if heading:
            level = min(len(heading.group(1)) + 1, 6)
            out.append("<h%d>%s</h%d>" % (level, inline(heading.group(2)), level))
            i += 1
            continue

        if HR_RE.match(line):
            out.append("<hr>")
            i += 1
            continue

        # table: a header row followed by a separator row
        if "|" in line and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1]):
            header = _cells(line)
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(_cells(lines[i]))
                i += 1
            thead = "".join("<th>%s</th>" % inline(c) for c in header)
            labels = [re.sub(r"[`*_]", "", c).strip() for c in header]
            body = []
            for row in rows:
                anchor = ""
                if row_anchor and row:
                    tc = TC_ID_RE.match(row[0].strip())
                    if tc:
                        anchor = ' id="tc-%s"' % tc.group(1)
                cells = "".join(
                    '<td data-label="%s">%s</td>'
                    % (esc(labels[k]) if k < len(labels) else "", inline(c))
                    for k, c in enumerate(row))
                body.append("<tr%s>%s</tr>" % (anchor, cells))
            # 4+ columns can never fit a phone: those stack into rows of label/value pairs
            wrap_cls = "tw wide" if len(header) >= 4 else "tw"
            out.append(
                '<div class="%s"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
                % (wrap_cls, thead, "".join(body))
            )
            continue

        if line.lstrip().startswith(">"):
            quote = []
            while i < n and lines[i].lstrip().startswith(">"):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>%s</blockquote>" % md_to_html("\n".join(quote)))
            continue

        bullet = BULLET_RE.match(line)
        ordered = ORDERED_RE.match(line)
        if bullet or ordered:
            is_ordered = bool(ordered and not bullet)
            items = []
            while i < n:
                b = BULLET_RE.match(lines[i])
                o = ORDERED_RE.match(lines[i])
                if not b and not o:
                    if lines[i].strip() and lines[i].startswith(("  ", "\t")) and items:
                        ind, text, checked = items[-1]
                        items[-1] = (ind, text + " " + lines[i].strip(), checked)
                        i += 1
                        continue
                    break
                indent = len((b or o).group(1).replace("\t", "  "))
                text = b.group(2) if b else o.group(3)
                checked = None
                cb = CHECKBOX_RE.match(text)
                if cb:
                    checked = cb.group(1).lower() == "x"
                    text = cb.group(2)
                items.append((indent, text, checked))
                i += 1
            out.append(_render_list(items, is_ordered))
            continue

        para = []
        while i < n and lines[i].strip() and not HEADING_RE.match(lines[i]) \
                and not FENCE_RE.match(lines[i]) and not BULLET_RE.match(lines[i]) \
                and not ORDERED_RE.match(lines[i]) and not HR_RE.match(lines[i]) \
                and not lines[i].lstrip().startswith(">"):
            if "|" in lines[i] and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1]):
                break
            para.append(lines[i])
            i += 1
        if para:
            out.append("<p>%s</p>" % inline(" ".join(l.strip() for l in para)))

    return "".join(out)


# --------------------------------------------------------------------------------------
# Reading the plan artifacts
# --------------------------------------------------------------------------------------

STATUS_ORDER = ["done", "needs-human", "in-progress", "blocked", "todo"]
STATUS_LABEL = {
    "todo": "todo",
    "in-progress": "in-progress",
    "done": "done",
    "blocked": "blocked",
    "needs-human": "needs-human",
}


def read(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except (IOError, OSError):
        return ""


def split_frontmatter(text):
    """Return (dict, body). Supports the flat `key: value` + simple list subset we use."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end]
    body = text[end + 4:]
    data = {}
    key = None
    for line in raw.split("\n"):
        line = line.split(" #")[0].rstrip() if " #" in line else line.rstrip()
        if not line.strip():
            continue
        item = re.match(r"^\s+-\s+(.*)$", line)
        if item and key:
            data.setdefault(key, [])
            if isinstance(data[key], list):
                data[key].append(item.group(1).strip().strip("\"'"))
            continue
        kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if kv:
            key = kv.group(1)
            value = kv.group(2).strip()
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                data[key] = [v.strip().strip("\"'") for v in inner.split(",") if v.strip()]
            elif value == "":
                data[key] = []
            else:
                data[key] = value.strip("\"'")
    return data, body


def sections(md):
    """Split a document into [(heading_text, body_md)] on `## ` boundaries."""
    md = COMMENT_RE.sub("", md or "")
    out = []
    current = ("", [])
    for line in md.split("\n"):
        m = re.match(r"^##\s+(.*?)\s*$", line)
        if m:
            out.append((current[0], "\n".join(current[1])))
            current = (m.group(1).strip(), [])
        else:
            current[1].append(line)
    out.append((current[0], "\n".join(current[1])))
    return out


def first_table(md):
    """Return [(header, [rows])] for the first pipe table in a chunk of markdown."""
    lines = (md or "").split("\n")
    for i in range(len(lines) - 1):
        if "|" in lines[i] and TABLE_SEP_RE.match(lines[i + 1]):
            header = [c.lower().strip() for c in _cells(lines[i])]
            rows = []
            j = i + 2
            while j < len(lines) and "|" in lines[j] and lines[j].strip():
                rows.append(_cells(lines[j]))
                j += 1
            return header, rows
    return [], []


def norm_status(value):
    value = (value or "").strip().lower()
    value = re.sub(r"[`*_]", "", value)
    return value if value in STATUS_LABEL else "todo"


def parse_plan(plan_dir):
    md = read(os.path.join(plan_dir, "PLAN.md"))
    if not md:
        return None
    stripped = COMMENT_RE.sub("", md)
    title = ""
    for line in stripped.split("\n"):
        m = re.match(r"^#\s+(.*)$", line)
        if m:
            title = re.sub(r"^Plan\s*[—:-]\s*", "", m.group(1)).strip()
            break
    status = ""
    m = re.search(r"Status:\s*([A-Za-z-]+)", stripped)
    if m:
        status = m.group(1).strip().lower()
    drafted = ""
    m = re.search(r"Drafted:\s*([0-9-]{4,10})", stripped)
    if m:
        drafted = m.group(1)

    secs = sections(md)
    tasks = []
    queue_rows = []
    for name, body in secs:
        low = name.lower()
        if low.startswith("tasks"):
            header, rows = first_table(body)
            idx = dict((h, k) for k, h in enumerate(header))
            for row in rows:
                def col(key, default=""):
                    k = idx.get(key)
                    if k is None or k >= len(row):
                        return default
                    return re.sub(r"[`*]", "", row[k]).strip()
                tid = col("id")
                if not re.match(r"^task-\d+$", tid):
                    continue
                deps = [d.strip() for d in re.split(r"[,\s]+", col("depends_on"))
                        if re.match(r"^task-\d+$", d.strip())]
                tasks.append({
                    "id": tid,
                    "title": col("title"),
                    "repo": col("repo"),
                    "depends_on": deps,
                    "model": col("model").lower(),
                    "risk": col("risk").lower(),
                    "ui_verify": col("ui_verify").lower() or "none",
                    "status": norm_status(col("status")),
                    "spec": None,
                    "body": "",
                    "fm": {},
                    "mismatch": "",
                })
        elif "manual verification" in low:
            header, rows = first_table(body)
            for row in rows:
                if row and re.match(r"^task-\d+", re.sub(r"[`*]", "", row[0]).strip()):
                    queue_rows.append(row)
    return {
        "title": title or os.path.basename(plan_dir.rstrip("/")),
        "status": status or "draft",
        "drafted": drafted,
        "sections": secs,
        "tasks": tasks,
        "queue": queue_rows,
        "raw": md,
    }


def attach_specs(plan, plan_dir):
    """Merge tasks/*.md into the PLAN.md table. PLAN.md wins on status; disagreement is
    surfaced rather than silently resolved."""
    tasks_dir = os.path.join(plan_dir, "tasks")
    by_id = dict((t["id"], t) for t in plan["tasks"])
    try:
        files = sorted(f for f in os.listdir(tasks_dir) if f.endswith(".md"))
    except (IOError, OSError):
        return
    for name in files:
        path = os.path.join(tasks_dir, name)
        fm, body = split_frontmatter(read(path))
        tid = str(fm.get("id", "")).strip()
        if not re.match(r"^task-\d+$", tid):
            m = re.match(r"^(task-\d+)", name)
            tid = m.group(1) if m else ""
        if not tid:
            continue
        task = by_id.get(tid)
        if task is None:
            deps = fm.get("depends_on") or []
            task = {
                "id": tid, "title": str(fm.get("title", tid)), "repo": str(fm.get("repo", "")),
                "depends_on": deps if isinstance(deps, list) else [],
                "model": str(fm.get("model", "")).lower(), "risk": str(fm.get("risk", "")).lower(),
                "ui_verify": str(fm.get("ui_verify", "none")).lower(),
                "status": norm_status(str(fm.get("status", "todo"))),
                "mismatch": "không có trong bảng task của PLAN.md",
            }
            plan["tasks"].append(task)
            by_id[tid] = task
        task["spec"] = os.path.join("tasks", name)
        task["body"] = body
        task["fm"] = fm
        if not task.get("title"):
            task["title"] = str(fm.get("title", tid))
        spec_status = norm_status(str(fm.get("status", "")))
        if fm.get("status") and spec_status != task["status"]:
            task["mismatch"] = "PLAN.md ghi `%s`, spec ghi `%s`" % (task["status"], spec_status)
    plan["tasks"].sort(key=lambda t: t["id"])


def depth_levels(tasks):
    """Longest-path depth per task → the parallel lanes. Cycle-safe."""
    by_id = dict((t["id"], t) for t in tasks)
    memo = {}

    def depth(tid, seen):
        if tid in memo:
            return memo[tid]
        if tid in seen or tid not in by_id:
            return 0
        seen = seen | {tid}
        deps = [d for d in by_id[tid]["depends_on"] if d in by_id]
        value = 0 if not deps else 1 + max(depth(d, seen) for d in deps)
        memo[tid] = value
        return value

    lanes = {}
    for task in tasks:
        lanes.setdefault(depth(task["id"], set()), []).append(task)
    return [lanes[k] for k in sorted(lanes)]


def parse_journal(journal_md):
    """The journal table of PROGRESS.md as structured events, so the dashboard can show what
    happened to a task rather than making the reader scan rows."""
    header, rows = first_table(journal_md)
    idx = dict((h, i) for i, h in enumerate(header))
    fallback = ["when", "task", "action", "agent", "note"]
    events = []
    for row in rows:
        def col(key):
            k = idx.get(key)
            if k is None and key in fallback:
                k = fallback.index(key)          # header not in English → positional
            if k is None or k >= len(row):
                return ""
            return re.sub(r"[`*]", "", row[k]).strip()
        m = re.match(r"^(task-\d+)", col("task"))
        events.append({"when": col("when"), "task": m.group(1) if m else "",
                       "action": col("action"), "agent": col("agent"), "note": col("note")})
    return events


def journal_stats(events):
    stats = {}
    for e in events:
        if not e["task"]:
            continue
        st = stats.setdefault(e["task"], {"events": [], "attempts": 0, "fails": 0,
                                          "last_fail": "", "blocked": False})
        st["events"].append(e)
        action = e["action"].lower()
        if action.startswith("dispatch"):
            st["attempts"] += 1
        elif action.startswith("fail"):
            st["fails"] += 1
            st["last_fail"] = e["note"]
        elif action.startswith("blocked"):
            st["blocked"] = True
    return stats


def action_pill(action):
    a = action.lower()
    cls = "todo"
    if a.startswith("pass"):
        cls = "done"
    elif a.startswith("fail") or a.startswith("blocked"):
        cls = "blocked"
    elif a.startswith("needs-human"):
        cls = "needs-human"
    elif a.startswith("dispatch"):
        cls = "in-progress"
    return '<span class="pill %s">%s</span>' % (cls, esc(action or "—"))


def html_table(headers, rows):
    """Same markup the markdown tables get, so narrow screens stack it identically."""
    thead = "".join("<th>%s</th>" % esc(h) for h in headers)
    body = []
    for row in rows:
        cells = "".join('<td data-label="%s">%s</td>'
                        % (esc(headers[i]) if i < len(headers) else "", cell)
                        for i, cell in enumerate(row))
        body.append("<tr>%s</tr>" % cells)
    cls = "tw wide" if len(headers) >= 4 else "tw"
    return ('<div class="%s"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
            % (cls, thead, "".join(body)))


def parse_progress(md):
    """Pull the HANDOFF block out of PROGRESS.md so it can be pinned and copied."""
    if not md:
        return "", ""
    m = re.search(r"^##\s+HANDOFF[^\n]*\n(.*)$", COMMENT_RE.sub("", md), re.S | re.M)
    if not m:
        return md, ""
    return md[:m.start()], m.group(1)


# --------------------------------------------------------------------------------------
# The page
# --------------------------------------------------------------------------------------

CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{
  --bg:#f6f7f9; --panel:#fff; --panel2:#fbfbfd; --ink:#1b1d21; --muted:#69707d;
  --line:#e3e6ec; --accent:#4f46e5; --accent-soft:#eef0fe;
  --done:#15803d; --done-bg:#e7f6ec; --prog:#1d4ed8; --prog-bg:#e6edfd;
  --todo:#5b6472; --todo-bg:#eef0f3; --block:#b91c1c; --block-bg:#fdeaea;
  --human:#a35a06; --human-bg:#fdf1e0; --risk:#b91c1c;
  --shadow:0 1px 2px rgba(16,20,30,.05),0 8px 24px rgba(16,20,30,.06);
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme=light]){
    --bg:#0e1015; --panel:#161922; --panel2:#1b1f2a; --ink:#e7e9ef; --muted:#98a1b1;
    --line:#262b37; --accent:#8b93f8; --accent-soft:#20233a;
    --done:#5ed58c; --done-bg:#132a1d; --prog:#8ab0ff; --prog-bg:#141f38;
    --todo:#98a1b1; --todo-bg:#1e222c; --block:#ff8f8f; --block-bg:#2c1618;
    --human:#f0b45e; --human-bg:#2e2210; --risk:#ff8f8f;
    --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.25);
  }
}
:root[data-theme=dark]{
  --bg:#0e1015; --panel:#161922; --panel2:#1b1f2a; --ink:#e7e9ef; --muted:#98a1b1;
  --line:#262b37; --accent:#8b93f8; --accent-soft:#20233a;
  --done:#5ed58c; --done-bg:#132a1d; --prog:#8ab0ff; --prog-bg:#141f38;
  --todo:#98a1b1; --todo-bg:#1e222c; --block:#ff8f8f; --block-bg:#2c1618;
  --human:#f0b45e; --human-bg:#2e2210; --risk:#ff8f8f;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.25);
}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,"Helvetica Neue",sans-serif;
  -webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
code{font-family:var(--mono);font-size:.87em;background:var(--accent-soft);
  padding:.1em .35em;border-radius:4px;overflow-wrap:break-word;word-break:normal}
pre{background:var(--panel2);border:1px solid var(--line);border-radius:10px;
  padding:12px 14px;overflow-x:auto;font-size:13px;line-height:1.5}
pre code{background:none;padding:0;font-size:inherit}
hr{border:0;border-top:1px solid var(--line);margin:18px 0}
blockquote{margin:12px 0;padding:2px 14px;border-left:3px solid var(--accent);
  background:var(--panel2);border-radius:0 8px 8px 0;color:var(--muted)}
img{max-width:100%}
.tw{overflow-x:auto;margin:12px 0;border:1px solid var(--line);border-radius:10px}
.tw,pre,.lanes{scrollbar-width:thin;scrollbar-color:var(--line) transparent}
.tw::-webkit-scrollbar,pre::-webkit-scrollbar,.lanes::-webkit-scrollbar{height:9px;width:9px}
.tw::-webkit-scrollbar-thumb,pre::-webkit-scrollbar-thumb,.lanes::-webkit-scrollbar-thumb{
  background:var(--line);border-radius:9px}
.tw::-webkit-scrollbar-track,pre::-webkit-scrollbar-track,.lanes::-webkit-scrollbar-track{
  background:transparent}
.card,.deps,p,li,td,th,blockquote{overflow-wrap:break-word}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{padding:8px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--panel2);font-weight:600;font-size:12px;letter-spacing:.02em;
  text-transform:uppercase;color:var(--muted);white-space:nowrap}
tbody tr:last-child td{border-bottom:0}
tbody tr:target{background:var(--accent-soft)}
ul,ol{padding-left:22px;margin:8px 0}
li{margin:3px 0}
li.chk{list-style:none;margin-left:-20px;display:flex;gap:9px;align-items:flex-start}
li.chk i{flex:none;width:15px;height:15px;margin-top:5px;border:1.5px solid var(--line);
  border-radius:4px;position:relative;background:var(--panel2)}
li.chk.on i{background:var(--done);border-color:var(--done)}
li.chk.on i::after{content:"";position:absolute;left:4.5px;top:1px;width:4px;height:8px;
  border:solid #fff;border-width:0 2px 2px 0;transform:rotate(45deg)}
:root[data-theme=dark] li.chk.on i::after{border-color:#0e1015}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) li.chk.on i::after{border-color:#0e1015}}
/* layout */
.wrap{display:flex;align-items:flex-start;max-width:1500px;margin:0 auto}
nav{position:sticky;top:0;flex:none;width:250px;max-height:100vh;overflow-y:auto;
  overscroll-behavior:contain;padding:20px 14px;border-right:1px solid var(--line)}
main{flex:1;min-width:0;padding:22px 30px 120px}
.brand{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);
  margin:0 0 10px 8px}
nav a.nl{display:flex;justify-content:space-between;gap:8px;align-items:center;
  padding:6px 10px;border-radius:8px;color:var(--ink);font-size:13.5px}
nav a.nl:hover{background:var(--panel);text-decoration:none}
nav a.nl.on{background:var(--accent-soft);color:var(--accent);font-weight:600}
nav .grp{margin:16px 0 6px 8px;font-size:11px;text-transform:uppercase;letter-spacing:.06em;
  color:var(--muted)}
nav .tl{display:flex;gap:8px;align-items:center;padding:5px 10px;border-radius:8px;
  font-size:13px;color:var(--ink)}
nav .tl:hover{background:var(--panel);text-decoration:none}
nav .tl .dot{flex:none;width:8px;height:8px;border-radius:50%}
nav .tl span.t{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
/* header */
header{background:var(--panel);border:1px solid var(--line);border-radius:14px;
  padding:18px 20px;box-shadow:var(--shadow);margin-bottom:18px}
h1{margin:0;font-size:23px;letter-spacing:-.01em}
.sub{color:var(--muted);font-size:13px;margin-top:6px;display:flex;flex-wrap:wrap;gap:6px 14px}
.bar{height:8px;border-radius:99px;background:var(--todo-bg);overflow:hidden;display:flex;
  margin-top:14px}
.bar i{display:block;height:100%}
.legend{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.pill{display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:600;
  padding:2px 9px;border-radius:99px;white-space:nowrap}
.pill.done{color:var(--done);background:var(--done-bg)}
.pill.in-progress{color:var(--prog);background:var(--prog-bg)}
.pill.todo{color:var(--todo);background:var(--todo-bg)}
.pill.blocked{color:var(--block);background:var(--block-bg)}
.pill.needs-human{color:var(--human);background:var(--human-bg)}
.tag{display:inline-flex;align-items:center;gap:4px;font-size:11.5px;padding:1px 8px;
  border-radius:99px;border:1px solid var(--line);color:var(--muted);white-space:nowrap;
  font-family:var(--mono)}
.tag.risk{color:var(--risk);border-color:var(--risk)}
.tag.ui{color:var(--accent);border-color:var(--accent)}
/* sections + cards */
section{scroll-margin-top:14px;margin-bottom:34px}
h2.sh{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);
  margin:0 0 12px 2px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;
  padding:18px 20px;box-shadow:var(--shadow);margin-bottom:14px}
.card>h3:first-child,.card>h2:first-child{margin-top:0}
.card h3{font-size:15px;margin:18px 0 8px}
.card h4{font-size:13.5px;margin:14px 0 6px;color:var(--muted)}
.card p{margin:8px 0}
.alert{border-color:var(--human);background:var(--human-bg)}
.attn{border-color:var(--block)}
.attn>h3:first-child{color:var(--block)}
.lesson{border-left:3px solid var(--accent)}
.lesson>h3:first-child{color:var(--accent)}
.act{margin:16px 0 6px}
.act h4{margin:0 0 2px;color:var(--muted)}
.tag.fail{color:var(--block);border-color:var(--block)}
.alert .tw{border-color:var(--human)}
.warn{font-size:12.5px;color:var(--human);background:var(--human-bg);border-radius:8px;
  padding:6px 10px;margin:10px 0}
/* tasks */
.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;align-items:center}
.toolbar input{flex:1;min-width:180px;padding:8px 12px;border-radius:10px;
  border:1px solid var(--line);background:var(--panel);color:var(--ink);font-size:13.5px}
.toolbar input:focus{outline:2px solid var(--accent);outline-offset:-1px}
button{font:inherit;font-size:13px;padding:7px 12px;border-radius:10px;cursor:pointer;
  border:1px solid var(--line);background:var(--panel);color:var(--ink)}
button:hover{border-color:var(--accent);color:var(--accent)}
.task{scroll-margin-top:14px}
.task[hidden]{display:none}
.task summary{cursor:pointer;list-style:none;display:flex;gap:10px;align-items:baseline;
  flex-wrap:wrap;margin:-18px -20px;padding:18px 20px}
.task summary::-webkit-details-marker{display:none}
.task summary:hover .tt{color:var(--accent)}
.task[open] summary{border-bottom:1px solid var(--line);margin-bottom:14px}
.tid{font-family:var(--mono);font-size:12px;color:var(--muted);flex:none}
.tt{font-weight:600;font-size:15px;flex:1;min-width:150px}
.meta{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.deps{font-size:12.5px;color:var(--muted);margin:0 0 12px}
.deps a{font-family:var(--mono);font-size:12px}
/* lanes */
.lanes{display:flex;gap:12px;overflow-x:auto;padding-bottom:6px}
.lane{flex:none;min-width:150px;background:var(--panel2);border:1px solid var(--line);
  border-radius:12px;padding:10px}
.lane h4{margin:0 0 8px;font-size:11px;text-transform:uppercase;letter-spacing:.06em;
  color:var(--muted)}
.lane a{display:flex;gap:7px;align-items:center;font-size:12.5px;padding:5px 7px;
  border-radius:8px;color:var(--ink);font-family:var(--mono)}
.lane a:hover{background:var(--panel);text-decoration:none}
.dot{width:8px;height:8px;border-radius:50%;flex:none}
.dot.done{background:var(--done)}.dot.in-progress{background:var(--prog)}
.dot.todo{background:var(--todo)}.dot.blocked{background:var(--block)}
.dot.needs-human{background:var(--human)}
.foot{color:var(--muted);font-size:12px;text-align:center;padding:20px 0 0}
.tools{position:fixed;bottom:14px;right:16px;display:flex;gap:6px;z-index:5}
.tools button{background:var(--panel);box-shadow:var(--shadow)}
/* ── narrow: the sidebar becomes a sticky row of section links ─────────────── */
@media (max-width:1080px){
  .wrap{flex-direction:column;max-width:100%}
  nav{position:sticky;top:0;z-index:4;width:100%;max-height:none;overflow-x:auto;
    overflow-y:hidden;display:flex;gap:6px;align-items:center;padding:9px 12px;
    background:var(--bg);border-right:0;border-bottom:1px solid var(--line)}
  nav .brand,nav .grp,nav .tl{display:none}
  nav a.nl{flex:none;white-space:nowrap;padding:6px 12px}
  main{width:100%;padding:16px 16px 90px}
  section,.task,tbody tr{scroll-margin-top:64px}
}
/* ── phones: 4+ column tables stack instead of scrolling sideways ──────────── */
@media (max-width:760px){
  .tw.wide{border:0;overflow-x:visible;border-radius:0}
  .tw.wide table,.tw.wide tbody,.tw.wide tr,.tw.wide td{display:block;width:auto}
  .tw.wide thead{display:none}
  .tw.wide tr{border:1px solid var(--line);border-radius:10px;background:var(--panel2);
    margin-bottom:10px;padding:6px 2px}
  .tw.wide tr:last-child{margin-bottom:0}
  .tw.wide td{border-bottom:0;padding:6px 12px}
  .tw.wide td+td{border-top:1px dashed var(--line)}
  .tw.wide td::before{content:attr(data-label);display:block;font-size:10.5px;
    text-transform:uppercase;letter-spacing:.04em;color:var(--muted);font-weight:600;
    margin-bottom:1px}
  .tw.wide td:not([data-label])::before,.tw.wide td[data-label=""]::before{display:none}
  .tw.wide tr:target{background:var(--accent-soft);border-color:var(--accent)}
}
@media (max-width:600px){
  main{padding:14px 12px 90px}
  header,.card{padding:14px;border-radius:12px}
  .task summary{margin:-14px;padding:14px}
  .task[open] summary{margin-bottom:12px}
  h1{font-size:20px}
  body{font-size:14.5px}
}
@media print{
  nav,.tools,.toolbar{display:none}
  .task{break-inside:avoid}
  .task .body{display:block!important}
  .card{box-shadow:none}
}
"""

JS = """
(function(){
  var root=document.documentElement, KEY='fw-theme';
  try{var t=localStorage.getItem(KEY); if(t) root.setAttribute('data-theme',t);}catch(e){}
  var tb=document.getElementById('theme');
  if(tb) tb.onclick=function(){
    var cur=root.getAttribute('data-theme');
    if(!cur) cur=matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light';
    var next=cur==='dark'?'light':'dark';
    root.setAttribute('data-theme',next);
    try{localStorage.setItem(KEY,next);}catch(e){}
  };
  var tasks=[].slice.call(document.querySelectorAll('details.task'));
  var q=document.getElementById('q');
  if(q) q.oninput=function(){
    var v=q.value.trim().toLowerCase();
    tasks.forEach(function(d){
      if(!v){ d.hidden=false; return; }
      var hit=d.textContent.toLowerCase().indexOf(v)>-1;
      d.hidden=!hit;
      if(hit && d.querySelector('.body').textContent.toLowerCase().indexOf(v)>-1) d.open=true;
    });
  };
  var ex=document.getElementById('expand');
  if(ex) ex.onclick=function(){
    var anyClosed=tasks.some(function(d){return !d.open && !d.hidden;});
    tasks.forEach(function(d){ if(!d.hidden) d.open=anyClosed; });
    ex.textContent=anyClosed?ex.dataset.close:ex.dataset.open;
  };
  function openHash(){
    var h=location.hash.slice(1); if(!h) return;
    var el=document.getElementById(h); if(!el) return;
    var d=el.closest?el.closest('details'):null; if(d) d.open=true;
    if(el.tagName==='DETAILS') el.open=true;
    setTimeout(function(){el.scrollIntoView({block:'start'});},0);
  }
  addEventListener('hashchange',openHash); openHash();
  var cp=document.getElementById('copy');
  if(cp) cp.onclick=function(){
    var txt=document.getElementById('handoff-src').textContent;
    var lbl=cp.textContent;
    var done=function(){cp.textContent=cp.dataset.done;setTimeout(function(){cp.textContent=lbl;},1800);};
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(done,done);}
    else{var ta=document.createElement('textarea');ta.value=txt;document.body.appendChild(ta);
      ta.select();try{document.execCommand('copy');}catch(e){}document.body.removeChild(ta);done();}
  };
  var links=[].slice.call(document.querySelectorAll('nav a.nl'));
  var secs=links.map(function(a){return document.getElementById(a.getAttribute('href').slice(1));});
  function spy(){
    var best=0;
    secs.forEach(function(s,i){ if(s && s.getBoundingClientRect().top<=120) best=i; });
    links.forEach(function(a,i){ a.classList.toggle('on',i===best); });
  }
  addEventListener('scroll',spy,{passive:true}); spy();
})();
"""

STR = {
    "en": {
        "overview": "Overview", "tasks": "Tasks", "testcases": "Testcases",
        "progress": "Progress", "context": "System context", "queue": "Manual verification queue",
        "handoff": "HANDOFF — read this to continue", "journal": "Journal",
        "filter": "Filter tasks…", "expand": "Expand all", "collapse": "Collapse all",
        "copy": "Copy HANDOFF", "copied": "Copied ✓", "theme": "Theme",
        "group": "Group", "deps": "Depends on", "unlocks": "Unlocks", "nodeps": "no dependencies",
        "files": "Files", "spec": "open .md", "generated": "Generated",
        "derived": "Generated file — do not edit. The markdown files next to it are the source "
                   "of truth; this page is rebuilt from them.",
        "mismatch": "Status mismatch", "notasks": "No tasks in the PLAN.md table yet.",
        "of": "of", "donelabel": "done",
        "attention": "Needs attention — tasks that failed or stalled",
        "activity": "What happened to this task", "attempts": "attempts",
        "lastfail": "last failure", "colwhen": "when", "colaction": "action",
        "colagent": "agent", "colnote": "note", "colstatus": "status", "coltask": "task",
        "lessons": "Lessons from failed attempts — every later executor reads these",
        "attention_nav": "Needs attention", "lessons_nav": "Lessons",
        "retries": "re-runs",
    },
    "vi": {
        "overview": "Tổng quan", "tasks": "Task", "testcases": "Testcase",
        "progress": "Tiến độ", "context": "System context", "queue": "Manual verification queue",
        "handoff": "HANDOFF — đọc khối này để làm tiếp", "journal": "Nhật ký",
        "filter": "Lọc task…", "expand": "Mở tất cả", "collapse": "Đóng tất cả",
        "copy": "Copy HANDOFF", "copied": "Đã copy ✓", "theme": "Giao diện",
        "group": "Nhóm", "deps": "Phụ thuộc", "unlocks": "Mở khoá", "nodeps": "không phụ thuộc",
        "files": "File", "spec": "mở .md", "generated": "Sinh lúc",
        "derived": "File sinh tự động — đừng sửa. Các file markdown cạnh nó mới là bản gốc; "
                   "trang này được dựng lại từ chúng.",
        "mismatch": "Lệch trạng thái", "notasks": "Bảng task trong PLAN.md chưa có dòng nào.",
        "of": "/", "donelabel": "xong",
        "attention": "Cần chú ý — task từng FAIL hoặc đang tắc",
        "activity": "Diễn biến của task này", "attempts": "lượt chạy",
        "lastfail": "lỗi lần cuối", "colwhen": "lúc", "colaction": "hành động",
        "colagent": "agent", "colnote": "ghi chú", "colstatus": "trạng thái", "coltask": "task",
        "lessons": "Bài học rút từ các lần FAIL — mọi executor sau đều đọc phần này",
        "attention_nav": "Cần chú ý", "lessons_nav": "Bài học",
        "retries": "lượt chạy lại",
    },
}


def pick_lang(plan):
    m = re.search(r"^\s*[-*]\s*Language:\s*(.+)$", plan["raw"], re.M | re.I)
    value = (m.group(1) if m else "").lower()
    if "viet" in value or "việt" in value or value.strip() in ("vi", "vn"):
        return "vi"
    return "en"


def emit(plan, plan_dir, out_path):
    T = STR[pick_lang(plan)]
    tasks = plan["tasks"]
    counts = dict((s, 0) for s in STATUS_ORDER)
    for t in tasks:
        counts[t["status"]] = counts.get(t["status"], 0) + 1
    total = len(tasks) or 1
    unlocks = dict((t["id"], []) for t in tasks)
    for t in tasks:
        for d in t["depends_on"]:
            if d in unlocks:
                unlocks[d].append(t["id"])

    testcases_md = read(os.path.join(plan_dir, "testcases.md"))
    context_md = read(os.path.join(plan_dir, "SYSTEM-CONTEXT.md"))
    progress_md = read(os.path.join(plan_dir, "PROGRESS.md"))
    journal_md, handoff_md = parse_progress(progress_md)
    lessons_body = ""
    for name, body in sections(context_md):
        if "lessons" in name.lower() or "bài học" in name.lower():
            lessons_body = body
    events = parse_journal(journal_md)
    stats = journal_stats(events)
    troubled = [t for t in tasks
                if stats.get(t["id"], {}).get("fails") or stats.get(t["id"], {}).get("blocked")
                or t["status"] == "blocked"]

    p = []
    p.append("<!doctype html><html lang=\"vi\"><head><meta charset=\"utf-8\">")
    p.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    p.append("<title>%s — feature plan</title>" % esc(plan["title"]))
    p.append("<style>%s</style></head><body>" % CSS)
    p.append('<div class="tools"><button id="theme" title="%s">◐</button></div>' % esc(T["theme"]))
    p.append('<div class="wrap">')

    # ---- sidebar
    nav = ['<nav><p class="brand">feature-workflow</p>']
    entries = [("queue", T["queue"], bool(plan["queue"])),
               ("attention", T["attention_nav"], bool(troubled)),
               ("lessons", T["lessons_nav"], bool(lessons_body.strip())),
               ("overview", T["overview"], True),
               ("tasks", T["tasks"], bool(tasks)),
               ("testcases", T["testcases"], bool(testcases_md)),
               ("progress", T["progress"], bool(progress_md)),
               ("context", T["context"], bool(context_md))]
    for anchor, label, show in entries:
        if not show:
            continue
        extra = ""
        if anchor == "tasks":
            extra = '<span class="tag">%d</span>' % len(tasks)
        nav.append('<a class="nl" href="#%s">%s%s</a>' % (anchor, esc(label), extra))
    if tasks:
        nav.append('<p class="grp">%s</p>' % esc(T["tasks"]))
        for t in tasks:
            nav.append('<a class="tl" href="#%s"><i class="dot %s"></i>'
                       '<span class="t">%s · %s</span></a>'
                       % (t["id"], t["status"], esc(t["id"].replace("task-", "")),
                          esc(t["title"] or t["id"])))
    nav.append("</nav>")
    p.append("".join(nav))

    # ---- header
    p.append("<main>")
    p.append('<header><h1>%s</h1><div class="sub">' % esc(plan["title"]))
    p.append('<span class="pill %s">%s</span>' % (
        norm_status(plan["status"]) if plan["status"] in STATUS_LABEL else "todo",
        esc(plan["status"])))
    if plan["drafted"]:
        p.append("<span>%s</span>" % esc(plan["drafted"]))
    p.append("<span>%d %s %s %s</span>" % (counts.get("done", 0), T["of"], len(tasks),
                                           esc(T["donelabel"])))
    reruns = sum(max(0, st["attempts"] - 1) for st in stats.values())
    if reruns:
        p.append('<span class="pill blocked">%d %s</span>' % (reruns, esc(T["retries"])))
    p.append('<span>%s %s</span>' % (esc(T["generated"]),
                                     time.strftime("%Y-%m-%d %H:%M")))
    p.append("</div>")
    if tasks:
        p.append('<div class="bar">')
        for s in STATUS_ORDER:
            if counts.get(s):
                p.append('<i class="seg-%s" style="width:%.4f%%;background:var(--%s)"></i>'
                         % (s, 100.0 * counts[s] / total,
                            {"done": "done", "in-progress": "prog", "todo": "todo",
                             "blocked": "block", "needs-human": "human"}[s]))
        p.append("</div><div class=\"legend\">")
        for s in STATUS_ORDER:
            if counts.get(s):
                p.append('<span class="pill %s">%s %d</span>' % (s, esc(STATUS_LABEL[s]),
                                                                 counts[s]))
        p.append("</div>")
    p.append("</header>")

    # ---- manual verification queue, hoisted when it has real rows
    queue_body = ""
    for name, body in plan["sections"]:
        if "manual verification" in name.lower():
            queue_body = body
    if plan["queue"]:
        p.append('<section id="queue"><div class="card alert"><h3>⚠︎ %s</h3>%s</div></section>'
                 % (esc(T["queue"]), md_to_html(queue_body)))

    # ---- tasks that failed or stalled: the overview that raw journal rows don't give
    if troubled:
        rows = []
        for t in troubled:
            st = stats.get(t["id"], {})
            rows.append([
                '<a href="#%s">%s</a> %s' % (esc(t["id"]), esc(t["id"]),
                                             esc(t["title"] or "")),
                '<span class="pill %s">%s</span>' % (t["status"], esc(STATUS_LABEL[t["status"]])),
                "%d" % st.get("attempts", 0),
                "%d" % st.get("fails", 0),
                inline(st.get("last_fail", "") or "—"),
            ])
        p.append('<section id="attention"><div class="card attn"><h3>⟲ %s</h3>%s</div></section>'
                 % (esc(T["attention"]),
                    html_table([T["coltask"], T["colstatus"], T["attempts"], "FAIL",
                                T["lastfail"]], rows)))

    # ---- lessons learned: hoisted out of SYSTEM-CONTEXT.md because it drives every executor
    if lessons_body.strip():
        p.append('<section id="lessons"><div class="card lesson"><h3>✎ %s</h3>%s</div></section>'
                 % (esc(T["lessons"]), md_to_html(lessons_body)))

    # ---- overview: every PLAN.md section except the two rendered specially
    p.append('<section id="overview"><h2 class="sh">%s</h2><div class="card">'
             % esc(T["overview"]))
    for name, body in plan["sections"]:
        low = name.lower()
        if low.startswith("tasks"):
            continue
        if "manual verification" in low and plan["queue"]:
            continue
        if not name:
            # the preamble already lives in the header card: drop its H1 and Drafted line
            body = re.sub(r"^#\s+.*$", "", body, count=1, flags=re.M)
            body = re.sub(r"^_?\s*Drafted:.*$", "", body, count=1, flags=re.M)
            if not body.strip():
                continue
        else:
            p.append("<h3>%s</h3>" % inline(name))
        p.append(md_to_html(body))
    p.append("</div></section>")

    # ---- tasks
    if tasks:
        p.append('<section id="tasks"><h2 class="sh">%s</h2>' % esc(T["tasks"]))
        lanes = depth_levels(tasks)
        if len(lanes) > 1:
            p.append('<div class="card"><div class="lanes">')
            for idx, lane in enumerate(lanes):
                p.append('<div class="lane"><h4>%s %d</h4>' % (esc(T["group"]), idx + 1))
                for t in lane:
                    p.append('<a href="#%s"><i class="dot %s"></i>%s</a>'
                             % (t["id"], t["status"], esc(t["id"])))
                p.append("</div>")
            p.append("</div></div>")
        p.append('<div class="toolbar"><input id="q" placeholder="%s">'
                 '<button id="expand" data-open="%s" data-close="%s">%s</button></div>'
                 % (esc(T["filter"]), esc(T["expand"]), esc(T["collapse"]), esc(T["expand"])))
        for t in tasks:
            p.append('<details class="task card" id="%s"><summary>' % esc(t["id"]))
            p.append('<span class="tid">%s</span><span class="tt">%s</span>'
                     % (esc(t["id"]), esc(t["title"] or "")))
            p.append('<span class="meta"><span class="pill %s">%s</span>'
                     % (t["status"], esc(STATUS_LABEL[t["status"]])))
            if t.get("repo") and t["repo"] not in ("—", "-", "."):
                p.append('<span class="tag">%s</span>' % esc(t["repo"]))
            if t.get("model"):
                p.append('<span class="tag">%s</span>' % esc(t["model"]))
            if t.get("risk"):
                cls = "tag risk" if t["risk"] == "high" else "tag"
                p.append('<span class="%s">risk: %s</span>' % (cls, esc(t["risk"])))
            if t.get("ui_verify") and t["ui_verify"] not in ("none", "—", "-", ""):
                p.append('<span class="tag ui">ui: %s</span>' % esc(t["ui_verify"]))
            st = stats.get(t["id"], {})
            if st.get("fails"):
                p.append('<span class="tag fail">FAIL ×%d</span>' % st["fails"])
            if st.get("attempts", 0) > 1:
                p.append('<span class="tag">⟲ %d %s</span>' % (st["attempts"],
                                                               esc(T["attempts"])))
            p.append("</span></summary>")
            if t.get("mismatch"):
                p.append('<p class="warn">⚠︎ %s — %s</p>' % (esc(T["mismatch"]),
                                                             inline(t["mismatch"])))
            bits = []
            if t["depends_on"]:
                bits.append("%s: %s" % (esc(T["deps"]), " ".join(
                    '<a href="#%s">%s</a>' % (esc(d), esc(d)) for d in t["depends_on"])))
            else:
                bits.append("%s: <em>%s</em>" % (esc(T["deps"]), esc(T["nodeps"])))
            if unlocks.get(t["id"]):
                bits.append("%s: %s" % (esc(T["unlocks"]), " ".join(
                    '<a href="#%s">%s</a>' % (esc(u), esc(u)) for u in unlocks[t["id"]])))
            files = t.get("fm", {}).get("files") or []
            if isinstance(files, list) and files:
                bits.append("%s: %s" % (esc(T["files"]),
                                        " ".join("<code>%s</code>" % esc(f) for f in files)))
            if t.get("spec"):
                bits.append('<a href="%s">%s ↗</a>' % (esc(t["spec"]), esc(T["spec"])))
            p.append('<p class="deps">%s</p>' % " · ".join(bits))
            if st.get("events"):
                rows = [[esc(e["when"]), action_pill(e["action"]), esc(e["agent"]),
                         inline(e["note"] or "—")] for e in st["events"]]
                p.append('<div class="act"><h4>%s</h4>%s</div>'
                         % (esc(T["activity"]),
                            html_table([T["colwhen"], T["colaction"], T["colagent"],
                                        T["colnote"]], rows)))
            p.append('<div class="body">%s</div>' % md_to_html(t.get("body", "")))
            p.append("</details>")
        p.append("</section>")
    else:
        p.append('<section id="tasks"><h2 class="sh">%s</h2><div class="card"><p>%s</p></div>'
                 "</section>" % (esc(T["tasks"]), esc(T["notasks"])))

    # ---- testcases
    if testcases_md:
        p.append('<section id="testcases"><h2 class="sh">%s</h2><div class="card">%s</div>'
                 "</section>" % (esc(T["testcases"]),
                                 md_to_html(re.sub(r"^#\s+.*$", "", testcases_md, count=1,
                                                   flags=re.M), row_anchor=True)))

    # ---- progress
    if progress_md:
        p.append('<section id="progress"><h2 class="sh">%s</h2>' % esc(T["progress"]))
        if handoff_md:
            p.append('<div class="card"><h3>%s <button id="copy" data-done="%s">%s</button></h3>'
                     % (esc(T["handoff"]), esc(T["copied"]), esc(T["copy"])))
            p.append(md_to_html(handoff_md))
            p.append('<pre id="handoff-src" style="display:none">%s</pre></div>'
                     % esc(handoff_md.strip()))
        p.append('<div class="card">%s</div></section>'
                 % md_to_html(re.sub(r"^#\s+.*$", "", journal_md, count=1, flags=re.M)))

    # ---- system context
    if context_md:
        p.append('<section id="context"><h2 class="sh">%s</h2><div class="card">%s</div>'
                 "</section>" % (esc(T["context"]),
                                 md_to_html(re.sub(r"^#\s+.*$", "", context_md, count=1,
                                                   flags=re.M))))

    p.append('<p class="foot">%s</p>' % esc(T["derived"]))
    p.append("</main></div><script>%s</script></body></html>" % JS)

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("".join(p))
    return out_path


def resolve_plan_dir(target):
    target = os.path.abspath(target)
    if os.path.isfile(target):
        target = os.path.dirname(target)
    for _ in range(4):
        if os.path.isfile(os.path.join(target, "PLAN.md")):
            return target
        parent = os.path.dirname(target)
        if parent == target:
            break
        target = parent
    return None


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    quiet = "--quiet" in argv
    out = None
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 < len(argv):
            out = argv[i + 1]
            args = [a for a in args if a != out]
    if not args:
        sys.stderr.write("usage: render-dashboard.py <plan-dir|file inside it> "
                         "[--out PATH] [--quiet]\n")
        return 2
    plan_dir = resolve_plan_dir(args[0])
    targets = [plan_dir] if plan_dir else []
    if not plan_dir and os.path.isdir(args[0]):
        # a plans root: render every feature under it
        base = os.path.abspath(args[0])
        targets = [os.path.join(base, d) for d in sorted(os.listdir(base))
                   if os.path.isfile(os.path.join(base, d, "PLAN.md"))]
    if not targets:
        if not quiet:
            sys.stderr.write("render-dashboard: no PLAN.md at or under %s — nothing to do\n"
                             % args[0])
        return 0
    for target in targets:
        plan = parse_plan(target)
        if plan is None:
            continue
        attach_specs(plan, target)
        path = emit(plan, target, out or os.path.join(target, "dashboard.html"))
        if not quiet:
            print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

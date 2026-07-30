#!/usr/bin/env python3
"""Claude Code status -> GeekMagic SmallTV monitor (SD_RU firmware).

This firmware has no text/DIY-Text API, so we render a 240x240 GIF with
Pillow and push it into the device's Photo album. The device runs in
"dedicated status display" mode: Photo theme active, agent_status.gif the
sole enabled photo.

Driven by Claude Code hooks (reads the hook JSON object from stdin).

  agent_glance.py                          # hook mode: dispatch on hook_event_name
  agent_glance.py --ip $AGENT_GLANCE_IP     # set device IP (persisted)
  agent_glance.py --setup                  # take over device (backup + Photo-only)
  agent_glance.py --restore               # revert device to pre-setup state
  agent_glance.py --test working|waiting|done [subtitle]
  agent_glance.py --flush-queue           # (internal) detached worker: debounce + single upload
"""
import sys, os, json, time, mimetypes, uuid, subprocess, glob, re
import urllib.request, urllib.parse, urllib.error
from contextlib import contextmanager
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Persistent state lives in a stable user dir (NOT the install/plugin dir,
# which is ephemeral). IP/limit come from env vars first; config.json is an
# optional local fallback.
STATE_DIR = os.path.expanduser("~/.agent-glance")
os.makedirs(STATE_DIR, exist_ok=True)
CONFIG_PATH = os.path.join(STATE_DIR, "config.json")
BACKUP_PATH = os.path.join(STATE_DIR, "device_backup.json")

# Cross-platform scratch dir (use tempfile on Windows; /tmp elsewhere).
TMP_DIR = os.environ.get("TEMP") or "/tmp"
TMP_GIF = os.path.join(TMP_DIR, "agent_status.gif")
THROTTLE_PATH = os.path.join(TMP_DIR, "agent_glance_last.json")
ERRLOG = os.path.join(TMP_DIR, "agent_glance_error.log")
# Race-resolution state: events from independent hook processes land here, a
# single detached worker drains them under a device lock so only the
# highest-priority, latest state reaches the device.
QUEUE_PATH = os.path.join(TMP_DIR, "agent_glance_queue.jsonl")
LOCK_DIR = os.path.join(TMP_DIR, "agent_glance_upload.lock")
DEBOUNCE_SEC = 0.6   # window to coalesce competing events (Stop vs Notification)
QUEUE_TTL = 30       # drop queue entries older than this (crash-recovery GC)

STATUS_FILE = "agent_status.gif"     # fixed name -> overwrites itself (bounded flash use)
PHOTO_THEME_ID = 2                # "Фото" theme on SD_RU firmware
THROTTLE_SEC = 8                  # skip re-push of identical state within this window

# State precedence: when competing events coalesce in the debounce window, the
# highest-priority one wins (ties broken by recency). `done` outranks a late
# `waiting` so the screen never flips back to APPROVAL after a Stop.
STATE_PRIORITY = {"done": 3, "working": 2, "waiting": 1}


# ---------------------------------------------------------------- config / http
def load_config():
    # Env vars take precedence (portable across machines + plugin installs);
    # config.json is an optional local fallback for the personal setup.
    cfg = {"ip": "", "context_limit": 200000}
    if os.path.exists(CONFIG_PATH):
        try:
            cfg.update(json.load(open(CONFIG_PATH)))
        except Exception:
            pass
    if os.environ.get("AGENT_GLANCE_IP"):
        cfg["ip"] = os.environ["AGENT_GLANCE_IP"]
    if os.environ.get("AGENT_GLANCE_CONTEXT_LIMIT"):
        try:
            cfg["context_limit"] = int(os.environ["AGENT_GLANCE_CONTEXT_LIMIT"])
        except Exception:
            pass
    return cfg


def base_url():
    ip = load_config().get("ip")
    if not ip:
        raise RuntimeError("no device IP set (run: agent_glance.py --ip <IP>)")
    return "http://" + ip.replace("http://", "").rstrip("/")


def _get(path, timeout=4):
    return urllib.request.urlopen(urllib.request.Request(base_url() + path), timeout=timeout).read()


def _get_status(path, timeout=4):
    """Like _get but returns the HTTP status instead of raising on 4xx.

    The firmware answers 403 when a disable would leave zero themes/photos
    enabled (anti-blank-screen guard). We treat that as soft, not fatal.
    """
    try:
        urllib.request.urlopen(urllib.request.Request(base_url() + path), timeout=timeout)
        return 200
    except urllib.error.HTTPError as e:
        return e.code


def _post_multipart(path, field, filepath, timeout=10):
    boundary = "----cc" + uuid.uuid4().hex
    data = open(filepath, "rb").read()
    mime = mimetypes.guess_type(filepath)[0] or "application/octet-stream"
    body = (
        f"--{boundary}\r\n".encode()
        + f'Content-Disposition: form-data; name="{field}"; filename="{os.path.basename(filepath)}"\r\n'.encode()
        + f"Content-Type: {mime}\r\n\r\n".encode()
        + data
        + f"\r\n--{boundary}--\r\n".encode()
    )
    req = urllib.request.Request(
        base_url() + path, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    return urllib.request.urlopen(req, timeout=timeout).read()


def photo_list():
    return json.loads(_get("/photo/list"))


def theme_list():
    return json.loads(_get("/theme/list"))


def _upload_with_retry(path, field, filepath, retries=3, delay=0.8):
    """Upload, retrying on transient failures (the ESP8266 returns 403/5xx
    when busy handling a previous request)."""
    last = None
    for _ in range(retries):
        try:
            return _post_multipart(path, field, filepath)
        except Exception as e:
            last = e
            time.sleep(delay)
    raise last


def set_photo_enabled(name, state):
    return _get_status("/photo/toggle?" + urllib.parse.urlencode({"name": name, "state": "1" if state else "0"}))


def set_theme_enabled(tid, state):
    return _get_status("/theme/toggle?" + urllib.parse.urlencode({"id": tid, "state": "1" if state else "0"}))


# ---------------------------------------------------------------- race resolution
# Each host fires every hook event in its OWN process, so events can't share
# in-process state. We serialize device access across processes: events land in
# a queue file, a single detached worker drains them under a directory-based
# lock (mkdir is atomic on every OS — no flock/msvcrt needed) and pushes only
# the winning state. This kills the "done screen overwritten by a late
# APPROVAL notification" race.
def _pid_alive(pid):
    """True if `pid` is an existing process. Best-effort, cross-platform."""
    if not pid:
        return False
    try:
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes
            k32 = ctypes.windll.kernel32
            SYNCHRONIZE = 0x00100000
            h = k32.OpenProcess(SYNCHRONIZE, False, int(pid))
            if not h:
                return False
            k32.CloseHandle(h)
            return True
        else:
            os.kill(int(pid), 0)
            return True
    except Exception:
        return False


@contextmanager
def _device_lock(timeout=8.0):
    """Serialize device access via atomic directory creation.

    Stale locks (owner crashed) are reclaimed after the deadline: the lock dir
    holds a pidfile so we can confirm the owner is dead before taking over.
    """
    pidfile = os.path.join(LOCK_DIR, "owner.pid")
    deadline = time.time() + timeout
    acquired = False
    while True:
        try:
            os.mkdir(LOCK_DIR)
            acquired = True
            try:
                with open(pidfile, "w") as fh:
                    fh.write(str(os.getpid()))
            except Exception:
                pass
            break
        except FileExistsError:
            if time.time() > deadline:
                # Possibly stale — verify owner, then force-clear if dead.
                owner = None
                try:
                    with open(pidfile) as fh:
                        owner = fh.read().strip()
                except Exception:
                    pass
                if owner and _pid_alive(owner):
                    # Owner is live but slow; extend and keep waiting a bit.
                    deadline = time.time() + 2.0
                    time.sleep(0.2)
                    continue
                # Owner gone (or unreadable) -> reclaim stale lock.
                try:
                    os.remove(pidfile)
                except Exception:
                    pass
                try:
                    os.rmdir(LOCK_DIR)
                except Exception:
                    pass
                continue
            time.sleep(0.15)
    try:
        yield
    finally:
        if acquired:
            try:
                os.remove(pidfile)
            except Exception:
                pass
            try:
                os.rmdir(LOCK_DIR)
            except Exception:
                pass


def _enqueue(entry):
    """Append an event to the cross-process queue. One-line JSON per entry."""
    with open(QUEUE_PATH, "a") as fh:
        fh.write(json.dumps(entry) + "\n")


def _drain_queue():
    """Read+clear the queue. Caller must hold _device_lock."""
    entries = []
    if os.path.exists(QUEUE_PATH):
        try:
            with open(QUEUE_PATH) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        continue
            os.remove(QUEUE_PATH)
        except FileNotFoundError:
            pass  # another worker already drained — that's fine
    # Garbage-collect stale entries (crash recovery).
    now = time.time()
    return [e for e in entries if now - e.get("ts", now) < QUEUE_TTL]


def _resolve_state_key(ev, data):
    """Map an event to a display state, or None if it shouldn't update."""
    if ev in ("Notification", "PermissionRequest"):
        return "waiting"
    if ev in ("PreToolUse",):
        tool = (data.get("toolCall") or {}).get("name") or data.get("tool_name") or data.get("tool") or ""
        if tool == "ask_permission":
            return "waiting"
        return "working"
    return EVENT_STATE.get(ev)


def _resolve(entries):
    """Pick the winning entry: most recent timestamp/seq wins, using priority as tiebreaker."""
    if not entries:
        return None
    return max(entries, key=lambda e: (
        e.get("ts", 0),
        e.get("seq", 0),
        STATE_PRIORITY.get(e.get("state"), 0),
    ))


def _next_seq():
    """Monotonic tiebreaker across processes: microsecond clock + pid."""
    return (time.time(), os.getpid())


# ---------------------------------------------------------------- rendering
def _font(size, bold=True, cjk=False):
    # cjk=True -> prefer a Korean(+Latin) font so Hangul renders instead of tofu.
    if cjk:
        cands = [
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ]
    else:
        cands = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold
            else "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    for p in cands:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


# bg, label color, accent/dot, big word, subtitle default
STATES = {
    "working": dict(bg=(22, 34, 64),   fg=(255, 209, 102), label="WORKING",  sub="processing…",     pulse=True),
    "waiting": dict(bg=(150, 27, 27),  fg=(255, 255, 255), label="APPROVAL", sub="needs your input", pulse=False),
    "done":    dict(bg=(20, 62, 49),   fg=(120, 230, 150), label="DONE",     sub="idle — ready",     pulse=False),
}


def _wrap(text, font, max_w, draw, max_lines=2):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        trial = cur + ch
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines[:max_lines]


def detect_host():
    """Which agent is driving us, for the footer label.

    Each host runs the script out of its own install tree, so the path is a
    more reliable signal than env vars or event names (UserPromptSubmit and
    Stop are shared between Claude Code and Codex).
    """
    p = os.path.abspath(__file__)
    for frag, label in (
        ("/.claude/plugins/", "claude code"),
        ("/.codex/plugins/", "codex"),
        ("/.gemini/", "antigravity"),
        ("/.hermes/", "hermes"),
    ):
        if frag in p:
            return label

    # Not running from an install tree (e.g. a dev checkout). Fall back to
    # markers the host sets at runtime.
    #
    # Only runtime-exclusive names are safe here: users commonly export
    # HERMES_*/GEMINI_* API keys in their shell profile, so matching on those
    # prefixes would mislabel every session.
    if os.environ.get("CLAUDECODE") or os.environ.get("CLAUDE_PLUGIN_ROOT"):
        return "claude code"
    if os.environ.get("CODEX_SANDBOX") or os.environ.get("CODEX_HOME"):
        return "codex"
    return "agent"


def project_name(cwd=None):
    """Project label = basename of the session's working directory."""
    try:
        p = os.path.abspath(cwd or os.getcwd())
        return os.path.basename(p.rstrip("/")) or "-"
    except Exception:
        return "-"


def _fmt(n):
    n = int(n or 0)
    if n >= 1_000_000:
        return "{:.1f}M".format(n / 1_000_000)
    if n >= 1000:
        return "{}k".format(n // 1000)
    return str(n)


MODEL_LIMIT_PATTERNS = [
    (r"gemini-?2\.[59]-?pro|gemini-?1\.5-?pro|gemini-?2-?pro", 2_000_000),
    (r"gemini", 1_000_000),
    (r"claude", 200_000),
    (r"gpt-4|codex|deepseek|qwen", 128_000),
    (r"o1|o3", 200_000),
]


def resolve_model_context_limit(model_name, fallback_limit=200000):
    if not model_name or model_name == "-":
        return fallback_limit
    m = str(model_name).lower().strip()
    for pattern, limit in MODEL_LIMIT_PATTERNS:
        if re.search(pattern, m):
            return limit
    return fallback_limit


def _estimate_tokens(text):
    if not text:
        return 0
    return max(1, int(len(str(text)) / 3.5))


def git_branch(cwd=None):
    try:
        p = cwd or os.getcwd()
        res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=p, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=1)
        if res.returncode == 0:
            b = res.stdout.strip()
            if b and b != "HEAD":
                return b
    except Exception:
        pass
    return None


def estimate_cost(model, cum_in, cum_out):
    m = (model or "").lower()
    if "flash" in m or "mini" in m:
        in_p, out_p = 0.15, 0.60
    elif "pro" in m or "sonnet" in m or "gpt-4" in m or "claude" in m:
        in_p, out_p = 2.50, 10.00
    elif "opus" in m:
        in_p, out_p = 15.00, 75.00
    else:
        in_p, out_p = 0.50, 1.50
    return (cum_in * in_p + cum_out * out_p) / 1_000_000


def format_duration(sec):
    sec = int(sec or 0)
    if sec < 60:
        return f"{sec}s"
    m = sec // 60
    s = sec % 60
    if m < 60:
        return f"{m}m {s}s"
    h = m // 60
    m = m % 60
    return f"{h}h {m}m"


def parse_iso_ts(ts_str):
    if not ts_str:
        return None
    try:
        ts_str = str(ts_str).rstrip("Z").split(".")[0]
        return time.mktime(time.strptime(ts_str, "%Y-%m-%dT%H:%M:%S"))
    except Exception:
        return None


def parse_transcript(path=None):
    """Pull model + token usage + duration + cost from session transcript JSONL across hosts."""
    fallback_limit = load_config().get("context_limit", 200000)
    info = {
        "model": "-",
        "ctx": 0,
        "cum_in": 0,
        "cum_out": 0,
        "total": 0,
        "cost": 0.0,
        "duration": "0s",
        "subagents": 0,
        "compacted": False,
        "limit": fallback_limit,
    }

    if not path or not os.path.exists(path):
        candidates = []
        candidates.extend(glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")))
        candidates.extend(glob.glob(os.path.expanduser("~/.gemini/antigravity-cli/brain/*/.system_generated/logs/transcript.jsonl")))
        candidates.extend(glob.glob(os.path.expanduser("~/.codex/sessions/*/*.jsonl")))
        candidates.extend(glob.glob(os.path.expanduser("~/.codex/*/*.jsonl")))
        if candidates:
            candidates.sort(key=os.path.getmtime)
            path = candidates[-1]
        else:
            return info

    if not os.path.exists(path):
        return info

    is_agy = "antigravity-cli" in path or ".system_generated" in path
    peak_in = 0
    last_u = None
    start_ts = None
    latest_ts = None
    subagents = 0

    try:
        with open(path, errors="ignore") as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except Exception:
                    continue

                ts = parse_iso_ts(o.get("created_at") or o.get("timestamp"))
                if ts:
                    if start_ts is None or ts < start_ts:
                        start_ts = ts
                    if latest_ts is None or ts > latest_ts:
                        latest_ts = ts

                if is_agy:
                    stype = o.get("type", "")
                    source = o.get("source", "")
                    content = o.get("content", "") or ""
                    thinking = o.get("thinking", "") or ""
                    tool_calls = json.dumps(o.get("tool_calls", [])) if o.get("tool_calls") else ""

                    if "invoke_subagent" in tool_calls or "invoke_subagent" in content:
                        subagents += 1

                    if "Model Selection" in content:
                        for line_c in content.splitlines():
                            if "Model Selection" in line_c:
                                parts = line_c.split("to ")
                                if len(parts) > 1:
                                    info["model"] = parts[1].split(".")[0].strip()

                    if stype == "CHECKPOINT" or "{{ CHECKPOINT" in content:
                        info["compacted"] = True
                        info["ctx"] = _estimate_tokens(content)
                        continue

                    in_tok = 0
                    out_tok = 0
                    if source == "MODEL":
                        out_tok = _estimate_tokens(thinking) + _estimate_tokens(content) + _estimate_tokens(tool_calls)
                    else:
                        in_tok = _estimate_tokens(content)

                    info["cum_in"] += in_tok
                    info["cum_out"] += out_tok
                    info["ctx"] += (in_tok + out_tok)
                else:
                    m = o.get("message") or {}
                    if m.get("role") != "assistant":
                        continue
                    u = m.get("usage")
                    if not u:
                        continue
                    last_u = u
                    info["model"] = m.get("model", info["model"])
                    in_side = (u.get("input_tokens", 0)
                               + u.get("cache_read_input_tokens", 0)
                               + u.get("cache_creation_input_tokens", 0))
                    out_side = u.get("output_tokens", 0)
                    info["cum_in"] += in_side
                    info["cum_out"] += out_side

                    if peak_in > 10000 and in_side < peak_in * 0.75:
                        info["compacted"] = True
                    if in_side > peak_in:
                        peak_in = in_side
    except Exception:
        pass

    if not is_agy and last_u:
        info["ctx"] = (last_u.get("input_tokens", 0)
                       + last_u.get("cache_read_input_tokens", 0)
                       + last_u.get("cache_creation_input_tokens", 0))

    if info["model"] == "-" and is_agy:
        info["model"] = "Gemini 3.6 Flash"

    if start_ts and latest_ts and latest_ts >= start_ts:
        info["duration"] = format_duration(latest_ts - start_ts)
    else:
        info["duration"] = "0s"

    info["total"] = info["cum_in"] + info["cum_out"]
    info["cost"] = estimate_cost(info["model"], info["cum_in"], info["cum_out"])
    info["subagents"] = subagents
    info["limit"] = resolve_model_context_limit(info["model"], fallback_limit)
    return info


def _foot_str(d, host, proj, font, max_w):
    """"<project> · <host>", project truncated so the pair always fits max_w."""
    while proj and d.textlength("{} · {}".format(proj, host), font=font) > max_w:
        proj = proj[:-1]
    return "{} · {}".format(proj, host) if proj else host


def get_context_tier_color(pct):
    """4-tier dynamic color scheme for context window fill:
    - 0% ~ 49%: Normal / Safe (Mint Green)
    - 50% ~ 74%: Moderate Usage (Golden Yellow)
    - 75% ~ 89%: High Usage (Warning Orange)
    - 90% ~ 100%: Critical / Danger (Alert Red)
    """
    if pct >= 90:
        return (255, 75, 75)
    elif pct >= 75:
        return (255, 140, 40)
    elif pct >= 50:
        return (255, 205, 70)
    else:
        return (120, 230, 160)


def render(state, sub=None, info=None, out=TMP_GIF):
    s = STATES.get(state, STATES["working"])
    info = info or {}
    W = H = 240
    img = Image.new("RGB", (W, H), s["bg"])
    d = ImageDraw.Draw(img)
    cx = W // 2

    d.rectangle([0, 0, W, 6], fill=s["fg"])              # top accent bar

    # ---- header: project · branch · host (top, bold) ----
    host = detect_host()
    proj = info.get("project") or project_name()
    branch = info.get("branch") or git_branch()

    if branch:
        head_str = "{} · {}".format(proj, branch)
    else:
        head_str = "{} · {}".format(proj, host)

    fhead = _font(16, True, cjk=True)
    head_str = _foot_str(d, host, head_str, fhead, 216)
    d.text((cx, 24), head_str, font=fhead, fill=(240, 240, 240), anchor="mm")
    d.line([(14, 38), (226, 38)], fill=s["fg"], width=1)  # divider under header

    # ---- status: dot + label inline on one row ----
    flab = _font(24, True)
    label_w = d.textlength(s["label"], font=flab)
    dot_r = 5
    gap = 14
    row_w = dot_r * 2 + gap + label_w
    rx = cx - row_w / 2
    dot_cx = rx + dot_r
    status_y = 60
    d.ellipse([dot_cx - dot_r, status_y - dot_r, dot_cx + dot_r, status_y + dot_r], fill=s["fg"])
    if s["pulse"]:
        d.ellipse([dot_cx - dot_r - 4, status_y - dot_r - 4,
                   dot_cx + dot_r + 4, status_y + dot_r + 4], outline=s["fg"], width=2)
    d.text((dot_cx + dot_r + gap, status_y), s["label"], font=flab, fill=s["fg"], anchor="lm")

    sub = (sub or "").strip() or s["sub"]
    fsub = _font(16, cjk=True)
    y = 90                                      # margin below the status row
    for ln in _wrap(sub, fsub, 200, d, max_lines=3):
        d.text((cx, y), ln, font=fsub, fill=(225, 225, 225), anchor="mm")
        y += 20

    # ---- metrics block ----
    limit = info.get("limit") or resolve_model_context_limit(info.get("model"), load_config().get("context_limit", 200000))
    ctx = info.get("ctx", 0)
    pct = min(100, round(ctx / limit * 100)) if limit else 0
    compacted = info.get("compacted", False)
    tier_color = get_context_tier_color(pct)

    # Divider capping metrics block
    d.line([(14, 154), (226, 154)], fill=s["fg"], width=1)

    # Model [Limit] (left) + Context % (right)
    limit_fmt = _fmt(limit)
    model_str = info.get("model", "-")
    model_tag = "{} [{}]".format(model_str, limit_fmt) if limit_fmt else model_str
    pct_str = "{}%".format(pct)

    d.text((14, 170), model_tag, font=_font(13, True), fill=(215, 215, 215), anchor="lm")
    d.text((226, 170), pct_str, font=_font(14, True), fill=tier_color, anchor="rm")

    # Context usage bar
    d.rectangle([14, 186, 226, 193], fill=(60, 60, 60))
    if pct > 0:
        d.rectangle([14, 186, 14 + int(212 * pct / 100), 193], fill=tier_color)

    # Token & Cost row
    ftn = _font(11, False)
    in_str = _fmt(info.get("cum_in", 0))
    out_str = _fmt(info.get("cum_out", 0))
    tot_str = _fmt(info.get("total", 0))
    cost_val = info.get("cost", 0.0)
    cost_str = "${:.2f}".format(cost_val) if cost_val > 0 else "$0.00"

    tok_label = "in:{} out:{} tot:{}".format(in_str, out_str, tot_str)
    d.text((14, 208), tok_label, font=ftn, fill=(200, 200, 200), anchor="lm")
    d.text((226, 208), cost_str, font=_font(11, True), fill=(255, 210, 80), anchor="rm")

    # Session Duration & Subagents row
    dur_str = "⏱ {}".format(info.get("duration", "0s"))
    subs = info.get("subagents", 0)
    sub_str = "← {} agent{}".format(subs, "s" if subs != 1 else "") if subs > 0 else host

    d.text((14, 226), dur_str, font=_font(11, True, True), fill=(180, 180, 180), anchor="lm")
    d.text((226, 226), sub_str, font=ftn, fill=(180, 180, 180), anchor="rm")

    img.save(out, "GIF")
    return out


# ---------------------------------------------------------------- push / lifecycle
def _trim(text, n=40):
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def push_state(state, sub=None, info=None):
    """Render + upload a state. Throttles identical re-pushes to spare flash."""
    key = "{}|{}".format(state, sub or "")
    now = time.time()
    try:
        if os.path.exists(THROTTLE_PATH):
            prev = json.load(open(THROTTLE_PATH))
            prev_key = prev.get("key", "")
            prev_state = prev_key.split("|")[0] if "|" in prev_key else ""
            # Only throttle if the state AND subtitle are identical. State transitions ALWAYS push!
            if prev_state == state and prev_key == key and now - prev.get("t", 0) < THROTTLE_SEC:
                return False  # identical state pushed recently -> skip
    except Exception:
        pass

    gif = render(state, sub, info)
    _upload_with_retry("/photo/upload", "file", gif)
    set_photo_enabled(STATUS_FILE, True)
    json.dump({"key": key, "t": now}, open(THROTTLE_PATH, "w"))
    return True


# ---------------------------------------------------------------- background worker
def _flush_worker():
    """Detached: wait out the debounce window, then push ONE winning state.

    Runs without blocking the hook caller. Under _device_lock it drains the
    queue so only a single render+upload happens per coalesced burst.
    """
    time.sleep(DEBOUNCE_SEC)
    try:
        with _device_lock():
            entries = _drain_queue()
            if not entries:
                return
            final = _resolve(entries)
            if not final:
                return
            push_state(final["state"], final.get("sub"), final.get("info"))
    except Exception as e:
        try:
            with open(ERRLOG, "a") as fh:
                fh.write("{} flush: {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S"), e))
        except Exception:
            pass


def _unix_detach(fn):
    """Fork a child that runs fn detached, so the hook caller returns at once."""
    pid = os.fork()
    if pid != 0:
        return                 # parent returns immediately
    os.setsid()
    try:
        _devnull_stdio()
        fn()
    except Exception:
        pass
    os._exit(0)


def _win_detach_flush():
    """Windows: re-exec ourselves detached with --flush-queue.

    os.fork doesn't exist on Windows, and a daemon thread dies when the hook
    process exits. A detached subprocess survives to complete the upload.
    """
    flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
    DETACHED = 0x00000008
    creationflags = flags | DETACHED
    try:
        subprocess.Popen(
            [sys.executable, os.path.abspath(__file__), "--flush-queue"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, close_fds=True,
            creationflags=creationflags,
        )
    except Exception as e:
        try:
            with open(ERRLOG, "a") as fh:
                fh.write("{} win_spawn: {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S"), e))
        except Exception:
            pass


def _spawn_flush():
    """Launch the detached flush worker in a platform-appropriate way."""
    if sys.platform == "win32":
        _win_detach_flush()
    else:
        _unix_detach(_flush_worker)


def setup():
    if not load_config().get("ip"):
        raise RuntimeError("set IP first: agent_glance.py --ip <IP>")

    backup = {
        "themes": {t["id"]: t["enabled"] for t in theme_list()["themes"]},
        "photos": {f["name"]: f["enabled"] for f in photo_list()["files"]},
    }
    json.dump(backup, open(BACKUP_PATH, "w"), indent=2)

    # initial screen
    render("done", "monitor ready")
    _upload_with_retry("/photo/upload", "file", TMP_GIF)

    # make agent_status.gif the sole enabled photo (it's already uploaded above)
    set_photo_enabled(STATUS_FILE, True)
    time.sleep(0.3)
    for f in photo_list()["files"]:
        if f["name"] != STATUS_FILE:
            set_photo_enabled(f["name"], False)
            time.sleep(0.25)

    # Photo theme = sole active theme. Enable the target FIRST so the device
    # never sees zero enabled themes (which it rejects with HTTP 403), then
    # disable the rest. Pauses let the ESP8266 process each request.
    set_theme_enabled(PHOTO_THEME_ID, True)
    time.sleep(0.4)
    for t in theme_list()["themes"]:
        if t["id"] != PHOTO_THEME_ID:
            set_theme_enabled(t["id"], False)
            time.sleep(0.3)

    enabled = [t["id"] for t in theme_list()["themes"] if t["enabled"]]
    print("setup complete — device is now a Claude status display")
    print("active theme id:", enabled, "(want [%d])" % PHOTO_THEME_ID)
    print("restore later with: agent_glance.py --restore")


def restore():
    if not os.path.exists(BACKUP_PATH):
        raise RuntimeError("no backup found at " + BACKUP_PATH)
    b = json.load(open(BACKUP_PATH))
    for tid, en in b["themes"].items():
        set_theme_enabled(int(tid), en)
    for name, en in b["photos"].items():
        set_photo_enabled(name, en)
    try:
        _get("/photo/delete?" + urllib.parse.urlencode({"name": STATUS_FILE}))
    except Exception:
        pass
    print("restored — device back to its original themes/photos")


# ---------------------------------------------------------------- hook dispatch
def _devnull_stdio():
    dn = os.open(os.devnull, os.O_RDWR)
    for fd in (0, 1, 2):
        try:
            os.dup2(dn, fd)
        except Exception:
            pass


                                                                    # -- host event maps
# Claude Code and Codex send snake_case `hook_event_name`; Antigravity (agy)
# sends camelCase `hookEventName` and only supports 5 events (no
# UserPromptSubmit, no Notification). Codex has no Notification either — its
# approval event is PermissionRequest.
EVENT_STATE = {
    "UserPromptSubmit":  "working",   # claude, codex
    "PreInvocation":     "working",   # agy
    "Notification":      "waiting",   # claude
    "PermissionRequest": "waiting",   # codex
    "PreToolUse":        "working",   # claude, codex, agy
    "PostToolUse":       "working",   # claude, codex, agy
    "Stop":              "done",      # claude, codex, agy
    "SubagentStop":      "done",      # claude, codex
}


def _norm_event(data):
    """Return (event, transcript_path) across host payload conventions."""
    ev = data.get("hook_event_name") or data.get("hookEventName") or ""
    tp = data.get("transcript_path") or data.get("transcriptPath") or ""
    # agy (Antigravity) does NOT send an event-name key on stdin — it tells the
    # event apart by which payload field is present. Infer it here so hooks fire.
    if not ev and detect_host() == "antigravity":
        if "toolCall" in data or "stepIdx" in data:
            ev = "PreToolUse"
        elif "invocationNum" in data or "initialNumSteps" in data:
            ev = "PreInvocation"
        elif "executionNum" in data or "terminationReason" in data or "fullyIdle" in data:
            ev = "Stop"
    return ev, tp


def _subtitle_for(ev, data):
    if ev in ("UserPromptSubmit",):
        return _trim(data.get("prompt") or data.get("user_prompt") or "", 38)
    if ev in ("Notification",):
        return _trim(data.get("message") or "approval requested", 38)
    if ev == "PermissionRequest":
        return _trim(data.get("tool_name") or "approval needed", 38)
    if ev in ("PreToolUse", "PostToolUse"):
        tool = (data.get("toolCall") or {}).get("name") or data.get("tool_name") or data.get("tool") or ""
        if tool == "ask_permission":
            return _trim("approval requested", 38)
        return _trim(tool or "executing tool…", 38)
    return None


# agy runs hooks synchronously and parses stdout as a per-event result. Each
# event has its own contract; emit the minimal no-op payload so agy is satisfied
# (we never inject steps, block a tool, or force the loop to continue).
AGY_CONTRACT = {
    "PreInvocation":  {"injectSteps": []},
    "PostInvocation": {"injectSteps": [], "terminationBehavior": ""},
    "PreToolUse":     {"decision": "allow"},
    "PostToolUse":    {},
    "Stop":           {"decision": ""},   # non-"continue" lets the agent stop
}


def _maybe_emit_agy_contract(ev):
    """agy parses stdout as the event's result; emit the contract so it is
    satisfied. Claude Code/Codex ignore stdout on these status hooks."""
    if detect_host() == "antigravity":
        sys.stdout.write(json.dumps(AGY_CONTRACT.get(ev, {})))


def _build_info(data, tp):
    """Assemble the metrics block pushed with a state (model/tokens/project)."""
    info = parse_transcript(tp)
    # claude/codex send `cwd`; agy sends `workspacePaths`
    cwd = data.get("cwd") or (data.get("workspacePaths") or [None])[0]
    info["project"] = project_name(cwd)
    return info


def handle_hook():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}
    ev, tp = _norm_event(data)

    state = _resolve_state_key(ev, data)
    if state is None:
        # Even ignored events must answer agy's output contract.
        _maybe_emit_agy_contract(ev)
        return

    # Enqueue and let a single detached worker coalesce competing events under
    # a device lock, so the screen reflects the highest-priority, latest state.
    entry = {
        "state": state,
        "sub": _subtitle_for(ev, data),
        "info": _build_info(data, tp),
        "ts": time.time(),
        "seq": _next_seq(),
        "priority": STATE_PRIORITY.get(state, 0),
    }
    _enqueue(entry)
    _maybe_emit_agy_contract(ev)
    _spawn_flush()          # detached — caller returns immediately


def main():
    args = sys.argv[1:]
    if not args:
        handle_hook()
        return
    a = args[0]
    if a == "--ip" and len(args) > 1:
        cfg = load_config()
        cfg["ip"] = args[1]
        json.dump(cfg, open(CONFIG_PATH, "w"), indent=2)
        print("device IP saved:", args[1])
    elif a == "--setup":
        setup()
    elif a == "--restore":
        restore()
    elif a == "--test":
        info = parse_transcript(None)
        push_state(args[1] if len(args) > 1 else "working",
                   args[2] if len(args) > 2 else None, info)
        print("pushed:", args[1] if len(args) > 1 else "working")
    elif a == "--flush-queue":
        # Internal detached worker entry point (Windows): debounce + single
        # upload. On Unix this is reached only if invoked directly.
        _flush_worker()
    else:
        print(__doc__)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        try:
            with open(ERRLOG, "a") as fh:
                fh.write("{} {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S"), e))
        except Exception:
            pass
    sys.exit(0)  # never block the hook

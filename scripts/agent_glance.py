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
import sys, os, json, time, mimetypes, uuid, subprocess, glob, re, math
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

# Frame geometry (rendered output is always 240x240).
W = H = 240
CX = W // 2

# GIF mode: per-host character GIFs, composited into the middle of the chrome.
USER_GIF_DIR = os.path.join(STATE_DIR, "gifs")           # ~/.agent-glance/gifs
USER_HOSTS_DIR = os.path.join(USER_GIF_DIR, "hosts")     # user overrides (precedence)
USER_ANIME_DIR = os.path.join(USER_GIF_DIR, "anime")
BUNDLED_HOSTS_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "assets", "hosts"))
_MAX_FRAMES = 16      # bound output size / decode time / flash wear
_MIN_FRAME_MS = 50    # floor; below this the device stutters

# State precedence: when competing events coalesce in the debounce window, the
# highest-priority one wins (ties broken by recency). `done` outranks a late
# `waiting` so the screen never flips back to APPROVAL after a Stop.
STATE_PRIORITY = {"done": 3, "working": 2, "waiting": 1}


# ---------------------------------------------------------------- config / http
def load_config():
    # Env vars take precedence (portable across machines + plugin installs);
    # config.json is an optional local fallback for the personal setup.
    cfg = {"ip": "", "context_limit": 200000,
           "display": {"preset": "default", "layout": "frame", "gifs": {}}}
    if os.path.exists(CONFIG_PATH):
        try:
            cfg.update(json.load(open(CONFIG_PATH)))
        except Exception:
            pass
    # Shallow cfg.update can replace the whole "display" dict; normalize so the
    # nested keys always exist with sane defaults.
    d = cfg.get("display")
    if not isinstance(d, dict):
        d = {}
    d.setdefault("preset", "default")
    d.setdefault("layout", "frame")
    d.setdefault("gifs", {})
    cfg["display"] = d
    if os.environ.get("AGENT_GLANCE_IP"):
        cfg["ip"] = os.environ["AGENT_GLANCE_IP"]
    if os.environ.get("AGENT_GLANCE_CONTEXT_LIMIT"):
        try:
            cfg["context_limit"] = int(os.environ["AGENT_GLANCE_CONTEXT_LIMIT"])
        except Exception:
            pass
    if os.environ.get("AGENT_GLANCE_PRESET"):
        cfg["display"]["preset"] = os.environ["AGENT_GLANCE_PRESET"].strip().lower()
    if os.environ.get("AGENT_GLANCE_LAYOUT"):
        cfg["display"]["layout"] = os.environ["AGENT_GLANCE_LAYOUT"].strip().lower()
    return cfg


def _host_filename(host):
    """Map a detect_host() label to its GIF stem, e.g. "claude code" -> claude-code.gif."""
    return host.replace(" ", "-").lower() + ".gif"


def _unpack_entry(entry, default_layout):
    """A custom gifs entry is either a path string or {"path":..,"layout":..}.

    A relative path is resolved against USER_GIF_DIR (~/.agent-glance/gifs) so
    users can just drop files there; an absolute path is used as-is for
    anyone keeping GIFs elsewhere.
    """
    if isinstance(entry, dict):
        path, layout = entry.get("path"), entry.get("layout", default_layout)
    else:
        path, layout = entry, default_layout
    if path and not os.path.isabs(path):
        path = os.path.join(USER_GIF_DIR, path)
    return path, layout


def _pick_state(entry, state):
    """Pick the per-state candidate out of a gifs[host]/gifs["default"] value.

    A per-state map (e.g. {"working":..,"waiting":..,"done":..}) is keyed by
    `state`, falling back to its own "default" sub-key; a flat entry (str, or
    {"path":..,"layout":..}) applies to every state as-is.
    """
    if isinstance(entry, dict) and "path" not in entry:
        return entry.get(state) or entry.get("default")
    return entry


def _resolve_char(preset, host, state, cfg):
    """Resolve (char_path, layout) for this push, or (None, None) to fall back.

    custom : gifs[host][state] -> gifs[host] (flat) -> gifs["default"][state] -> gifs["default"] (flat)
    anime  : user anime override (fullscreen); else hosts placeholder fallback
    hosts  : user override -> bundled placeholder
    """
    display = cfg.get("display", {})
    gifs = display.get("gifs", {}) or {}
    layout_default = display.get("layout", "frame")
    stem = _host_filename(host)

    if preset == "custom":
        cand = _pick_state(gifs.get(host), state) if host in gifs else None
        if not cand and "default" in gifs:
            cand = _pick_state(gifs["default"], state)
        if cand:
            path, layout = _unpack_entry(cand, layout_default)
            if path and os.path.exists(path):
                return path, layout

    if preset == "anime":
        # Anime art is TBD ("지정 예정"). User override wins; otherwise fall
        # through to the hosts placeholder so the screen never blanks.
        user = os.path.join(USER_ANIME_DIR, stem)
        if os.path.exists(user):
            return user, "fullscreen"

    # hosts preset, plus custom/anime fallback -> user override then bundled.
    user = os.path.join(USER_HOSTS_DIR, stem)
    if os.path.exists(user):
        return user, layout_default
    bundled = os.path.join(BUNDLED_HOSTS_DIR, stem)
    if os.path.exists(bundled):
        return bundled, layout_default
    return None, None


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
    """Pick the winning entry: most recent timestamp/seq wins, using priority as tiebreaker.
    Automatically expires stale 'approval' (waiting) entries older than 25 seconds.
    """
    if not entries:
        return None
    now = time.time()
    valid = []
    for e in entries:
        ts = e.get("ts", 0)
        state = e.get("state")
        if state == "waiting" and (now - ts > 25):
            continue
        valid.append(e)
    if not valid:
        return None
    return max(valid, key=lambda e: (
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


def parse_transcript(path=None, cwd=None):
    """Pull model + token usage from session transcript JSONL across hosts."""
    fallback_limit = load_config().get("context_limit", 200000)
    info = {"model": "-", "ctx": 0, "cum_in": 0, "cum_out": 0, "compacted": False, "limit": fallback_limit}

    # Check live status cache (~/.agent-glance/last_status.json) for 100% exact parity with TUI
    cache_file = os.path.expanduser("~/.agent-glance/last_status.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file) as cf:
                cache_data = json.load(cf)
            cache_cwd = (cache_data.get("workspace") or {}).get("current_dir") or cache_data.get("cwd")
            if not cwd or not cache_cwd or os.path.basename(cwd.rstrip("/")) == os.path.basename(cache_cwd.rstrip("/")):
                cw = cache_data.get("context_window") or {}
                m = cache_data.get("model") or {}
                c_in = cw.get("total_input_tokens") or cw.get("input_tokens") or 0
                c_out = cw.get("total_output_tokens") or cw.get("output_tokens") or 0
                c_pct = cw.get("used_percentage")
                c_limit = cw.get("context_window_size") or cw.get("max_tokens")
                c_model = m.get("id") or m.get("display_name")

                if c_pct is not None or c_in or c_out:
                    if c_model:
                        info["model"] = str(c_model)
                    if c_limit:
                        info["limit"] = int(c_limit)
                    else:
                        info["limit"] = resolve_model_context_limit(info["model"], fallback_limit)
                    info["cum_in"] = int(c_in)
                    info["cum_out"] = int(c_out)
                    if c_pct is not None:
                        info["pct"] = int(round(float(c_pct)))
                        info["ctx"] = int(info["limit"] * info["pct"] / 100)
                    else:
                        info["ctx"] = info["cum_in"] + info["cum_out"]
                        info["pct"] = min(100, round(info["ctx"] / info["limit"] * 100)) if info["limit"] else 0
                    return info
        except Exception:
            pass

    if not path or not os.path.exists(path):
        candidates = []
        proj_name = os.path.basename(cwd.rstrip("/")) if cwd else None

        all_claude = glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))
        all_agy = glob.glob(os.path.expanduser("~/.gemini/antigravity-cli/brain/*/.system_generated/logs/transcript.jsonl"))
        all_codex = glob.glob(os.path.expanduser("~/.codex/sessions/*/*.jsonl")) + glob.glob(os.path.expanduser("~/.codex/*/*.jsonl"))

        if proj_name:
            candidates.extend([p for p in all_claude if proj_name in p])
            candidates.extend([p for p in all_codex if proj_name in p])
            if not candidates and ("antigravity" in proj_name.lower() or "agentglance" in proj_name.lower()):
                candidates.extend(all_agy)

        if not candidates:
            candidates = all_claude + all_agy + all_codex

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

    try:
        with open(path, errors="ignore") as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except Exception:
                    continue

                if is_agy:
                    stype = o.get("type", "")
                    source = o.get("source", "")
                    content = o.get("content", "") or ""
                    thinking = o.get("thinking", "") or ""
                    tool_calls = json.dumps(o.get("tool_calls", [])) if o.get("tool_calls") else ""

                    if stype in ("USER_INPUT", "SYSTEM") and "Model Selection" in content:
                        for line_c in content.splitlines():
                            if line_c.strip().startswith("Model Selection"):
                                parts = line_c.split("to ")
                                if len(parts) > 1:
                                    info["model"] = parts[1].rstrip(".").strip()

                    if stype == "CHECKPOINT":
                        info["compacted"] = True

                    in_tok = 0
                    out_tok = 0
                    if source == "MODEL":
                        out_tok = _estimate_tokens(thinking) + _estimate_tokens(content) + _estimate_tokens(tool_calls)
                    else:
                        in_tok = _estimate_tokens(content)

                    info["cum_in"] += in_tok
                    info["cum_out"] += out_tok
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

    if is_agy:
        info["ctx"] = info["cum_in"] + info["cum_out"]
    elif last_u:
        info["ctx"] = (last_u.get("input_tokens", 0)
                       + last_u.get("cache_read_input_tokens", 0)
                       + last_u.get("cache_creation_input_tokens", 0))

    if info["model"] == "-" and is_agy:
        info["model"] = "Gemini 3.6 Flash"

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


def _draw_header(d, s, info):
    """Top accent bar + project · host header + divider. Shared chrome."""
    d.rectangle([0, 0, W, 6], fill=s["fg"])              # top accent bar
    host = detect_host()
    proj = info.get("project") or project_name()
    fhead = _font(18, True, cjk=True)
    head = _foot_str(d, host, proj, fhead, 216)
    d.text((CX, 26), head, font=fhead, fill=(240, 240, 240), anchor="mm")
    d.line([(16, 42), (224, 42)], fill=s["fg"], width=1)  # divider under header


def _draw_footer(d, s, info):
    """Bottom metrics block (model / context % / usage bar / tokens). Shared chrome."""
    # ---- metrics block: flush to the bottom, generous row spacing ----
    limit = info.get("limit") or resolve_model_context_limit(info.get("model"), load_config().get("context_limit", 200000))
    ctx = info.get("ctx", 0)
    pct = info.get("pct") if info.get("pct") is not None else (min(100, round(ctx / limit * 100)) if limit else 0)
    compacted = info.get("compacted", False)

    # token row, flush to the bottom edge
    ftn = _font(12, False)
    d.text((16, 228), "in {}".format(_fmt(info.get("cum_in", 0))), font=ftn, fill=(185, 185, 185), anchor="lm")
    d.text((CX, 228), "{}/{}".format(_fmt(ctx), _fmt(limit)), font=ftn, fill=(220, 220, 220), anchor="mm")
    d.text((224, 228), "out {}".format(_fmt(info.get("cum_out", 0))), font=ftn, fill=(185, 185, 185), anchor="rm")

    # Tier-based dynamic color for context bar & percentage label
    tier_color = get_context_tier_color(pct)

    # context usage bar (well clear of the token glyphs above it)
    d.rectangle([16, 200, 224, 208], fill=(70, 70, 70))
    if pct > 0:
        d.rectangle([16, 200, 16 + int(208 * pct / 100), 208], fill=tier_color)

    # model (left) + context % (right), above the bar
    pct_str = "{}%".format(pct)
    model_str = info.get("model", "-")
    d.text((16, 182), model_str, font=_font(13, True), fill=(215, 215, 215), anchor="lm")
    d.text((224, 182), pct_str, font=_font(14, True), fill=tier_color, anchor="rm")

    # divider capping the whole metrics block
    d.line([(16, 168), (224, 168)], fill=s["fg"], width=1)

    # divider capping the whole metrics block
    d.line([(16, 166), (224, 166)], fill=s["fg"], width=1)


def render(state, sub=None, info=None, out=TMP_GIF):
    s = STATES.get(state, STATES["working"])
    info = info or {}
    img = Image.new("RGB", (W, H), s["bg"])
    d = ImageDraw.Draw(img)
    _draw_header(d, s, info)

    # ---- status: dot + label inline on one row (default mode middle) ----
    flab = _font(26, True)
    label_w = d.textlength(s["label"], font=flab)
    dot_r = 6
    gap = 16
    row_w = dot_r * 2 + gap + label_w          # dot + gap + text
    rx = CX - row_w / 2                         # left edge of the row
    dot_cx = rx + dot_r                         # dot center
    status_y = 68
    d.ellipse([dot_cx - dot_r, status_y - dot_r, dot_cx + dot_r, status_y + dot_r], fill=s["fg"])
    if s["pulse"]:
        d.ellipse([dot_cx - dot_r - 4, status_y - dot_r - 4,
                   dot_cx + dot_r + 4, status_y + dot_r + 4], outline=s["fg"], width=2)
    d.text((dot_cx + dot_r + gap, status_y), s["label"], font=flab, fill=s["fg"], anchor="lm")

    sub = (sub or "").strip() or s["sub"]
    fsub = _font(18, cjk=True)
    y = 100                                     # margin below the status row
    for ln in _wrap(sub, fsub, 200, d, max_lines=3):
        d.text((CX, y), ln, font=fsub, fill=(225, 225, 225), anchor="mm")
        y += 22

    _draw_footer(d, s, info)
    img.save(out, "GIF")
    return out


# Middle zone where the character GIF is composited in "frame" layout:
# between the header divider (y=42) and the footer divider (y=166).
MIDDLE_BOX = (8, 46, 224, 116)   # (x, y, w, h)


def _load_gif_frames(path):
    """Return [(RGB frame, duration_ms), ...] from an animated (or static) GIF.

    Coalesces disposal so every returned frame is a full source-resolution
    image (handles delta-encoded and transparent GIFs correctly).
    """
    frames = []
    with Image.open(path) as im:
        n = getattr(im, "n_frames", 1) or 1
        canvas = None
        for i in range(n):
            im.seek(i)
            dur = max(_MIN_FRAME_MS, int(im.info.get("duration") or 100))
            disposal = im.info.get("disposal", 0)
            frame_rgba = im.convert("RGBA")
            # disposal 2 (restore-to-background) -> reset canvas; 1/none -> accumulate
            if canvas is None or disposal == 2:
                canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))
            canvas = Image.alpha_composite(canvas, frame_rgba)
            frames.append((canvas.convert("RGB"), dur))
    if not frames:
        raise ValueError("no frames in " + path)
    if len(frames) > _MAX_FRAMES:
        stride = math.ceil(len(frames) / _MAX_FRAMES)
        frames = frames[::stride][:_MAX_FRAMES]
    return frames


def _contain_box(src_w, src_h, box):
    """Aspect-preserving fit inside box=(x,y,w,h); returns paste (x,y,w,h)."""
    bx, by, bw, bh = box
    scale = min(bw / src_w, bh / src_h)
    w = max(1, int(src_w * scale))
    h = max(1, int(src_h * scale))
    x = bx + (bw - w) // 2
    y = by + (bh - h) // 2
    return x, y, w, h


def _build_chrome_base(state, info, layout):
    """Static chrome drawn once: state-colored bg + (frame layout) header/footer."""
    s = STATES.get(state, STATES["working"])
    img = Image.new("RGB", (W, H), s["bg"])
    if layout == "frame":
        d = ImageDraw.Draw(img)
        _draw_header(d, s, info)
        _draw_footer(d, s, info)
    return img, s


def render_gif(state, sub=None, info=None, char_path=None, layout="frame", out=TMP_GIF):
    """Compose an animated GIF: state-colored chrome + character frames.

    The device loops the result locally, so only one upload is needed per push.
    Falls back to the caller (raise) on any error so push_state can render static.
    """
    info = info or {}
    src_frames = _load_gif_frames(char_path)
    chrome_base, _s = _build_chrome_base(state, info, layout)

    out_frames, durations = [], []
    for src, dur in src_frames:
        base = chrome_base.copy()
        if layout == "fullscreen":
            base.paste(src.resize((W, H), Image.LANCZOS), (0, 0))
        else:
            x, y, w, h = _contain_box(src.width, src.height, MIDDLE_BOX)
            base.paste(src.resize((w, h), Image.LANCZOS), (x, y))
        out_frames.append(base)
        durations.append(dur)

    out_frames[0].save(
        out, "GIF",
        save_all=True,
        append_images=out_frames[1:],
        loop=0,
        duration=durations,
        disposal=2,
    )
    return out


# ---------------------------------------------------------------- push / lifecycle
def _trim(text, n=40):
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def _last_pushed():
    """Best-effort (state, key, t) of the most recent successful push, or (None, None, 0)."""
    try:
        prev = json.load(open(THROTTLE_PATH))
        prev_key = prev.get("key", "")
        prev_state = prev_key.split("|")[0] if "|" in prev_key else ""
        return prev_state, prev.get("project"), prev_key, prev.get("t", 0)
    except Exception:
        return None, None, None, 0


def push_state(state, sub=None, info=None):
    """Render + upload a state. Throttles identical re-pushes to spare flash."""
    key = "{}|{}".format(state, sub or "")
    now = time.time()
    project = (info or {}).get("project")
    prev_state, _prev_project, prev_key, prev_t = _last_pushed()
    # Only throttle if the state AND subtitle are identical. State transitions ALWAYS push!
    if prev_state == state and prev_key == key and now - prev_t < THROTTLE_SEC:
        return False  # identical state pushed recently -> skip

    cfg = load_config()
    preset = cfg["display"]["preset"]
    char_path, layout = (None, None)
    if preset != "default":
        char_path, layout = _resolve_char(preset, detect_host(), state, cfg)
    if char_path:
        try:
            gif = render_gif(state, sub, info, char_path, layout)
        except Exception as e:
            try:
                with open(ERRLOG, "a") as fh:
                    fh.write("{} render_gif: {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S"), e))
            except Exception:
                pass
            gif = render(state, sub, info)   # never blank the screen
    else:
        gif = render(state, sub, info)
    _upload_with_retry("/photo/upload", "file", gif)
    set_photo_enabled(STATUS_FILE, True)
    json.dump({"key": key, "t": now, "project": project}, open(THROTTLE_PATH, "w"))
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
    cwd = data.get("cwd") or (data.get("workspacePaths") or [None])[0]
    info = parse_transcript(tp, cwd=cwd)
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

    # Gif mode renders + uploads a whole character animation per push, which
    # the device can't keep up with if every tool call re-fires it. "working"
    # is sticky once shown: only a real transition (prompt submit, done,
    # waiting) needs a fresh push, so PreToolUse/PostToolUse chatter during an
    # already-"working" turn is a no-op.
    if ev in ("PreToolUse", "PostToolUse") and state == "working":
        if load_config()["display"]["preset"] != "default":
            cwd = data.get("cwd") or (data.get("workspacePaths") or [None])[0]
            last_state, last_project, _k, _t = _last_pushed()
            if last_state == "working" and last_project == project_name(cwd):
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
    elif a == "--preset" and len(args) > 1:
        val = args[1].strip().lower()
        if val not in ("default", "hosts", "anime", "custom"):
            print("preset must be one of: default | hosts | anime | custom")
            return
        cfg = load_config()
        cfg["display"]["preset"] = val
        json.dump(cfg, open(CONFIG_PATH, "w"), indent=2)
        print("preset saved:", val, "— mode:", "default" if val == "default" else "gif (animated)")
    elif a == "--layout" and len(args) > 1:
        val = args[1].strip().lower()
        if val not in ("frame", "fullscreen"):
            print("layout must be: frame | fullscreen")
            return
        cfg = load_config()
        cfg["display"]["layout"] = val
        json.dump(cfg, open(CONFIG_PATH, "w"), indent=2)
        print("layout saved:", val)
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

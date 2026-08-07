---
name: agent-glance
description: >-
  Connect a GeekMagic SmallTV (SD_RU/SDPro ESP8266 firmware) as a Claude Code
  status monitor. Use when the user wants to show Claude's working/waiting/done
  state, model, context %, and token counts on the SmallTV display. Triggers on
  "smalltv", "geekmagic", "status monitor", "기기에 상태 표시", "시계 모니터".
---

# agent-glance — Claude Code status on a GeekMagic SmallTV

Renders Claude Code session state (WORKING / APPROVAL / DONE) plus live metrics
(model, context %, in/out tokens) to a GeekMagic SmallTV's 240×240 display.

The target firmware (**SD_RU** / **SD Pro**, ESP8266 community firmware) has
**no text API**, so a GIF is rendered with Pillow and pushed to the device's
Photo album. The device runs as a dedicated status display (Photo theme = sole
active theme, `agent_status.gif` = sole photo). **Hooks auto-activate when this
plugin is enabled** — no manual `settings.json` editing required.

## How it works

```
host lifecycle hook (JSON on stdin)
        │
   scripts/agent_glance.py
     · normalises the payload (hook_event_name | hookEventName)
     · maps the host's event to WORKING / APPROVAL / DONE
     · parses the session transcript for model / context / tokens
     · renders a 240×240 GIF (Korean-safe fonts)
     · backgrounds the upload (never blocks the agent), retries on busy-403
        │
   GeekMagic SmallTV Photo album  →  display
```

## Multi-host hooks

The three hosts do **not** share a hook format. Each gets its own file, and no
generic `hooks/hooks.json` exists — that path is the default for *both* Claude
and Codex, so leaving one there risks the wrong host loading it.

| Host | Hook file | Why that path |
|---|---|---|
| Claude Code | `hooks/claude-hooks.json` | declared via `.claude-plugin/plugin.json` |
| Codex | `hooks/codex-hooks.json` | declared via `.codex-plugin/plugin.json` |
| agy (Antigravity) | `hooks.json` (plugin **root**) | forced — agy's manifest schema is `additionalProperties:false`, so the path cannot be declared |

Event mapping, since the hosts expose different lifecycles:

| Display state | Claude Code | Codex | agy |
|---|---|---|---|
| ● WORKING | `UserPromptSubmit` | `UserPromptSubmit` | `PreInvocation` |
| ⛔ APPROVAL | `Notification` | `PermissionRequest` | `PreToolUse` matcher `ask_permission` |
| ✓ DONE | `Stop` | `Stop` | `Stop` |

Structural differences the script absorbs:
- Claude/Codex send `hook_event_name` (snake_case); agy sends `hookEventName`
  (camelCase) and `transcriptPath` instead of `transcript_path`.
- agy wraps everything in a **named hook group** (`{"agent-glance": {…}}`) rather
  than Claude/Codex's `{"hooks": {…}}`.
- Codex has no `Notification` event; agy has neither `Notification` nor
  `UserPromptSubmit`, and only 5 events total.

### Absolute path requirement (Codex / agy)

Only Claude Code substitutes `${CLAUDE_PLUGIN_ROOT}` inside hook commands.
Codex and agy need a real absolute path, so their hook files point at a stable
location instead of guessing each host's install layout:

```bash
python3 "$HOME/.agent-glance/agent_glance.py"
```

Run this once after install to put the runtime there (`--setup` also does it):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py" --link-runtime
```

## Prerequisites

1. **GeekMagic SmallTV on SD_RU / SD Pro firmware** (ESP8266). Verify by opening
   `http://<DEVICE_IP>/` — the web UI title is "Умные погодные часы" (SD_RU) and
   `/photo/list`, `/theme/list`, `/config` respond. (Official GeekMagic stock
   firmware and SmallTV-PRO/ESP32 use a *different* API and are not supported.)
2. **Device and this machine on the same Wi-Fi.**
3. **Python 3.8+ with Pillow**: `python3 -c "import PIL"` — if missing,
   `pip install Pillow`.

## Setup (do once)

```bash
# 1. Point the tool at the device (env var — works for any user/machine):
export AGENT_GLANCE_IP=192.168.x.x        # add to ~/.zshrc to persist

# 2. (Optional) context window for the % bar. Default 200000.
export AGENT_GLANCE_CONTEXT_LIMIT=1000000   # e.g. a 1M-context model

# 3. Take over the device (backs up themes/photos, switches to Photo-only):
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py" --setup
```

`--setup` writes a backup to `~/.agent-glance/device_backup.json`. To revert the
device to its original clock/themes later: `... --restore`.

The hooks (UserPromptSubmit / Notification / Stop) are declared in
`hooks/hooks.json` and fire automatically while the plugin is enabled — the
first prompt after enabling animates the display.

## Commands

| Command | Effect |
|---|---|
| `--setup` | Take over device (backup + Photo-only mode + first frame) |
| `--restore` | Revert device to the pre-setup themes/photos |
| `--test working\|waiting\|done [subtitle]` | Manual push (uses newest local transcript for metrics; respects the current preset, so it previews gif mode) |
| `--ip <IP>` | Save IP to `~/.agent-glance/config.json` (alternative to the env var) |
| `--preset default\|hosts\|custom` | Switch display mode (`default` = static frame; others = animated gif mode) |
| `--layout frame\|fullscreen` | gif-mode layout: `frame` keeps header+footer; `fullscreen` is the GIF only |

## GIF mode (optional)

> [!WARNING]
> **GIF Size Warning**: GIFs that are too large place heavy strain on ESP8266 RAM/Flash, leading to instability or unexpected device reboots. Keep files strictly within specs (**< 100 KB** recommended).

Beyond the static status frame, gif mode composites a **looping animated GIF** (character in the middle, header + status footer kept) that the firmware decodes and plays locally — one upload per state, no per-frame network traffic. State is still shown via the top accent bar + background colour.

```bash
# bundled neutral per-host character placeholders (work out of the box):
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py" --preset hosts
```

To replace a character with the user's own GIF (wins over bundled; updates on the next push, no restart), drop it in the user dir named for the host — `claude-code.gif`, `codex.gif`, `antigravity.gif`, `hermes.gif`, or `agent.gif` for any other host:

```bash
mkdir -p ~/.agent-glance/gifs/hosts
cp my-character.gif ~/.agent-glance/gifs/hosts/claude-code.gif
```

`custom` lets the user map their own GIFs per host and per state in `~/.agent-glance/config.json`:

```json
"display": { "preset": "custom", "layout": "frame",
  "gifs": { "default": "/path/fallback.gif",
            "claude code": { "working": "a.gif", "waiting": "b.gif", "done": "c.gif" } } }
```

A missing or unreadable GIF falls back to the static frame — the screen never blanks. See the repo README for the full resolution order.

### Optimal GIF Specifications

| Parameter | Frame Layout | Fullscreen Layout |
|---|---|---|
| **Optimal Resolution** | **224 × 116 px** (1.93:1) or **116 × 116 px** (1:1) | **240 × 240 px** (1:1) |
| **Middle Box Target** | `(8, 46, 224, 116)` | Covers full screen |
| **Recommended File Size** | **< 100 KB** (Hard max < 300 KB to prevent ESP8266 RAM/OOM crashes & reboots) |
| **Frame Count** | **12 – 16 frames** (Script downsamples exceeding frames to `_MAX_FRAMES = 16`) |
| **Frame Delay** | **80ms – 150ms** per frame (1.2s – 2.0s loop) |
| **Colors** | **64 – 128 colors** |

**Shrinking an oversized source GIF** (raw exports easily hit multi-MB): sample ~14 frames evenly across the whole clip (preserves full motion range), then re-encode at a short target loop (compresses playback speed only — don't just fps-downsample, that keeps the original's slow duration and blows the loop-length spec):

```bash
# 1) sample frames, cropped/scaled per layout (STEP = source nb_frames / 14, rounded down)
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=224:116:force_original_aspect_ratio=decrease" -vsync 0 frames/f_%03d.png   # frame layout
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=240:240:force_original_aspect_ratio=increase,crop=240:240" -vsync 0 frames/f_%03d.png   # fullscreen layout (crop to square — it's stretched to fill, not letterboxed)

# 2) re-encode at 10fps (100ms/frame) with a small palette
ffmpeg -framerate 10 -i frames/f_%03d.png \
  -vf "split[s0][s1];[s0]palettegen=max_colors=64:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer" \
  output.gif
```

Still over 300 KB → drop `max_colors` to 32 before cutting frame count.

## Verified device API (SD_RU / SD Pro)

| Action | Endpoint |
|---|---|
| upload image | `POST /photo/upload` (multipart field `file`) |
| photo on/off | `GET /photo/toggle?name=<f>&state=1\|0` |
| delete photo | `GET /photo/delete?name=<f>` |
| theme on/off | `GET /theme/toggle?id=<n>&state=1\|0` (id 2 = Photo) |
| read state | `GET /photo/list`, `GET /theme/list`, `GET /config` |

Gotchas discovered by probing:
- `state` must be `1`/`0`. The firmware `atoi()`s it, so `"true"` becomes `0`.
- Disabling the last enabled theme/photo returns **HTTP 403** (anti-blank-screen
  guard). Setup enables the target first, then disables the rest.
- `/config` exposes the device Wi-Fi password and weather API key with **no
  auth** — that is the firmware's behavior, not something this tool adds.

## Limitations / notes

- **The 7 themes cannot each show a session.** Only the Photo theme (id 2)
  renders custom content; the other six are fixed clock/weather UIs. Multiple
  sessions could instead rotate via the photo album (one GIF per session) — not
  implemented in this version.
- Hook uploads run in a background child process and retry, so a powered-off or
  slow device never blocks Claude Code. Errors log to
  `/tmp/agent_glance_error.log` (empty = healthy).
- State (config + backup) lives in `~/.agent-glance/`, NOT the plugin install dir
  (which is ephemeral and cleared on update).

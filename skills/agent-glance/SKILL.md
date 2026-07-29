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
| `--test working\|waiting\|done [subtitle]` | Manual push (uses newest local transcript for metrics) |
| `--ip <IP>` | Save IP to `~/.agent-glance/config.json` (alternative to the env var) |

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

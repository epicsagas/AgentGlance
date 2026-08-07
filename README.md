<div align="center">
<img width="320px" src="assets/logo.png" alt="Agent Glance" />
<h1>Agent Glance</h1>

**[English](README.md)** | [한국어](docs/i18n/ko/README.md) | [日本語](docs/i18n/ja/README.md) | [简体中文](docs/i18n/zh-Hans/README.md) | [繁體中文](docs/i18n/zh-Hant/README.md) | [Español](docs/i18n/es/README.md) | [Français](docs/i18n/fr/README.md) | [Deutsch](docs/i18n/de/README.md) | [Português](docs/i18n/pt/README.md) | [Русский](docs/i18n/ru/README.md) | [Italiano](docs/i18n/it/README.md)

</div>

<hr />

> Turn a **GeekMagic SmallTV** into a live agent status display — for Claude Code, Codex, and agy.

The little TV shows what your agent is doing right now: **WORKING**, **APPROVAL NEEDED**, or **DONE** — plus the model, context-window usage, and token counts pulled from the live session transcript.
The killer feature is the red **APPROVAL** screen: put the agent on another monitor and you can walk away, glance over, and know the moment it's blocked on you instead of discovering it ten minutes later.

| Event | Display |
|---|---|
| prompt submitted | ● **WORKING** (amber) + the prompt |
| approval needed | ⛔ **APPROVAL** (red) + what it wants |
| turn finished | ✓ **DONE** (green) |

Each frame also carries `model · context bar + % · in/out tokens`.

<div align="center">
<table width="100%">
<tr>
<td width="50%"><img src="assets/claude-approval.jpeg" width="100%" alt="claude approval"></td>
<td width="50%"><img src="assets/claude-done.jpeg" width="100%" alt="claude done"></td>
</tr>
</table>
</div>

## Who is this for?

- **You run long agent sessions** — migrations, test suites, big refactors — and keep checking the terminal to see if it finished or stalled.
- **You walk away from the keyboard** — and want to know the *moment* the agent needs your approval, not ten minutes later.
- **You use Claude Code / Codex / agy / hermes** headlessly and miss the visual feedback a full IDE would give you.
- **You own a GeekMagic SmallTV** sitting idle and want it to actually pull its weight.

If you've ever alt-tabbed back to a terminal and thought *"wait, has it been waiting on me this whole time?"* — this is for you.

## Requirements

- A GeekMagic SmallTV running **SD_RU / SD Pro** community firmware (ESP8266). Quick check — this must return JSON with a `files` array:

  ```bash
  curl -s http://<DEVICE_IP>/photo/list
  ```
  
  Stock GeekMagic firmware and the ESP32 "PRO" expose a *different* API and are **not** supported.
  
- The device on the same Wi-Fi as your machine.
- Python 3.8+ with Pillow (`pip install Pillow`).

## Install

Published through the [`epicsagas/plugins`](https://github.com/epicsagas/plugins) marketplace; the plugin itself lives at [`epicsagas/AgentGlance`](https://github.com/epicsagas/AgentGlance).

**Claude Code**

```bash
claude plugin marketplace add epicsagas/plugins
claude plugin install agent-glance@epicsagas
```

**Codex**

```bash
codex plugin marketplace add epicsagas/plugins
codex plugin add agent-glance@epicsagas
```

**agy (Antigravity)**

```bash
agy plugin install https://github.com/epicsagas/AgentGlance
```

**hermes**

```bash
hermes plugins install epicsagas/AgentGlance
hermes plugins enable agent-glance
```

### What each host gets

| Host | Skills | Slash commands | Auto hooks | Status |
|---|:--:|:--:|:--:|---|
| Claude Code | ✅ | ✅ | ✅ | verified end to end |
| Codex | ✅ | ✅ | ✅ | hook file matches the documented schema; not runtime-verified |
| agy | ✅ | ✅ (converted to skills) | ✅ | `agy plugin validate` passes: 1 skill, 4 commands, 1 hook group processed |
| hermes | ✅ | — | ✅ | hooks registered in `__init__.py`; verified against a mock context, not a live session |

Then onboard the device — this finds it, saves the IP, backs up the device, and switches it to monitor mode:

```
/agent-glance:setup
```

On hosts without slash commands, run the same steps by hand:

```bash
python3 <plugin>/scripts/agent_glance.py --ip <DEVICE_IP>
python3 <plugin>/scripts/agent_glance.py --setup
```

Hooks ship with the plugin and activate on their own. **Restart the agent after installing** — hooks are loaded at session start.

## Configuration

Config is read **env-var first**, falling back to `~/.agent-glance/config.json` (written by `--ip`). The env var is the portable option for shared or multi-machine setups.

| Variable | Purpose | Default |
|---|---|---|
| `AGENT_GLANCE_IP` | device IP — **required** | — |
| `AGENT_GLANCE_CONTEXT_LIMIT` | context window used to scale the % bar | `200000` |
| `AGENT_GLANCE_PRESET` | display preset: `default` \| `hosts` \| `custom` | `hosts` |
| `AGENT_GLANCE_LAYOUT` | gif-mode layout: `frame` \| `fullscreen` | `frame` |

### GIF mode & presets

> [!WARNING]
> **Warning on GIF Size**: If a GIF file is too large, it places heavy strain on the device's memory (ESP8266 RAM/Flash) and may cause unexpected reboots or crashes. Please keep your GIFs strictly within the recommended specifications (**< 100 KB** recommended).

The default mode is the static status frame described above. Set a different preset to switch to **gif mode**, which composites a looping animated GIF (character in the middle, header + status footer kept) that the device plays locally — one upload per state, no per-frame network traffic. State is still signalled by the top accent bar + background colour.

| Preset | What it shows |
|---|---|
| `default` | Static frame (the original behaviour) |
| `hosts` | A bundled per-host character GIF in the middle; header + footer kept |
| `custom` | Your own GIFs, per host and/or per state (see schema) |

Pick a preset with the `--preset` CLI flag (it persists to `config.json`, like `--ip`):

```
python3 scripts/agent_glance.py --preset hosts
```

`hosts` ships with neutral placeholders in `assets/hosts/` so it works immediately. To use your own character, drop a GIF into the user directory — it takes precedence over the bundled one, and the screen updates on the next state push (no restart):

```bash
mkdir -p ~/.agent-glance/gifs/hosts
cp my-character.gif ~/.agent-glance/gifs/hosts/claude-code.gif
```

Name the file after the host it should replace (lowercase, spaces → hyphens):

| Detected host | Override filename |
|---|---|
| Claude Code | `claude-code.gif` |
| Codex | `codex.gif` |
| Antigravity | `antigravity.gif` |
| Hermes | `hermes.gif` |
| any other host | `agent.gif` |

### Optimal GIF Specifications

| Parameter | `frame` Layout | `fullscreen` Layout |
|---|---|---|
| **Optimal Resolution** | **224 × 116 px** (~1.93:1) or **116 × 116 px** (1:1) | **240 × 240 px** (1:1 square) |
| **Composite Target** | Fits inside `MIDDLE_BOX = (8, 46, 224, 116)` | Covers entire 1.54" SmallTV screen |
| **Recommended File Size** | **< 100 KB** (Hard max < 300 KB to avoid ESP8266 RAM/OOM crashes & reboots) |
| **Frame Count** | **12 – 16 frames** (Script downsamples exceeding frames to `_MAX_FRAMES = 16`) |
| **Frame Delay** | **80ms – 150ms** per frame (1.2s – 2.0s loop) |
| **Color Palette** | **64 – 128 colors** (optimizes rendering speed & Flash wear) |

**Shrinking a source GIF to spec** (raw exports easily hit multi-MB): sample frames evenly across the whole clip, then re-encode at a short target loop so the full range of motion survives even though playback speed is compressed.

1 — sample ~14 frames evenly across the source, cropped/scaled per layout:

```bash
# frame layout: letterboxed into MIDDLE_BOX, so just scale down (no crop needed)
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=224:116:force_original_aspect_ratio=decrease" \
  -vsync 0 frames/f_%03d.png

# fullscreen layout: stretched to fill 240x240, so crop to square first or it'll distort
ffmpeg -i source.gif -vf "select='not(mod(n,STEP))',scale=240:240:force_original_aspect_ratio=increase,crop=240:240" \
  -vsync 0 frames/f_%03d.png
```

`STEP` = source frame count ÷ 14 (rounded down) — ffprobe the source (`ffprobe -v error -select_streams v -show_entries stream=nb_frames -of default=nw=1 source.gif`) to get it.

2 — re-encode the sampled frames at a short target loop (10fps = 100ms/frame ≈ 1.4s loop for 14 frames) with a small palette:

```bash
ffmpeg -framerate 10 -i frames/f_%03d.png \
  -vf "split[s0][s1];[s0]palettegen=max_colors=64:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer" \
  output.gif
```

Still over 300 KB? Drop `max_colors` to 32 (try `dither=none` too) before cutting frame count — that's what actually keeps the loop expensive.

`custom` reads `display.gifs` from `config.json`. Each host entry is either a path string (one GIF for all states) or a per-state map; `"default"` is the fallback. Any entry can also be `{"path": ..., "layout": "fullscreen"}` to go full-screen for that one:

```json
"display": {
  "preset": "custom",
  "layout": "frame",
  "gifs": {
    "default": "/abs/path/fallback.gif",
    "claude code": { "working": "a.gif", "waiting": "b.gif", "done": "c.gif" },
    "codex": "/one-gif-for-all-states.gif",
    "agent": { "path": "x.gif", "layout": "fullscreen" }
  }
}
```

Resolution order per push: `gifs[host][state]` → `gifs[host]` → `gifs["default"]` → bundled hosts placeholder. A missing or unreadable GIF never blanks the screen — it falls back to the static frame.

## Commands

| Command | What it does |
|---|---|
| `/agent-glance:setup` | Full onboarding — discover device, verify firmware, save IP, back up, take over |
| `/agent-glance:status` | Health check — reachability, active theme, duplicate hooks, error log |
| `/agent-glance:test` | Push a frame (or cycle all three) to check rendering |
| `/agent-glance:restore` | Put the device back to its original clock and photos |

A few options are **CLI flags only** (no slash command) — they persist to `~/.agent-glance/config.json`, mirroring `--ip`:

| Flag | What it does |
|---|---|
| `--ip <IP>` | save the device IP |
| `--preset default\|hosts\|custom` | switch display mode (see [GIF mode](#gif-mode--presets)) |
| `--layout frame\|fullscreen` | gif-mode layout (frame keeps header+footer; fullscreen is the GIF only) |
| `--test [state] [subtitle]` | push a frame; respects the current preset, so it previews gif mode too |

## How it works

The firmware has **no text API**, so there is nothing to "print" to. Instead the script renders a 240×240 GIF with Pillow and pushes it into the device's Photo album, with that image as the only enabled photo and Photo as the only enabled theme — so the frame stays put instead of rotating away. The firmware's GIF decoder also plays **animated** GIFs, so in gif mode the script composites a multi-frame GIF and the device loops it locally — one upload per state, no per-frame traffic.

```
host lifecycle hook (JSON on stdin)
        │
   scripts/agent_glance.py
     · normalises the payload  (hook_event_name | hookEventName)
     · maps the host's event to WORKING / APPROVAL / DONE
     · reads the session transcript for model / context / tokens
     · renders a 240×240 GIF (CJK-safe font fallback)
     · forks the upload so the agent never waits on the device
        │
   SmallTV photo album  →  display
```

## Multi-host hooks

The three hosts do **not** share a hook format, so each gets its own file. There is deliberately no generic `hooks/hooks.json` — that path is the default for *both* Claude Code and Codex, and leaving one there means the wrong host loads it.

| Host | Hook file | Why there |
|---|---|---|
| Claude Code | `.claude-plugin/hooks.json` | declared in `.claude-plugin/plugin.json` |
| Codex | `.codex-plugin/hooks.json` | declared in `.codex-plugin/plugin.json` |
| agy | `hooks.json` (plugin **root**) | forced — agy's manifest schema is `additionalProperties:false`, so the path can't be declared |
| hermes | *(no file)* — `ctx.register_hook()` in `__init__.py` | hermes registers callbacks programmatically; handlers are called as `fn(**kwargs)` |

Because the hosts expose different lifecycles, the events differ too:

| Display | Claude Code | Codex | agy | hermes |
|---|---|---|---|---|
| ● WORKING | `UserPromptSubmit` | `UserPromptSubmit` | `PreInvocation` | `pre_llm_call` |
| ⛔ APPROVAL | `Notification` | `PermissionRequest` | `PreToolUse` matcher `ask_permission` | `pre_approval_request` |
| ✓ DONE | `Stop` | `Stop` | `Stop` | `post_llm_call` |

hermes is the only host with a first-class approval event; agy has none, so its
permission gate is matched through `PreToolUse` on the `ask_permission` tool.

And the payloads differ: Claude Code and Codex send `hook_event_name` / `transcript_path` (snake_case); agy sends `hookEventName` / `transcriptPath` (camelCase) and wraps its config in a named hook group. The script normalises all of it.

Only Claude Code substitutes `${CLAUDE_PLUGIN_ROOT}` inside hook commands, so the other two reference their own installed plugin path directly:

```
claude  ${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py
agy     $HOME/.gemini/config/plugins/agent-glance/scripts/agent_glance.py
codex   $HOME/.codex/plugins/cache/epicsagas/AgentGlance/<version>/scripts/agent_glance.py
        (resolved at hook time — Claude Code and Codex both install into
         versioned directories; agy does not)
```

## Device API reference (SD_RU / SD Pro)

| Action | Endpoint |
|---|---|
| upload image | `POST /photo/upload` (multipart field `file`) |
| photo on/off | `GET /photo/toggle?name=<f>&state=1\|0` |
| delete photo | `GET /photo/delete?name=<f>` |
| theme on/off | `GET /theme/toggle?id=<n>&state=1\|0` (id 2 = Photo) |
| read state | `GET /photo/list`, `/theme/list`, `/config` |

Gotchas found by probing a real device:

- `state` must be `1` / `0`. The firmware runs `atoi()` on it, so `"true"` becomes `0` and silently does the opposite of what you meant.
- Disabling the *last* enabled theme or photo returns **HTTP 403** — an anti-blank-screen guard. Setup enables the target first, then disables the rest.
- The ESP8266 is single-threaded and returns 403 when busy with a previous request, so uploads retry.
- ⚠️ `/config` serves the device's **Wi-Fi password and weather API key in plaintext with no authentication**. That is the firmware's behaviour, not something this plugin introduces — but treat the device as untrusted on a shared network.

## Limitations

- **The 7 device themes can't each show a session.** Only the Photo theme renders custom content; the other six are fixed clock/weather UIs. Rotating several sessions would mean multiple images in the album — not implemented.
- Metrics come from Claude Code's transcript format. Under Codex/agy the state colours still work, but model/token fields may be blank.
- State (`config.json`, `device_backup.json`) lives in `~/.agent-glance/`, not the plugin directory, which is wiped on plugin updates.

## License

[MIT](LICENSE)

---
description: Onboard and set up the GeekMagic SmallTV as an agent status monitor — finds the device, saves its IP, backs up the device, and switches it to dedicated-display mode
---

Onboard the SmallTV status monitor. Walk the user through this; don't assume any
step already happened.

## 1. Is the device already configured?

```bash
echo "env AGENT_GLANCE_IP=${AGENT_GLANCE_IP:-<unset>}"
cat ~/.agent-glance/config.json 2>/dev/null || echo "(no saved config)"
```

If an IP is already present, skip to step 3.

## 2. Find the device

Ask the user if they already know the device's IP (it is shown in the device's
own web UI, or in the router's client list). If they don't, offer to scan the
local network — say you are about to probe the local /24 and get their OK first:

```bash
BASE=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1)
BASE=${BASE%.*}
echo "scanning ${BASE}.1-254 ..."
for i in $(seq 1 254); do
  ( curl -s -m 0.4 "http://${BASE}.${i}/photo/list" 2>/dev/null \
      | grep -q '"files"' && echo "  FOUND SD_RU ${BASE}.${i}"
    curl -s -m 0.4 "http://${BASE}.${i}/app.json" 2>/dev/null \
      | grep -q '"theme"' && echo "  FOUND ULTRA ${BASE}.${i}" ) &
done; wait
```

Nothing found means the device is off, on another subnet/VLAN, or running
different firmware (see step 3).

## 3. Verify the firmware is supported

Either firmware works — check both:

```bash
curl -s -m 4 "http://<IP>/photo/list"   # SD_RU / SD Pro: JSON with a "files" array
curl -s -m 4 "http://<IP>/app.json"     # SmallTV Ultra: JSON with a "theme" key
```

One of the two must answer. If both 404, stop and tell the user their device
runs a different firmware — other GeekMagic stock variants and the ESP32 "PRO"
expose a different API and are not supported by this plugin.

## 4. Save the IP

Save it so every future session picks it up:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py" --ip <IP>
```

That writes `~/.agent-glance/config.json`. Also tell the user the portable
alternative, which takes precedence and is what to use on a shared or
multi-machine setup — add to `~/.zshrc`:

```bash
export AGENT_GLANCE_IP=<IP>
export AGENT_GLANCE_CONTEXT_LIMIT=200000   # set to the model's context window
```

`AGENT_GLANCE_CONTEXT_LIMIT` only scales the context-usage bar; the default is
200000. Ask what model they mostly run if it is clearly not a 200k window.

## 5. Take over the device

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py" --setup
```

This backs up the device's current themes and photos to
`~/.agent-glance/device_backup.json` **before** changing anything. Confirm the
output reports active theme `[2]` (Photo) on SD_RU, or `3` (Photo Album) on
SmallTV Ultra.

## 6. Choose the display mode (fresh setup only)

If step 1 found an existing config with a saved IP, the user already picked a
mode — keep the current preset and skip to step 7. Otherwise ask which of the
three modes they want (present all three; the first is the out-of-the-box
default):

**a) Static status frame (default)** — no animation, just the status screen:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py" --preset default
```

**b) Animated character (hosts)** — a looping per-host character GIF in the
middle of the frame, header + status footer kept. Ships with neutral
placeholders that work immediately:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py" --preset hosts
```

To swap in the user's own character instead, drop a GIF into the user dir
(wins over bundled; updates on the next push, no restart). Name it for the
host it replaces — `claude-code.gif`, `codex.gif`, `antigravity.gif`,
`hermes.gif`, or `agent.gif` for any other host:

```bash
mkdir -p ~/.agent-glance/gifs/hosts
cp my-character.gif ~/.agent-glance/gifs/hosts/claude-code.gif
```

**c) Custom GIFs** — the user's own GIFs, one for all states or one per state
(working / waiting / done). Run the helper wizard:

1. Ask whether they want **one GIF for everything** or **one per state**.
2. For each GIF they provide, run (omit `--state` for the one-for-everything
   case; add `--layout fullscreen` only if they want it edge-to-edge):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py" --gif <PATH> [--state working|waiting|done] [--layout frame|fullscreen]
```

3. The helper copies the file into `~/.agent-glance/gifs/` and writes the
   config itself — no manual JSON editing. Undo with `--gif-remove`.

After choosing b or c, preview it:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py" --test working "gif preview"
```

The mode can be changed any time later with `--preset default|hosts|custom`.

## 7. Show a frame and confirm

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py" --test done "monitor ready"
```

Ask the user to confirm they see a green DONE screen with the model name, a
context bar, and token counts along the bottom (in gif modes the character
animation is in the middle; the green DONE footer is what confirms the state).

Finally tell them:
- Hooks are bundled with the plugin and fire automatically — but **hooks load at
  session start**, so they must restart the agent before the display reacts to
  real activity.
- `/agent-glance:restore` puts the device back to its original clock.
- `/agent-glance:status` diagnoses a display that stops updating.

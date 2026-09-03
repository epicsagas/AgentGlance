---
name: ag-status
description: >-
  Health check for the SmallTV monitor — device reachability, display state,
  config, and recent errors. Use when the SmallTV display stops updating, shows
  the wrong screen, or the user asks whether the monitor is working ("status
  monitor 상태", "화면이 안 바뀐다", "smalltv 진단").
---

Report the health of the SmallTV monitor. Run these and summarise; do not dump
raw output at the user.

1. Config in effect (env var wins over the file):
   ```bash
   echo "AGENT_GLANCE_IP=${AGENT_GLANCE_IP:-<unset>}"
   echo "AGENT_GLANCE_CONTEXT_LIMIT=${AGENT_GLANCE_CONTEXT_LIMIT:-<unset, default 200000>}"
   echo "AGENT_GLANCE_PRESET=${AGENT_GLANCE_PRESET:-<unset, default default>}"
   echo "AGENT_GLANCE_LAYOUT=${AGENT_GLANCE_LAYOUT:-<unset, default frame>}"
   cat ~/.agent-glance/config.json 2>/dev/null || echo "(no config file — env only)"
   ```

2. Device reachable + what it is showing. The config's `firmware` key says which
   probe to use (`sd_ru` | `ultra`):
   ```bash
   # sd_ru:
   curl -s -m 4 "http://${AGENT_GLANCE_IP}/photo/list" | python3 -m json.tool
   curl -s -m 4 "http://${AGENT_GLANCE_IP}/theme/list" | python3 -m json.tool
   # ultra:
   curl -s -m 4 "http://${AGENT_GLANCE_IP}/app.json"
   curl -s -m 4 "http://${AGENT_GLANCE_IP}/filelist?dir=/image/" | grep -o 'agent_status[^'<']*'
   ```

3. Recent errors (empty means healthy):
   ```bash
   [ -s /tmp/agent_glance_error.log ] && tail -10 /tmp/agent_glance_error.log || echo "no errors"
   ```

Report as a short table: device online?, active theme (want id 2 = Photo on
sd_ru, 3 = Photo Album on ultra), `agent_status.gif` present (and on sd_ru,
enabled)?, backup exists?, errors.

Flag these specific problems if you see them:
- Active theme is not Photo (`[2]` sd_ru / `3` ultra) → the device is showing a
  clock, not the monitor. Re-run the `ag-setup` skill.
- Photos other than `agent_status.gif` are enabled → the display will rotate away
  from the status frame every few seconds.
- Hooks registered in BOTH `~/.claude/settings.json` and this plugin → every
  event uploads twice. Check with:
  ```bash
  grep -c agent_glance ~/.claude/settings.json 2>/dev/null || echo 0
  ```
  If that is non-zero while the plugin is enabled, tell the user to remove the
  hand-installed hooks from `settings.json` and keep the plugin's.

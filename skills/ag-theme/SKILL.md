---
name: ag-theme
description: >-
  Switch the SmallTV screen — weather, forecast, clocks, or back to the monitor
  (SmallTV Ultra firmware only). Use when the user wants to show a different
  screen on the device, or says "날씨 보여줘", "일기예보", "시계로 바꿔",
  "smalltv theme".
---

Switch what the SmallTV is showing (SmallTV Ultra firmware only). Map loose
wording from the user's request to a theme name (비/일기예보 → forecast etc.).

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py" --theme <name>
```

| Name | Screen |
|---|---|
| `weather` | Weather Clock Today |
| `forecast` | Weather Forecast |
| `photo` / `monitor` | Photo Album (the status monitor) |
| `clock` / `clock2` / `clock3` | Time styles 1–3 |
| `simple` | Simple Weather Clock |

A numeric id 1–7 also works. If no theme was named, ask which one.

This is a peek, not a takeover: the monitor re-asserts itself on the next agent
activity (prompt submitted, approval needed, or done) — no action needed to come
back. On SD_RU / SD Pro firmware the command exits with an error (themes there
are enable-flags, not a direct switch).

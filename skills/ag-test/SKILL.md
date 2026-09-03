---
name: ag-test
description: >-
  Push a test frame (working / waiting / done) to the SmallTV to check
  rendering. Use when the user wants to verify the display renders correctly,
  preview a state or GIF preset, or says "테스트 프레임", "화면 확인",
  "smalltv test".
---

Push a test frame to the SmallTV so the user can check the display.

## Preflight

```bash
echo "env AGENT_GLANCE_IP=${AGENT_GLANCE_IP:-<unset>}"
cat ~/.agent-glance/config.json 2>/dev/null || echo "(no saved config)"
```

If neither is set, the device has never been onboarded — stop and tell the user
to run the `ag-setup` skill first. Do not guess an IP.

## Push

Take the state (`working` | `waiting` | `done`) and an optional subtitle from
what the user asked for. Default to `waiting` (the most visually distinct) and
`test frame` when they did not say.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py" --test "<state>" "<subtitle>"
```

If the user did not name a state, cycle all three with a pause so they can watch
the transitions, ending on `done`:

```bash
for s in working waiting done; do
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py" --test "$s" "render check"
  sleep 3
done
```

## Confirm

```bash
[ -s /tmp/agent_glance_error.log ] && tail -5 /tmp/agent_glance_error.log || echo "no errors"
```

Expected: amber WORKING, red APPROVAL, green DONE — each with the model name, a
context-usage bar, and in/out token counts along the bottom.

`--test` respects the current preset: in gif mode (`--preset hosts`/`custom`)
the middle of the frame is the looping character GIF instead of the status text,
and the device animates it. State still shows via the top accent bar + background
colour. If gif mode is on but no character resolves, it falls back to the static
frame and logs to `/tmp/agent_glance_error.log`.

Report accurately rather than guessing:
- Nothing changes on screen → the device may not be in Photo mode; run the
  `ag-status` skill.
- Text renders as empty boxes → the font fallback has no glyphs for that
  script; say so instead of calling it a success.

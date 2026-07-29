---
description: Revert the SmallTV to the clock/themes it had before the monitor took it over
---

Restore the SmallTV to its pre-monitor state.

1. Show what the backup will restore, so the user knows what they are getting back:
   ```bash
   cat ~/.agent-glance/device_backup.json
   ```
   If the file is missing, stop and tell the user there is no backup — setup was
   never run from this machine, so there is nothing to restore to.

2. Restore:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/agent_glance.py" --restore
   ```

3. Verify the device is back to its original themes and photos:
   ```bash
   curl -s -m 4 "http://${AGENT_GLANCE_IP}/theme/list" | python3 -m json.tool
   curl -s -m 4 "http://${AGENT_GLANCE_IP}/photo/list" | python3 -m json.tool
   ```

Report which themes/photos are enabled now. Note that the plugin's hooks still
fire while the plugin is enabled — they will just re-upload `agent_status.gif` into
the album on the next event. To stop updates entirely, the user should disable
the plugin (`/plugin`), not only run restore.

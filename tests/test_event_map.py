"""Grok sends snake_case event values; Claude/Codex send PascalCase.

A UserPromptSubmit hook that ignores `user_prompt_submit` looks successful
in the TUI (exit 0) while the SmallTV never updates.
"""

import importlib.util
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script():
    path = ROOT / "scripts" / "agent_glance.py"
    spec = importlib.util.spec_from_file_location("agent_glance", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class EventMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ag = load_script()

    def _state(self, payload, env=None):
        saved = {}
        if env:
            for k, v in env.items():
                saved[k] = os.environ.get(k)
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        try:
            ev, _tp = self.ag._norm_event(payload)
            return self.ag._resolve_state_key(ev, payload), ev
        finally:
            for k, old in saved.items():
                if old is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = old

    def test_grok_user_prompt_submit_is_working(self):
        state, ev = self._state({"hookEventName": "user_prompt_submit"})
        self.assertEqual(ev, "UserPromptSubmit")
        self.assertEqual(state, "working")

    def test_grok_stop_is_done(self):
        state, ev = self._state({"hookEventName": "stop"})
        self.assertEqual(ev, "Stop")
        self.assertEqual(state, "done")

    def test_grok_notification_is_waiting(self):
        state, ev = self._state({"hookEventName": "notification"})
        self.assertEqual(ev, "Notification")
        self.assertEqual(state, "waiting")

    def test_claude_pascal_case_still_works(self):
        state, ev = self._state({"hook_event_name": "UserPromptSubmit"})
        self.assertEqual(ev, "UserPromptSubmit")
        self.assertEqual(state, "working")

    def test_grok_hook_event_env_fallback(self):
        state, ev = self._state({}, env={"GROK_HOOK_EVENT": "user_prompt_submit"})
        self.assertEqual(ev, "UserPromptSubmit")
        self.assertEqual(state, "working")


if __name__ == "__main__":
    unittest.main()

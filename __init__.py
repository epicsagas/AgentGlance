"""agent-glance — Hermes plugin entry point.

Hermes loads this module from ~/.hermes/plugins/agent-glance/ and calls
register(ctx) once at startup. It registers both the bundled skills and the
lifecycle hooks that drive the SmallTV status display.

Unlike the other hosts, Hermes has no hooks.json — callbacks are registered
programmatically via ctx.register_hook(name, fn), and handlers are called as
fn(**kwargs) (see VALID_HOOKS in hermes_cli/plugins.py).
"""
import threading
from pathlib import Path

# hermes event -> display state. Hermes exposes an explicit approval event,
# which is the one the display exists for.
HOOK_STATES = {
    "pre_llm_call": "working",
    "pre_approval_request": "waiting",
    "post_llm_call": "done",
}

_engine = None


def _load_engine():
    """Import scripts/agent_glance.py once, lazily (Pillow import is not free)."""
    global _engine
    if _engine is None:
        import importlib.util
        p = Path(__file__).parent / "scripts" / "agent_glance.py"
        spec = importlib.util.spec_from_file_location("agent_glance_engine", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _engine = mod
    return _engine


def _subtitle(state, kw):
    if state == "waiting":
        return kw.get("description") or kw.get("command") or "approval needed"
    if state == "working":
        return kw.get("user_message") or ""
    return None


def _push(state, kw):
    try:
        eng = _load_engine()
        cfg = eng.load_config()
        if not cfg.get("ip"):
            return                      # not onboarded — stay silent
        info = {
            "limit": cfg.get("context_limit", 200000),
            "project": eng.project_name(),
            "model": kw.get("model") or "-",
        }
        eng.push_state(state, eng._trim(_subtitle(state, kw) or "", 38), info)
    except Exception:
        pass                            # a status display must never break the agent


def _make_hook(state):
    def _hook(**kwargs):
        # Off the agent's thread: the device is on WiFi and may be asleep.
        threading.Thread(target=_push, args=(state, kwargs), daemon=True).start()
        return None
    return _hook


def register(ctx):
    """Register bundled skills and the status-display lifecycle hooks."""
    skills_dir = Path(__file__).parent / "skills"
    for child in sorted(skills_dir.iterdir()):
        skill_md = child / "SKILL.md"
        if child.is_dir() and skill_md.exists():
            ctx.register_skill(child.name, skill_md)

    for event, state in HOOK_STATES.items():
        ctx.register_hook(event, _make_hook(state))

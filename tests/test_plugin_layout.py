"""Every host reads this plugin straight from the repo root.

The Codex catalog once pointed at a ./plugins/agent-glance bundle. Grok also
scans Claude marketplace clones and treats plugins/<name>/ as a plugin, so it
bound the name agent-glance to that bundle, won the scope-precedence contest
against its own install, and silently dropped the hooks. Codex works fine with
"./", so the bundle is gone and these tests keep it gone.
"""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKILLS = ("agent-glance", "ag-setup", "ag-status", "ag-test", "ag-theme", "ag-restore")


def load(rel):
    return json.loads((ROOT / rel).read_text())


class NoNestedBundleTest(unittest.TestCase):
    def test_no_plugins_bundle(self):
        self.assertFalse(
            (ROOT / "plugins").exists(),
            "a plugins/<name>/ bundle makes grok shadow its own install",
        )

    def test_codex_catalog_points_at_repo_root(self):
        path = load(".agents/plugins/marketplace.json")["plugins"][0]["source"]["path"]
        self.assertEqual(path, "./", "codex reads the repo root, like every other host")


class GrokManifestTest(unittest.TestCase):
    """Flat path keys, hooks referenced as a file — matches epic-harness main."""

    def setUp(self):
        self.manifest = load(".grok-plugin/plugin.json")

    def test_uses_flat_path_keys(self):
        self.assertNotIn("components", self.manifest, "grok reads flat keys, not a components object")
        self.assertEqual(self.manifest.get("skills"), "./skills/")

    def test_hooks_point_at_the_single_hook_file(self):
        self.assertEqual(self.manifest.get("hooks"), "./hooks/hooks.json")
        self.assertTrue((ROOT / "hooks" / "hooks.json").is_file())

    def test_no_duplicate_hooks_copy(self):
        self.assertFalse(
            (ROOT / ".grok-plugin" / "hooks.json").exists(),
            "hooks live at hooks/hooks.json only; a copy here is never read",
        )


class SkillsTest(unittest.TestCase):
    """Commands are Claude-only, so every entry point ships as a skill."""

    def test_no_commands_directory(self):
        self.assertFalse((ROOT / "commands").exists())

    def test_manifests_declare_no_commands(self):
        for rel in (".grok-plugin/plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            self.assertNotIn("commands", load(rel), "{} still declares commands".format(rel))

    def test_every_skill_has_a_skill_md(self):
        for name in SKILLS:
            self.assertTrue(
                (ROOT / "skills" / name / "SKILL.md").is_file(),
                "skills/{}/SKILL.md is missing".format(name),
            )


class VersionTest(unittest.TestCase):
    def test_all_manifests_agree(self):
        versions = {rel: load(rel)["version"] for rel in (
            "plugin.json",
            ".grok-plugin/plugin.json",
            ".claude-plugin/plugin.json",
            ".codex-plugin/plugin.json",
        )}
        self.assertEqual(len(set(versions.values())), 1, "version drift: {}".format(versions))


if __name__ == "__main__":
    unittest.main()

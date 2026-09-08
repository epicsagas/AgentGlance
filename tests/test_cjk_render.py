"""Issue #2: cross-platform CJK font fallback + display-width-aware text.

A subtitle that renders fine with Latin input can overflow the 240x240
canvas or turn into tofu (☐☐☐) once Korean/CJK text reaches _trim/_wrap/
_font. These tests lock the display-width and word-boundary behavior.
"""

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script():
    path = ROOT / "scripts" / "agent_glance.py"
    spec = importlib.util.spec_from_file_location("agent_glance", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TrimTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ag = load_script()

    def test_narrow_text_unchanged_under_limit(self):
        self.assertEqual(self.ag._trim("hello world", 40), "hello world")

    def test_wide_text_respects_display_width(self):
        # 30 Hangul chars = 60 display columns; trimmed result must fit 38.
        out = self.ag._trim("한글테스트" * 6, 38)
        self.assertLessEqual(self.ag._dispw(out), 38)
        self.assertTrue(out.endswith("…"))

    def test_mixed_text_counts_wide_as_two(self):
        # 20 wide + 20 narrow chars = 60 columns > 40; must be trimmed.
        out = self.ag._trim("한" * 20 + "a" * 20, 40)
        self.assertLessEqual(self.ag._dispw(out), 40)


class WrapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ag = load_script()

    def _wrap(self, text, font, max_w, max_lines=3):
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (240, 240))
        return self.ag._wrap(text, font, max_w, ImageDraw.Draw(img), max_lines=max_lines)

    def test_cjk_wraps_within_max_width(self):
        from PIL import Image, ImageDraw
        font = self.ag._font(18, cjk=True)
        img = Image.new("RGB", (240, 240))
        d = ImageDraw.Draw(img)
        for ln in self._wrap("한글" * 40, font, 200):
            self.assertLessEqual(d.textlength(ln, font=font), 200)

    def test_latin_words_not_split_midword(self):
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (240, 240))
        d = ImageDraw.Draw(img)
        font = self.ag._font(18, cjk=True)
        text = "supercalifragilistic tokenized boundaries"
        # max_w fits the longest word on its own line but not all three words:
        # wraps must break between words, never mid-word.
        max_w = int(d.textlength("supercalifragilistic", font=font)) + 2
        lines = self.ag._wrap(text, font, max_w, d, max_lines=5)
        joined = " ".join(lines)
        for w in text.split():
            self.assertIn(w, joined)

    def test_oversized_single_token_hard_split(self):
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (240, 240))
        d = ImageDraw.Draw(img)
        font = self.ag._font(18, cjk=True)
        lines = self.ag._wrap("A" * 200, font, 100, d, max_lines=10)
        self.assertGreater(len(lines), 1)
        for ln in lines:
            self.assertLessEqual(d.textlength(ln, font=font), 100)

    def test_explicit_newline_respected(self):
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (240, 240))
        d = ImageDraw.Draw(img)
        font = self.ag._font(18, cjk=True)
        lines = self.ag._wrap("alpha\nbeta", font, 200, d, max_lines=3)
        self.assertEqual(lines[0], "alpha")
        self.assertEqual(lines[1], "beta")


class FontDiscoveryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ag = load_script()

    def test_candidates_cover_all_platforms(self):
        cjk = " ".join(self.ag.CJK_FONT_CANDIDATES)
        latin = " ".join(self.ag.LATIN_FONT_CANDIDATES)
        self.assertIn("/System/Library/Fonts", cjk)          # macOS
        self.assertIn("/usr/share/fonts", cjk)               # Linux
        self.assertIn("malgun.ttf", cjk)                     # Windows
        self.assertIn("msyh", cjk)
        self.assertIn("/usr/share/fonts", latin)
        self.assertIn("arial", latin)

    def test_font_returns_something(self):
        self.assertIsNotNone(self.ag._font(18))
        self.assertIsNotNone(self.ag._font(18, cjk=True))


class RenderSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ag = load_script()

    def test_cjk_subtitle_renders(self):
        out = os.path.join(tempfile.mkdtemp(), "smoke.gif")
        self.ag.render("working", sub="프로젝트 초기화 중 — 파일 검증", info={"model": "테스트모델", "ctx": 1234}, out=out)
        self.assertTrue(os.path.getsize(out) > 0)

    def test_long_cjk_subtitle_renders(self):
        out = os.path.join(tempfile.mkdtemp(), "smoke.gif")
        self.ag.render("working", sub="한" * 60, info={}, out=out)
        self.assertTrue(os.path.getsize(out) > 0)


if __name__ == "__main__":
    unittest.main()

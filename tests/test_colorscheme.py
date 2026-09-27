"""Tests für die Erzeugung des Farbschemas "Privos Dark"."""

import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "make_colorscheme", os.path.join(ROOT, "branding", "make-colorscheme.py"))
mc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mc)

SAMPLE = """[ColorEffects:Disabled]
Color=56,56,56

[Colors:Selection]
BackgroundNormal=61,174,233
ForegroundLink=29,153,243

[Colors:Window]
BackgroundNormal=32,35,38
ForegroundNormal=252,252,252
DecorationFocus=61,174,233

[General]
ColorScheme=BreezeDark
Name=Breeze Dark
Name[de]=Breeze Dunkel
"""


class ColorSchemeTests(unittest.TestCase):
    def test_accent_and_background_replaced(self):
        out = mc.convert(SAMPLE)
        self.assertNotIn("61,174,233", out)
        self.assertIn("BackgroundNormal=76,167,183", out)
        self.assertIn("BackgroundNormal=20,29,33", out)
        self.assertIn("ForegroundLink=142,203,211", out)

    def test_unrelated_values_untouched(self):
        out = mc.convert(SAMPLE)
        self.assertIn("ForegroundNormal=252,252,252", out)
        self.assertIn("Color=56,56,56", out)

    def test_no_partial_triplet_match(self):
        self.assertEqual(mc.convert("X=161,174,233\n"), "X=161,174,233\n")

    def test_name_and_id(self):
        out = mc.convert(SAMPLE)
        self.assertIn("Name=Privos Dark", out)
        self.assertIn("ColorScheme=PrivosDark", out)
        self.assertNotIn("Name[de]", out)


if __name__ == "__main__":
    unittest.main()

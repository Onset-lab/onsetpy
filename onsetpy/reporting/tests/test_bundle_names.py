from unittest import TestCase

from onsetpy.reporting.bundle_names import get_bundle_full_name


class TestGetBundleFullName(TestCase):
    def test_exact_abbreviation(self):
        self.assertEqual(get_bundle_full_name("CC_7"), "Corpus callosum - Splenium")

    def test_hemisphere_suffix(self):
        self.assertEqual(get_bundle_full_name("AF_L"), "Arcuate fasciculus (left)")
        self.assertEqual(get_bundle_full_name("CST_R"), "Corticospinal tract (right)")
        self.assertEqual(
            get_bundle_full_name("SLF_II_right"),
            "Superior longitudinal fasciculus II (right)",
        )
        self.assertEqual(get_bundle_full_name("UF_lh"), "Uncinate fasciculus (left)")

    def test_unknown_abbreviation(self):
        self.assertIsNone(get_bundle_full_name("FOO_L"))
        self.assertIsNone(get_bundle_full_name("FOO_X"))

    def test_custom_names_take_precedence(self):
        custom = {"AF": "Custom arcuate", "CST_L": "Left motor tract"}
        self.assertEqual(get_bundle_full_name("AF_R", custom), "Custom arcuate (right)")
        self.assertEqual(get_bundle_full_name("CST_L", custom), "Left motor tract")
        self.assertEqual(
            get_bundle_full_name("CST_R", custom), "Corticospinal tract (right)"
        )

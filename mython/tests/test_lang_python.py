#! /usr/bin/env python
# ______________________________________________________________________
# Module imports

import os
import unittest

import mython.lang.python as mlp

# ______________________________________________________________________
# Module data

KNOWN_VERSIONS = (
    (2, 6),
    (2, 7),
    (3, 2),
    (3, 3),
)

# ______________________________________________________________________
# Class definition

# TODO: repeatedly email this file to comp.lang.python and test via
# peer-review...or would that be TestCompLangPython... (*smirk*)

class TestLangPython(unittest.TestCase):
    def test_get_version_path(self):
        self.assertTrue(os.path.exists(mlp.get_version_path()))
        for version_info in KNOWN_VERSIONS:
            self.assertTrue(os.path.exists(mlp.get_version_path(version_info)))

    def test_get_grammar_path(self):
        self.assertTrue(os.path.exists(mlp.get_grammar_path()))
        for version_info in KNOWN_VERSIONS:
            self.assertTrue(os.path.exists(mlp.get_grammar_path(version_info)))

    def test_get_asdl_path(self):
        self.assertTrue(os.path.exists(mlp.get_asdl_path()))
        for version_info in KNOWN_VERSIONS:
            self.assertTrue(os.path.exists(mlp.get_asdl_path(version_info)))

# ______________________________________________________________________

if __name__ == "__main__":
    unittest.main()

# ______________________________________________________________________
# End of test_lang_python.py

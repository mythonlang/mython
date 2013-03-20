#! /usr/bin/env python
# ______________________________________________________________________
# Module imports

import unittest
import os
import mython.myparser

# ______________________________________________________________________
# Module data

MYPATH = os.path.join(os.path.split(mython.myparser.__file__)[0],
                      'tests', 'test_parser_0_0_2.my')

# ______________________________________________________________________
# Class definition

class TestMyParser(unittest.TestCase):
    def test_myparser_string(self):
        self.assertTrue(mython.myparser.main())

    def test_myparser_file(self):
        self.assertTrue(mython.myparser.main(MYPATH))

# ______________________________________________________________________

if __name__ == "__main__":
    unittest.main()

# ______________________________________________________________________
# End of test_myparser.py

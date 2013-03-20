#! /usr/bin/env python
# ______________________________________________________________________
# Module imports

import unittest
import mython.myast

# ______________________________________________________________________
# Class definition

class TestMyAST(unittest.TestCase):
    def test_myast(self):
        mython.myast.main()

# ______________________________________________________________________
# Main routine

if __name__ == "__main__":
    unittest.main()

# ______________________________________________________________________
# End of test_myast.py

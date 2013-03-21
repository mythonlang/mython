#! /usr/bin/env python
# ______________________________________________________________________
# Module imports

from __future__ import absolute_import

import unittest

from .test_myast import TestMyAST
from .test_myparser import TestMyParser
from .test_cst import TestCST
from .test_lang_python import TestLangPython

# ______________________________________________________________________

if __name__ == "__main__":
    unittest.main()

# ______________________________________________________________________
# End of mython/tests/__main__.py

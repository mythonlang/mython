import io
import os
import sys
import unittest
from mython.__main__ import main


EXPECTED = '''You should see this at compile time!
You should see this at import time!
You should see this at run time!
You should see this at eval time!
'''


class TestTest04(unittest.TestCase):
    def test_test04(self):
        stdout = sys.stdout
        test_stdout = io.StringIO()
        sys.argv = ('mython', os.path.join(os.path.dirname(__file__), 'test04.my'))
        sys.stdout = test_stdout
        main()
        sys.stdout = stdout
        self.assertEqual(test_stdout.getvalue(), EXPECTED)


if __name__ == "__main__":
    unittest.main()

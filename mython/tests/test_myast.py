#! /usr/bin/env python
# ______________________________________________________________________
# Module imports

import unittest, ast

import mython.myast
import mython.myparser

# ______________________________________________________________________
# Module definitions

TEST_MYEXPR_SRCS = (
    ('\n![bang]<bang>\n', True, 'bang'),
    ('\n!(  bingo )\n\n', False, '  bingo '),
)

TEST_MYSTMT_SRCS = [
    '''my[foo] bar(baz):
    biz

    boz

bar.explode(42)
''',
]

TEST_MYSTMT_SRCS.extend(mython.myparser.TEST_STRINGS)

# ______________________________________________________________________
# Class definition

class TestMyAST(unittest.TestCase):
    def test_myast(self):
        mython.myast.main()

    def test_myexpr(self):
        myparserobj = mython.myparser.MyParser()
        mytransformer = mython.myast.MyConcreteTransformer()
        for test_str, has_elang, expected_content in TEST_MYEXPR_SRCS:
            test_mycst = myparserobj.parse_string(test_str)
            test_myast = mytransformer.handle_node(test_mycst)
            self.assertTrue(len(test_myast.body) == 1)
            mystmt = test_myast.body[0]
            self.assertTrue(isinstance(mystmt, ast.Expr))
            self.assertTrue(isinstance(mystmt.value, mython.myast.MyExpr))
            self.assertTrue((not has_elang) or mystmt.value.elang)
            self.assertEqual(mystmt.value.estr, expected_content)

    def test_mystmt(self):
        myparserobj = mython.myparser.MyParser()
        mytransformer = mython.myast.MyConcreteTransformer()
        for test_str in TEST_MYSTMT_SRCS:
            cstobj = myparserobj.parse_string(test_str)
            astobj = mytransformer.handle_node(cstobj)
            self.assertTrue(len(astobj.body) >= 1)
            self.assertTrue(isinstance(astobj.body[0], mython.myast.MyStmt))
            # TODO: add more checks on result

# ______________________________________________________________________
# Main routine

if __name__ == "__main__":
    unittest.main()

# ______________________________________________________________________
# End of test_myast.py

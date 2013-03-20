#! /usr/bin/env python
# ______________________________________________________________________
# Module imports

import unittest, symbol, parser

import mython.cst
import mython.myparser

# ______________________________________________________________________
# Module data

TEST_SOURCE = '''
def foo():
    x = 44
    if x > 4:
       pass
'''

# ______________________________________________________________________
# Class definitions

class VisitPassStmt(mython.cst.ConcreteNodeVisitor):
    def __init__(self):
        super(VisitPassStmt, self).__init__(symbol.sym_name)
        self.saw_pass = False

    def visit_pass_stmt(self, _):
        self.saw_pass = True

# ______________________________________________________________________

class TestCST(unittest.TestCase):
    def test_py_cst_visitor(self):
        transformer = mython.cst.PyConcreteToMyConcreteTransformer()
        visitor = VisitPassStmt()
        visitor.visit(
            transformer.visit(
                parser.st2tuple(
                    parser.suite(TEST_SOURCE))))
        self.assertTrue(visitor.saw_pass)

    def test_my_cst_visitor(self):
        parserobj = mython.myparser.MyParser()
        visitor = VisitPassStmt()
        visitor.visit(parserobj.parse_string(TEST_SOURCE))
        self.assertTrue(visitor.saw_pass)

# ______________________________________________________________________
# Main routine

if __name__ == "__main__":
    unittest.main()

# ______________________________________________________________________
# End of test_cst.py

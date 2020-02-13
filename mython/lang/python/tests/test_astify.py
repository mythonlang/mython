import ast
import sys
import unittest
from mython.myparser import MyParser
from mython.lang.python import get_myhandler_class

test_ast = None
if sys.version_info[0] == 3:
    if sys.version_info[1] == 6:
        from mython.lang.python.python36.test import test_ast
    elif sys.version_info[1] == 7:
        from mython.lang.python.python37.test import test_ast
    elif sys.version_info[1] == 8:
        from mython.lang.python.python38.test import test_ast


def build_compiler():
    parsers = {'exec': MyParser(start_symbol='file_input'),
               'single': MyParser(start_symbol='single_input'),
               'eval': MyParser(start_symbol='eval_input')}
    handler = get_myhandler_class()()
    def mycompile(source, filename, mode, *args, **kws):
        cst = parsers[mode].parse_string(source)
        tree = handler.handle_node(cst)
        return tree
    return mycompile

mycompile = build_compiler()


class TestMyHandler(unittest.TestCase):
    @unittest.skipUnless(test_ast is not None,
                         'Testing unsupported Python version.')
    def test_exec_astification(self):
        maxDiff = self.maxDiff
        self.maxDiff = None
        try:
            idx = 1
            count = len(test_ast.exec_tests)
            for input, output in zip(test_ast.exec_tests,
                                     test_ast.exec_results):
                # XXX
                print('_'*60)
                print(f'{idx} of {count}:')
                print(input)
                test_tree = mycompile(input, '?', 'exec')
                myoutput = test_ast.to_tuple(test_tree)
                self.assertEqual(myoutput, output)
                idx += 1
        finally:
            self.maxDiff = maxDiff

    @unittest.skipUnless(test_ast is not None,
                         'Testing unsupported Python version.')
    def test_eval_astification(self):
        maxDiff = self.maxDiff
        self.maxDiff = None
        try:
            idx = 1
            count = len(test_ast.eval_tests)
            for input, output in zip(test_ast.eval_tests,
                                     test_ast.eval_results):
                # XXX
                print('_'*60)
                print(f'{idx} of {count}:')
                print(input)
                tree = mycompile(input, '?', 'eval')
                myoutput = test_ast.to_tuple(tree)
                self.assertEqual(myoutput, output)
                idx += 1
        finally:
            self.maxDiff = maxDiff


if __name__ == '__main__':
    unittest.main()

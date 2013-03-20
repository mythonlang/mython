#! /usr/bin/env python
'''
Utilities for dealing with concrete syntax, intented to be similar to
Python's ast utility module.
'''
# ______________________________________________________________________
# Module imports

import ast
import token

# ______________________________________________________________________
# Module data

__DEBUG__ = False

# ______________________________________________________________________
# Class definitions

class ConcreteNodeVisitor(object):
    def __init__(self, symbol_names=None):
        self.symbol_names = {} if symbol_names is None else symbol_names

    def visit(self, node):
        if __DEBUG__:
            print("Visiting: %s\n" % str(node))
        data = node[0]
        if isinstance(data, tuple):
            postfix = 'token'
        else:
            postfix = self.symbol_names.get(data, str(data))
        method = 'visit_' + postfix
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        data, children = node
        for child in children:
            self.visit(child)

# ______________________________________________________________________

class ConcreteNodeTransformer(ConcreteNodeVisitor):
    def generic_visit(self, node):
        data, children = node
        children[:] = list(transformed_child for transformed_child in
                               (self.visit(child) for child in children)
                           if transformed_child is not None)
        return node

# ______________________________________________________________________

class PyConcreteToMyConcreteTransformer(ConcreteNodeTransformer):
    def generic_visit(self, node):
        if node[0] < token.NT_OFFSET:
            ret_val = (node, [])
        else:
            ret_val = node[0], list(self.visit(child) for child in node[1:])
        return ret_val

# ______________________________________________________________________
# End of cst.py

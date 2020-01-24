#! /usr/bin/env python
# ______________________________________________________________________
# Module imports

import token
import ast
import sys

from mython.lang.python.astify import MyHandler
from mython.lang.python.python36.astify36 import My36Handler
from mython.lang.python.python37.astify37 import My37Handler
from mython.lang.python.python38.astify38 import My38Handler

# ______________________________________________________________________
# Class definitions

class MyStmt(ast.stmt):
    '''In ASDL:
    stmt = ...
         | MyStmt(expr? lang,
                  identifier? name,
                  arguments? args,
                  string body)
         | ...
    '''
    _fields = ('lang', 'name', 'args', 'body')

# ______________________________________________________________________

class MyExpr(ast.expr):
    '''In ASDL:
    expr = ...
         | MyExpr(expr? elang, string estr)
         | ...
    '''
    _fields = ('elang', 'estr')

# ______________________________________________________________________

def get_base_class():
    assert sys.version_info[0] == 3
    return {
        6: My36Handler,
        7: My37Handler,
        8: My38Handler,
    }.get(sys.version_info[1], MyHandler)

class MyConcreteTransformer(get_base_class()):
    def handle_not_test(self, node):
        children = node[1]
        child_count = len(children)
        assert child_count > 0
        first_child = children[0][0]
        if isinstance(first_child, tuple) and (first_child[1] == '!'):
            location = first_child[2]
            elang = None
            if child_count == 2:
                estr = self.handle_node(children[1])
            else:
                assert child_count == 5
                elang = self.handle_node(children[2])
                estr = self.handle_node(children[4])
            ret_val = MyExpr(elang, estr,
                             lineno=location[0], col_offset=location[1])
        else:
            ret_val = super(MyConcreteTransformer, self).handle_not_test(node)
        return ret_val

    def handle_compound_stmt(self, node):
        children = node[1]
        child_count = len(children)
        assert child_count > 0
        first_child = children[0][0]
        if isinstance(first_child, tuple) and (first_child[1] == 'my'):
            location = first_child[2]
            lang = None
            name = None
            params = None
            index = 1
            crnt_child = children[index][0]
            if isinstance(crnt_child, tuple) and (crnt_child[0] == token.LSQB):
                lang = self.handle_node(children[index + 1])
                assert children[index + 2][0][0] == token.RSQB
                index += 3
                crnt_child = children[index][0]
            if isinstance(crnt_child, tuple) and (crnt_child[0] == token.NAME):
                name = crnt_child[1]
                index += 1
                crnt_child = children[index][0]
                if crnt_child == 'parameters':
                    params = self.handle_node(children[index])
                    index += 1
            assert index + 1 == child_count, (index + 1, child_count)
            body = self.handle_node(children[index])
            ret_val = MyStmt(lang, name, params, body,
                             lineno=location[0], col_offset=location[1])
        else:
            ret_val = super(MyConcreteTransformer,
                            self).handle_compound_stmt(node)
        return ret_val

    def handle_mysuite(self, node):
        children = node[1]
        assert len(children) == 3
        if children[1][0][0] == token.NEWLINE:
            ret_val = children[2][0][1]
        else:
            ret_val = children[1][0][1]
        return ret_val

    def handle_myexpr(self, node):
        _, children = node
        assert len(children) == 2
        return children[-1][0][1][:-1]

    handle_myexpr1 = handle_myexpr

# ______________________________________________________________________

class MyAbstractTransformer(ast.NodeTransformer):
    def transform(self, node, env):
        self.env = env.copy()
        result = self.visit(node)
        env1 = self.env
        del self.env
        return result, env1

    def visit_MyStmt(self, node):
        myeval = self.env['myeval']
        if node.lang is None:
            lang = 'mython'
        else:
            lang = ast.Expression(node.lang)
        lang_fn, env = myeval(lang, self.env)
        env = env.copy()
        env['lineno'] = node.lineno
        env['col_offset'] = node.col_offset
        ret_val, env = lang_fn(node.name, node.args, node.body, env)
        return ret_val

    def visit_MyExpr(self, node):
        raise NotImplementedError()

# ______________________________________________________________________
# Main (self-test) routine

def main(*args, **kws):
    import ast
    for myast_cls in (MyStmt, MyExpr):
        assert issubclass(myast_cls, ast.AST), myast_cls
        fields = range(len(myast_cls._fields))
        node = myast_cls(*fields)
        results = list(expected == actual
                       for expected, actual in zip(zip(myast_cls._fields,
                                                       fields),
                                                   ast.iter_fields(node)))
        assert all(results), (node, results)

# ______________________________________________________________________

if __name__ == "__main__":
    main()

# ______________________________________________________________________
# End of mython.myast

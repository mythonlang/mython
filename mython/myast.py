#! /usr/bin/env python
# ______________________________________________________________________
# Module imports

import _ast

# ______________________________________________________________________
# Class definitions

class MyStmt(_ast.stmt):
    '''In ASDL:
    stmt = ...
         | MyStmt(expr lang,
                  identifier name,
                  arguments args,
                  string body,
                  int body_ofs)
         | ...
    '''
    _fields = ('lang', 'name', 'args', 'body', 'body_ofs')

# ______________________________________________________________________

class MyExpr(_ast.expr):
    '''In ASDL:
    expr = ...
         | MyExpr(expr elang, string estr)
         | ...
    '''
    _fields = ('elang', 'estr')

# ______________________________________________________________________
# Main (self-test) routine

def main(*args, **kws):
    import ast
    for myast_cls in (MyStmt, MyExpr):
        assert issubclass(myast_cls, _ast.AST), myast_cls
        fields = range(len(myast_cls._fields))
        node = myast_cls(*fields)
        results = list(expected == actual
                       for expected, actual in zip(zip(myast_cls._fields,
                                                       fields),
                                                   ast.iter_fields(node)))
        assert all(results), (node, results)

if __name__ == "__main__":
    main()

# ______________________________________________________________________
# End of mython.myast

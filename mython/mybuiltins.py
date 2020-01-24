#! /usr/bin/env python
# ______________________________________________________________________
"""
The built-ins of the Mython compile time environment.
"""
# ______________________________________________________________________
# Module imports

import sys as _sys
import ast as _pyast
import os as _os
import stat as _stat
import struct as _struct
import marshal as _marshal
import imp as _imp
import tokenize as _tokenize
import pprint as _pprint

from . import myparser as _myparser
from . import myast as _myast

# ______________________________________________________________________
# Function definitions

def myfrontend(text, env):
    "Parse and translate the given Mython source into a Python module AST."
    abstract_tree, env1 = env.get('myparse', myparse)(text, env)
    return env1.get('mydesugar', mydesugar)(abstract_tree, env1)

# ______________________________________________________________________

def myparse(text, env):
    """Given a source string, return a Mython abstract syntax tree."""
    # FIXME: Reintroduce better syntax error handling based on environment.
    parser = _myparser.MyParser(start_symbol=env.get('start_symbol', 'file_input'))
    concrete_tree = parser.parse_string(text)
    transformer = _myast.MyConcreteTransformer()
    return transformer.handle_node(concrete_tree), env

# ______________________________________________________________________

def mydesugar(ast, env):
    """Transform a Mython abstract syntax tree into a pure Python
    abstract syntax tree."""
    transformer = _myast.MyAbstractTransformer()
    ast1, env1 = transformer.transform(ast, env)
    ast2 = _myast.ast.fix_missing_locations(ast1)
    return ast2, env1

# ______________________________________________________________________

def mybackend(tree, env):
    """Given what is presumably a Python abstract syntax tree, generate a
    code object for that tree."""
    assert isinstance(tree, _pyast.AST)
    filename = env.get("filename", "<string>")
    entry_point = 'eval' if isinstance(tree, _pyast.Expression) else 'exec'
    code_obj = compile(tree, filename, entry_point)
    return code_obj, env

# ______________________________________________________________________

def myeval(code, env = None):
    """myeval(code, env)
    Evaluate the given abstract syntax tree, ast, in the environment, env.
    Returns the evaluation result."""
    if env is None:
        env = initial_environment()
    if isinstance(code, str):
        # FIXME: There is a bug somewhere in the environment chaining logic
        # that requires us to copy the environment before mutating it.
        env0 = env.copy()
        start_symbol = env0.get('start_symbol')
        env0['start_symbol'] = 'eval_input'
        pyexpr, env1 = env.get('myfrontend', myfrontend)(code, env0)
        pyast = _pyast.Expression(pyexpr)
        env1['start_symbol'] = start_symbol
    else:
        assert isinstance(code, _pyast.AST)
        pyast, env1 = env.get('mydesugar', mydesugar)(code, env)
    code_obj, env2 = env1.get('mybackend', mybackend)(pyast, env1)
    return eval(code_obj, env2), env2

# ______________________________________________________________________

def myescape (obj):
    """myescape(obj) Translate the given AST into a Python AST
    that can be evaluated to construct the given AST."""
    if isinstance(obj, _pyast.AST):
        ast_type = type(obj)
        esc_args = [myescape(getattr(obj, ctor_arg))
                    for ctor_arg in ast_type._fields
                    # FIXME: Investigate possible stink; Optional fields
                    # at the end of the field list may be elided by CPython.
                    # For example, constants' kind field goes missing if not
                    # explicitly given to the ctor.
                    if hasattr(obj, ctor_arg)
                    ]
        ret_val = _pyast.Call(_pyast.Name(ast_type.__name__, _pyast.Load()),
                              esc_args, [])
    elif isinstance(obj, dict):
        keyobjs = obj.keys()
        ret_val = _pyast.Dict(
            [myescape(keyobj) for keyobj in keyobjs],
            [myescape(obj[keyobj]) for keyobj in keyobjs])
    elif isinstance(obj, list):
        ret_val = _pyast.List([myescape(subobj) for subobj in obj],
                                    _pyast.Load())
    elif isinstance(obj, tuple):
        ret_val = _pyast.Tuple([myescape(subobj) for subobj in obj],
                                    _pyast.Load())
    elif isinstance(obj, int):
        ret_val = _pyast.Num(obj)
    elif isinstance(obj, float):
        ret_val = _pyast.Num(obj)
    elif isinstance(obj, str):
        ret_val = _pyast.Str(obj)
    elif obj is None:
        ret_val = _pyast.Name("None", _pyast.Load())
    else:
        raise NotImplementedError("Don't know how to escape '%r'!" % (obj))
    return ret_val

# ______________________________________________________________________

def mython (name, args, code, env0):
    """mython(name, args, code, env0)
    Quotation function for Mython."""
    stmt_lst = []
    ast, env1 = myparse(code, env0)
    esc_ast = myescape(ast)
    if name is not None:
        env1[name] = ast
        # XXX Add line and position information to the constructed syntax.
        stmt_lst = [_pyast.Assign([_pyast.Name(name, _pyast.Store())], esc_ast)]
    else:
        stmt_lst = [_pyast.Expr(esc_ast)]
    return stmt_lst, env1

# ______________________________________________________________________

def myfront (name, args, code, env0):
    """myfront(name, args, code, env0)
    Pragma function for MyFront."""
    ast, env = myfrontend(code, env0)
    env = env.copy()
    if name is not None:
        env[name] = ast
    _, env = myeval(ast, env)
    return [], env

# ______________________________________________________________________

def makequote (processor, use_env = False):
    """Given a 'source processor', return a quotation function.

    The 'source processor' should be a function (parser, interpreter,
    translator, etc.) that given a string, returns a Python object.
    The returned object should define a __repr__() method that is
    valid Mython syntax (this is true of most of the fundamental
    types).

    The optional use_env argument causes makequote() to use the given
    processor function to possibly mutate the environment.  If use_env
    is set, the processor function should accept two parameters: a
    string, and an environment.  In this case, the processor should
    return a Python object and a possibly modified environment.
    """
    if not use_env:
        def _quote (name, args, code, env):
            obj = processor(code)
            ast, env = env["myfrontend"]("%s = %r\n" % (name, obj) if name else
                                         "%r\n" % (obj,), env)
            return ast.body, env
    else:
        def _quote (name, args, code, env):
            obj, env = processor(code, env)
            ast, env = env["myfrontend"]("%s = %r\n" % (name, obj) if name else
                                         "%r\n" % (obj,), env)
            return ast.body, env
    _quote.__name__ = processor.__name__ + "_quote"
    return _quote

# ______________________________________________________________________

def makedesugar (desugar):
    """Given a string transformer from an arbitrary string to Mython
    module source (exec-style), create a quotation function that runs
    the string transformer and tries to compile the result.  Ignores
    the name."""
    def _desugar (name, code, env):
        ast, env = env["myfrontend"](desugar(code), env)
        return ast.body, env
    return _desugar

# ______________________________________________________________________

def output_module_co (name, code_obj, env):
    """output_module_co()
    """
    if name is not None:
        outfile = open(name, "wb")
        outfile.write(_imp.get_magic())
        if "filename" in env:
            mtime = _os.path.getmtime(env["filename"])
        else:
            mtime = 0
        outfile.write(_struct.pack("<i", mtime))
        outfile.write(_marshal.dumps(code_obj))
        outfile.close()
    return env

# ______________________________________________________________________

def _load_file (filename, env):
    """_load_file()
    Given a file name, and an environment, load the file, and
    extend/modify the environment with information about the current
    file to be processed."""
    with (open(filename)) as fileobj:
        text = fileobj.read()
    env["filename"] = filename
    env["output_file"] = "%s.pyc" % (_os.path.splitext(filename)[0])
    return text, env

# ______________________________________________________________________

def mycompile_file (filename, env = None):
    """mycompile_file(filename, env) -> co, env
    """
    if env is None:
        env = initial_environment()
    text, env = _load_file(filename, env)
    frontend = env.get("myfrontend", myfrontend)
    ast, env = frontend(text, env)
    backend = env.get("mybackend", mybackend)
    return backend(ast, env)

# ______________________________________________________________________

def mycompile_file_to_pyc (filename, env = None):
    """mycompile_file_to_pyc(filename, env) -> env

    Compile the given Mython file into Python bytecode, writing a .pyc
    file in the same directory.  Returns the modified, post
    compilation environment."""
    co, env = mycompile_file(filename, env)
    local_output_module_co = env.get("output_module_co", output_module_co)
    # XXX I'm not sure this is a good idea: keeping the output
    # filename in the environment.
    output_file = env.get("output_file",
                          "%s.pyc" % _os.path.splitext(filename)[0])
    env = local_output_module_co(output_file, co, env)
    return env

# ______________________________________________________________________

def warn (node, warning, env):
    """warn(node, warning, env) -> env

    Format and handle a warning message from the compiler."""
    lineno_str = "???"
    if hasattr(node, "lineno"):
        lineno_str = str(node.lineno)
    actual_warning = ('Warning, file "%s", line %s: %s\n' %
                      (env["filename"], lineno_str, warning))
    _sys.stderr.write(actual_warning)
    return env

# ______________________________________________________________________

def _check_my_file (parent_path, module_name):
    """_check_my_file(parent_path, module_name) -> string?

    Given a file path and base module file path (without a file
    extension given), check to see if a Mython module exists and needs
    to be recompiled.  Returns the path to the Mython module if so,
    None otherwise."""
    ret_val = None
    filename_base = _os.path.join(parent_path, module_name)
    my_filename = _os.path.extsep.join((filename_base, "my"))
    pyc_filename = _os.path.extsep.join((filename_base, "pyc"))
    try:
        my_filename_stat = _os.stat(my_filename)
        try:
            pyc_filename_stat = _os.stat(pyc_filename)
            my_mtime = my_filename_stat[_stat.ST_MTIME]
            pyc_mtime = pyc_filename_stat[_stat.ST_MTIME]
            if pyc_mtime <= my_mtime:
                ret_val = my_filename
        except OSError:
            ret_val = my_filename
    except OSError:
        # XXX Maybe add a verbosity thing to say we checked...implying
        # an environment should be threaded along...
        pass
    return ret_val

# ______________________________________________________________________

def __myimport__ (name, global_env = None, local_env = None, from_list = None,
                  level = -1):
    """__myimport__(name, globals, locals, fromlist, level) -> module

    Compile-time import function.  Ideally this is compatible with
    Python's run-time __import__, with the exception that certain
    caveats apply to circular or non-existent imports (typically
    warnings will be generated, unless there is a compile-time
    circular dependency)."""
    # ____________________________________________________________
    # XXX I have no idea if this appropriate for __import__ compatibility.
    if global_env is None:
        global_env = initial_environment()
    if local_env is None:
        local_env = {}
    if from_list is None:
        from_list = []
    # ____________________________________________________________
    # Load parent modules
    module_path = name.split(".")
    parent_module = None
    if len(module_path) > 1:
        # XXX This is total puntage on the possibility of there being
        # an __init__.my.  Fix it.
        parent_module = __import__(".".join(module_path[:-1]),
                                   global_env.copy(),
                                   local_env, from_list, level)
    # ____________________________________________________________
    # Now see if the leaf module has a Mython file or not.
    mython_source = None
    parent_path = getattr(parent_module, "__path__", None)
    if parent_path is None:
        # XXX Could refine this to exclude paths that already have
        # importers sitting in sys.path_importer_cache.
        candidate_paths = _sys.path[:]
        mython_paths = _os.getenv("MYTHONPATH")
        if mython_paths:
            candidate_paths += mython_paths.split(_os.path.pathsep)
        # XXX This could circumvent requirements for a directory
        # being a Python package...what to do (besides get some wisdom)?
        module_dirpath = _os.path.join(*module_path)
        for candidate_path in candidate_paths:
            mython_source = _check_my_file(candidate_path, module_dirpath)
            if mython_source:
                break
    else:
        # XXX Will module.__path__ always be a list?  When does it
        # have more than one entry in that list?
        for path in parent_path:
            mython_source = _check_my_file(path, module_path[-1])
    if mython_source:
        mycompile_file_to_pyc(mython_source, global_env)
    # ____________________________________________________________
    # There should now be a .pyc there.  Let Python do it's thing.
    my_module = __import__(name, global_env, local_env, from_list, level)
    return my_module, global_env

# ______________________________________________________________________

def initial_environment ():
    ret_val = {}
    for key, value in globals().items():
        if (key[0] != "_") or (key in ("__myimport__",)):
            ret_val[key] = value
    return ret_val

# ______________________________________________________________________
# End of mybuiltins.py

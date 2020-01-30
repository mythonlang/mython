#! /usr/bin/env python
# ______________________________________________________________________
# Module imports

import os
import sys

from .astify import MyHandler
from .python36.astify36 import My36Handler
from .python37.astify37 import My37Handler
from .python38.astify38 import My38Handler

# ______________________________________________________________________
# Module data

MYPATH = os.path.abspath(os.path.split(__file__)[0])

# ______________________________________________________________________
# Function definitions

def get_version_path(version_info=None):
    """Return the absolute path to a folder that holds data to a
    specific Python version.  Uses sys.version_info by default or a
    user supplied tuple or named tuple.
    """
    if version_info is None:
        version_info = sys.version_info
    return os.path.join(MYPATH, 'python%s' % (
            ''.join(str(ver) for ver in version_info[:2])))

def get_grammar_path(version_info=None):
    """Return the absolute path to a pgen Grammar for a specific
    version of Python.  Defaults to the version of the current
    interpreter."""
    return os.path.join(get_version_path(version_info), 'Grammar')

def get_asdl_path(version_info=None):
    """Return the absolute path to an ASDL abstract syntax definition
    for a specific version of Python.  Defaults to the version of the
    current interpreter."""
    return os.path.join(get_version_path(version_info), 'Python.asdl')

def get_myhandler_class(version_info=None):
    """Return the concrete syntax tree to abstract syntax tree transformer
    class for the given Python version (default is sys.version_info)."""
    if version_info is None:
        version_info = sys.version_info
    assert version_info[0] == 3
    return {
        6: My36Handler,
        7: My37Handler,
        8: My38Handler,
    }.get(version_info[1], MyHandler)

# ______________________________________________________________________
# End of mython/lang/python/__init__.py

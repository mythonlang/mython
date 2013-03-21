#! /usr/bin/env python
# ______________________________________________________________________
# Module imports

import os
import sys

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

# ______________________________________________________________________
# End of mython/lang/python/__init__.py

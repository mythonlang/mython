#! /usr/bin/env python
import sys
import types

from . import mybuiltins

def main():
    for arg in sys.argv[1:]:
        co, _ = mybuiltins.mycompile_file(arg)
        mod = types.ModuleType('__main__')
        exec(co, mod.__dict__)


if __name__ == '__main__':
    main()

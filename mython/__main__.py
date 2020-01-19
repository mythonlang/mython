#! /usr/bin/env python
import sys

from . import mybuiltins

def main():
    for arg in sys.argv[1:]:
        mybuiltins.mycompile_file(arg)


if __name__ == '__main__':
    main()

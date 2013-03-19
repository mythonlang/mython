#! /usr/bin/env python
# ______________________________________________________________________
# Module imports

import os
import StringIO
import pprint

import pgen2.parser
import pgen2.pgen
import pgen2.dfa

from mython import nfa, trampoline, mylexer
import mython.lang.python

# ______________________________________________________________________
# Module data

MY_GRAMMAR_EXT="""
not_test: BANG ('[' test ']' myexpr1 | myexpr0)
compound_stmt: 'my' ['[' test ']'] [NAME [parameters]] mysuite
mysuite: ':' (MYSUITE NEWLINE | NEWLINE MYSUITE)
myexpr0: ('('|'{'|'<') MYEXPR
myexpr1: ('('|'['|'{'|'<') MYEXPR
"""

py_grammar_path = os.path.split(mython.lang.python.__file__)[0]

TEST_STRINGS=[
"""
my[namedtupledef] Point(x, y): pass
"""
]

__DEBUG__ = False

# ______________________________________________________________________
# Function definition(s)

def pgen_compose (pgen, pgen_st1, pgen_st2, start_symbol,
                  additional_tokens = None):
    nfa_grammar1 = pgen.handleStart(pgen_st1)
    nfa_grammar2 = pgen.handleStart(pgen_st2)
    nfa_composed = nfa.compose_nfas(nfa_grammar1, nfa_grammar2)
    grammar3 = pgen.generateDfaGrammar(nfa_composed, start_symbol)
    pgen.translateLabels(grammar3, additional_tokens)
    pgen.generateFirstSets(grammar3)
    grammar3[0] = map(tuple, grammar3[0])
    return pgen2.dfa.addAccelerators(tuple(grammar3))

# ______________________________________________________________________
# Class definition(s)

class MyParser(object):
    def __init__(self, start_symbol=None, base_grammar_file=None):
        self.pgen = pgen2.pgen.PyPgen()
        if base_grammar_file is None:
            base_grammar_file = os.path.join(py_grammar_path,
                                             'python27/Grammar')
        py_pgen_st = pgen2.parser.parse_file(base_grammar_file)
        my_ext_pgen_st = pgen2.parser.parse_string(MY_GRAMMAR_EXT)
        self.my_grammar = pgen_compose(
            self.pgen, py_pgen_st, my_ext_pgen_st, 'file_input',
            { 'BANG' : mylexer.BANG,
              'MYEXPR' : mylexer.MYEXPR,
              'MYSUITE' : mylexer.MYSUITE })
        self.handlers = trampoline.pgen_grammar_to_handlers(
            self.my_grammar, {})
        nonterminal_override_names = 'mysuite', 'myexpr0', 'myexpr1'
        nonterminal_overrides = ((dfa[1], dfa[0])
                                 for dfa in self.my_grammar[0]
                                 if dfa[1] in nonterminal_override_names)
        for nonterminal_name, nonterminal_index in nonterminal_overrides:
            handler = getattr(self, 'parse_%s' % nonterminal_name)
            self.handlers[nonterminal_name] = handler
            self.handlers[nonterminal_index] = handler
        self.start_symbol = (start_symbol if start_symbol is not None
                             else 'file_input')
        self.handlers['start'] = self.parse_start

    def parse_start(self, instream, outtree):
        yield self.start_symbol

    def parse_mysuite(self, instream, outtree):
        instream.start_mysuite()
        outtree.pushpop(instream.expect(':'))
        outtree.push('mysuite')
        if instream.test_lookahead(mylexer.tokenize.NEWLINE):
            outtree.pushpop(instream.expect(mylexer.tokenize.NEWLINE))
            outtree.pushpop(instream.expect(mylexer.MYSUITE))
        else:
            outtree.pushpop(instream.expect(mylexer.MYSUITE))
            outtree.pushpop(instream.expect(mylexer.tokenize.NEWLINE))
        outtree.pop()
        if False: yield 'dummy'

    def parse_myexpr(self, instream, outtree):
        outtree.push('myexpr')
        open_delim = instream.expect('(', '[', '{', '<')
        instream.start_myexpr(open_delim)
        outtree.pushpop(open_delim)
        outtree.pushpop(instream.expect(mylexer.MYEXPR))
        outtree.pop()
        if False: yield 'dummy'

    parse_myexpr0 = parse_myexpr
    parse_myexpr1 = parse_myexpr

    def parse_lineiter(self, lineiter, env = None):
        if env is None:
            env = {}
        line_offset = env.get("lineno", 1) - 1
        column_offset = env.get("column_offset", 0)
        filename = env.get("filename", "<unknown>")
        readliner = mylexer.MythonReadliner(lineiter)
        token_stream = mylexer.MythonTokenStream(
            readliner, lnum = line_offset, column_offset = column_offset)
        tree_builder = trampoline.TreeBuilder()
        try:
            tree_builder = trampoline.trampoline_parse(
                self.handlers, token_stream, tree_builder)
        except SyntaxError as syntax_err:
            if __DEBUG__:
                pprint.pprint(tree_builder.__dict__)
                # If debugging, don't mask the syntax error, just re-raise it.
                raise
            if syntax_err.args[0].startswith("Line"):
                err_str = "File '%s', l%s" % (filename, syntax_err.args[0][1:])
            else:
                err_str = "File '%s', %s" % (filename, syntax_err.args[0])
            raise SyntaxError(err_str)
        return tree_builder.tree

    def parse_file(self, filename, env=None):
        if env is None:
            env = {}
        if "filename" not in env:
            env = env.copy()
            env["filename"] = filename
        return self.parse_lineiter(open(filename).next, env)

    def parse_string(self, src_str, env = None):
        if env is None:
            env = {}
        if "filename" not in env:
            env = env.copy()
            env["filename"] = "<string>"
        return self.parse_lineiter(StringIO.StringIO(src_str).next, env)

# ______________________________________________________________________
# Main (self-test) routine

def main (*args):
    my_parser = MyParser()
    if args:
        for arg in args:
            tree = my_parser.parse_file(arg)
            pprint.pprint(tree)
    else:
        for test_string in TEST_STRINGS:
            tree = my_parser.parse_string(test_string)
            pprint.pprint(tree)

# ______________________________________________________________________

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])

# ______________________________________________________________________
# End of myparser2.py

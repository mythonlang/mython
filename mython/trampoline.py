#! /usr/bin/env python
# ______________________________________________________________________
"""Module trampoline.py

Jonathan Riehl
"""
# ______________________________________________________________________
# Module imports

import token

# ______________________________________________________________________
# Module data

__DEBUG__ = False

# ______________________________________________________________________
# Compatibility layer

# This is crud.  Maybe this kind of compatibility isn't worth it?
# Conversely, it seems wrong that __builtins__ can be a dictionary if
# the module is imported, or a module if the module is run as a
# script.

if type(__builtins__) == dict:
    define_next = "next" not in __builtins__.keys()
else:
    define_next = "next" not in __builtins__.__dict__.keys()

if define_next:
    def next (obj):
        return obj.next()

# ______________________________________________________________________
# Function definitions

class TokenStream (object):
    def __init__ (self, tokenizer):
        self.tokenizer = tokenizer
        self.next_token = None

    def tokenize (self):
        return next(self.tokenizer)

    def get_token (self):
        ret_val = None
        if self.next_token is None:
            ret_val = self.tokenize()
        else:
            ret_val = self.next_token
            self.next_token = None
        return ret_val

    def get_lookahead (self):
        ret_val = None
        if self.next_token is None:
            ret_val = self.tokenize()
            self.next_token = ret_val
        else:
            ret_val = self.next_token
        return ret_val

    def test_lookahead (self, *tokens):
        ret_val = False
        lookahead = self.get_lookahead()
        if lookahead[0] in tokens:
            ret_val = True
        elif lookahead[1] in tokens:
            ret_val = True
        return ret_val

    def expect (self, *tokens):
        crnt_token = self.get_token()
        if (crnt_token[0] not in tokens) and (crnt_token[1] not in tokens):
            raise SyntaxError("Got %s, expected %s." % (str(crnt_token),
                                                        str(token)))
        return crnt_token

# ______________________________________________________________________

class ExclusiveTokenStream (TokenStream):
    def __init__ (self, tokenizer, exclusion_set):
        TokenStream.__init__(self, tokenizer)
        self.excludes = exclusion_set

    def tokenize (self):
        ret_val = next(self.tokenizer)
        while ret_val[0] in self.excludes:
            ret_val = next(self.tokenizer)
        return ret_val

# ______________________________________________________________________

class TreeBuilder (object):
    def __init__ (self):
        self.tree = ('start', [])
        self.stack = [self.tree]

    def push (self, elem):
        node = (elem, [])
        self.stack[-1][1].append(node)
        self.stack.append(node)
        return node

    def pop (self):
        return self.stack.pop()

    def pushpop (self, elem):
        node = (elem, [])
        self.stack[-1][1].append(node)
        return node

# ______________________________________________________________________

def trampoline_parse (handlers, instream, outtree = None):
    """Parse a lexical stream using a set of handler generators."""
    if outtree is None:
        outtree = TreeBuilder()
    generator_stack = [handlers['start'](instream, outtree)]
    while generator_stack:
        try:
            next_gen = next(generator_stack[-1])
            generator_stack.append(handlers[next_gen](instream, outtree))
        except StopIteration:
            del generator_stack[-1]
    return outtree

# ______________________________________________________________________

def pgen_grammar_to_handlers (grammar, handlers):
    """Extend a trampoline map with handlers for a pgen grammar tuple."""
    dfas, labels, start, accel = grammar
    label_map = {}
    i = 0
    for label in labels:
        label_map[label] = i
        i += 1
    # Note that the old version of classify() (see
    # basil.lang.python.DFAParser) was very inefficient, doing a
    # linear search through the grammar labels.  Using a dictionary
    # should be faster.
    def classify (intoken):
        tok_type, tok_name, tok_start, tok_stop, tok_line = intoken
        if (tok_type == token.NAME) and ((tok_type, tok_name) in label_map):
            return label_map[(tok_type, tok_name)]
        return label_map.get((tok_type, None), -1)
    # TODO: Check for and add accelerators...
    assert accel
    for dfa in dfas:
        handler = dfa_to_handler(classify, dfa, labels)
        handlers[dfa[0]] = handler
        handlers[dfa[1]] = handler
    return handlers

# ______________________________________________________________________

def dfa_to_handler (classify, dfa, symbol_tab = None):
    """Convert a DFA to a generator compatible with trampoline_parse.

    Accepts a classify function used to map from a token to a symbol
    in the grammar (these are the indicies used for state
    transitions/accelerators), a deterministic state automaton tuple,
    and an optional symbol table.  Returns a generator function that
    conforms to the trampoline parser protocol.
    """
    dfa_num, dfa_name, dfa_initial, states = (dfa[0], dfa[1], dfa[2], dfa[3])
    def _parse_dfa (instream, outtree):
        if __DEBUG__:
            print("Parse:%s" % dfa_name)
        outtree.push(dfa_name)
        state = states[dfa_initial]
        while 1:
            arcs, (accel_upper, accel_lower, accel_table), accept = state
            crnt_token = instream.get_lookahead()
            ilabel = classify(crnt_token)
            if __DEBUG__:
                symbol_str = ""
                if symbol_tab:
                    symbol_str = " %r" % (symbol_tab[ilabel],)
                print("%r %r%s %r" % (crnt_token, ilabel, symbol_str,
                                      ilabel-accel_lower))
            if (accel_lower <= ilabel) and (ilabel < accel_upper):
                accel_result = accel_table[ilabel - accel_lower]
                if -1 != accel_result:
                    if (accel_result & (1<<7)):
                        # PUSH
                        nt = (accel_result >> 8) + token.NT_OFFSET
                        if __DEBUG__:
                            print("PUSH %d" % nt)
                        yield nt
                        state = states[accel_result & ((1<<7) - 1)]
                    else:
                        # SHIFT
                        if __DEBUG__:
                            print("SHIFT %r" % (crnt_token,))
                        outtree.pushpop(instream.get_token())
                        state = states[accel_result]
                        if state[2] and len(state[0]) == 1:
                            break
                    continue
            if accept:
                break
            else:
                # TODO: Make the error string more instructive, like
                # the older DFAParser stuff did.
                candidates = [symbol_tab[accel_lower + accel_index]
                              for accel_result, accel_index in
                              zip(accel_table, range(len(accel_table)))
                              if accel_result != -1]
                if __DEBUG__:
                    label_index = accel_lower
                    for accel_result in accel_table:
                        if accel_result != -1:
                            symbol_str = ""
                            if symbol_tab:
                                symbol_str = " %r" % (symbol_tab[label_index],)
                            print("%r%s => %d" % (label_index, symbol_str,
                                                  accel_result))
                        label_index += 1
                    print("len(%r) = %d" % (accel_table, len(accel_table)))
                line_no, column_no = crnt_token[2]
                token_str = crnt_token[1]
                fmt_tup = (line_no, column_no, token_str)
                raise SyntaxError("Line %d, column %d, unexpected '%s'." %
                                  fmt_tup)
        if __DEBUG__:
            print("POP %s" % dfa_name)
        outtree.pop()
        return
    return _parse_dfa

# ______________________________________________________________________
# End of trampoline.py

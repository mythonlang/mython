#! /usr/bin/env python
# ______________________________________________________________________
"""Module mylexer

Lexical scanner for the Mython language.

Jonathan Riehl
"""
# ______________________________________________________________________
# Module imports

from __future__ import print_function

import sys
import re
import tokenize
import string
import pprint

import pgen2.tokenizer

from mython.trampoline import TokenStream

# ______________________________________________________________________
# Module data

tok_name = tokenize.tok_name.copy()
BANG, MYEXPR, MYSUITE = (tokenize.N_TOKENS + count for count in range(3))
tok_name[BANG] = 'BANG'
tok_name[MYEXPR] = 'MYEXPR'
tok_name[MYSUITE] = 'MYSUITE'
N_TOKENS = tokenize.N_TOKENS + 3

CLOSERS = {
    '{' : '}',
    '(' : ')',
    '<' : '>',
    '[' : ']',
}

__DEBUG__ = False

# ______________________________________________________________________
# Class definitions.

class MythonReadliner (object):
    def __init__ (self, readline):
        self.readline = readline
        self.last_line_count = 0
        self.stored_line = None
        self.empty_line_pattern = re.compile("\\A\\s*\\Z")
        self.ws_pattern = re.compile("\\A(\\s)+")

    def __call__ (self):
        # TODO Note that the real readline function takes an optional
        # size argument.  This should ideally be modified to be 100%
        # readline compatible.
        ret_val = "\n"
        if self.last_line_count > 0:
            assert self.stored_line != None
            self.last_line_count -= 1
            if self.last_line_count == 0:
                ret_val = self.stored_line
                self.stored_line = None
        elif self.stored_line != None:
            # This handles EOF in the presence of an empty mysuite
            # block.
            ret_val = self.stored_line
        else:
            ret_val = self.readline()
        return ret_val

    def scan_mysuite_block (self):
        ret_val = []
        crnt_line = self.readline()
        while ((crnt_line != '') and
               (self.empty_line_pattern.match(crnt_line) != None)):
            ret_val.append(crnt_line)
            crnt_line = self.readline()
        if crnt_line != '':
            match_obj = self.ws_pattern.match(crnt_line)
            indent_whitespace = match_obj.groups(1)
            # XXX It seems easier to read this code if we check for a
            # proper indentation level here instead of in the caller.
            while crnt_line.startswith(indent_whitespace):
                ret_val.append(crnt_line)
                crnt_line = self.readline()
                while ((crnt_line != '') and
                       (self.empty_line_pattern.match(crnt_line) != None)):
                    ret_val.append(crnt_line)
                    crnt_line = self.readline()
        self.last_line_count = len(ret_val)
        self.stored_line = crnt_line
        return ret_val

# ______________________________________________________________________

class MythonTokenStream (TokenStream):
    def __init__ (self, readliner, **kws):
        """Constructor for the Mython token stream.

        The MythonTokenStream class incorporates a method that creates
        a token generator (similar to tokenize.tokenize()).  This
        generator uses a large set of state variables to manage the
        lexical state in the generator, and these are exposed as
        attributes of the lexical stream.  These include:

        - lnum: The current/initial line number.  Default is 0.

        - parenlev: The current parenthesis level (determines if NL
          or NEWLINE tokens are generated at the end of a line).
          Default is 0.

        - in_mysuite: Flag used to signal that we are now scanning a
          Mython quotation token.  Default is False.

        ...TODO...

        These state variables may be initialized using keywork arguments.

        This lexical stream also defines a function or method for
        creating tokens:

        - make_token() - By default, this is a method that returns a
          tuple of its arguments.  This behavior is compatible with the
          tokenize module's generator.
        """
        self.readliner = readliner
        self.lnum = kws.get("lnum", 0)
        self.column_offset = kws.get("column_offset", 0)
        self.parenlev = kws.get("parenlev", 0)
        self.continued = kws.get("continued", 0)
        self.contstr = kws.get("contstr", 0)
        self.needcont = kws.get("needcont", 0)
        self.contline = kws.get("contline", 0)
        self.indents = kws.get("indents", [0])
        self.tabsize = kws.get("tabsize", 8)
        self.make_token = kws.get("make_token", self.make_token)
        self.endprog = kws.get("endprog")
        self.in_mysuite = kws.get("in_mysuite", False)
        self.in_myexpr = kws.get("in_myexpr", False)
        self.strstart = kws.get("strstart", (-1, -1))
        self.empty_line_pattern = re.compile("\\A\\s*\\Z")
        self.ws_pattern = re.compile("\\A(\\s+)")
        TokenStream.__init__(self, self.generate_tokens())

    def make_token (self, tok_sym, tok_str, start_pos, end_pos, tok_ln):
        start_line, start_col = start_pos
        end_line, end_col = end_pos
        ret_val = (tok_sym, tok_str,
                   (start_line, start_col + self.column_offset),
                   (end_line, end_col + self.column_offset), tok_ln)
        return ret_val

    def start_mysuite (self):
        "Change the lexical state to reflect entry of a mysuite block."
        self.in_mysuite = True

    def start_myexpr (self, open_delim):
        "Change the lexical state to reflect entry of a myexpr."
        self.open_delim = open_delim[1]
        self.in_myexpr = True

    def readline (self):
        "Read a line from the readline callable, increment the line number."
        try:
            ret_val = self.readliner()
        except StopIteration:
            ret_val = ''
        self.lnum += 1
        return ret_val

    def generate_tokens (self):
        """Creates a generator object that yields Python/Mython tokens.

        Based on (largely retyped and slightly modified from) the
        tokenize module by Ka Ping Yee and others, licensed under the
        PSFL (see .../basil/thirdparty/PSF_LICENSE).
        """
        namechars = string.ascii_letters + '_'
        numchars = '0123456789'
        while 1:
            line = self.readline()
            pos, max_pos = 0, len(line)
            if self.parenlev == 0 and self.in_mysuite:
                # This should only be reached if no non-whitespace
                # characters were found following the trailing colon
                # of a mysuite statement, and we've already recognized
                # the end of line token for the multi-line quotation.
                # This must go here so the readliner is properly
                # hijacked.
                mysuite_lnum = self.lnum
                mysuite_lns = []
                while ((line != '') and
                       (self.empty_line_pattern.match(line) != None)):
                    mysuite_lns.append(line)
                    line = self.readline()
                    pos, max_pos = 0, len(line)
                indent_ws = ''
                indent_lnum = -1
                if line != '':
                    indent_lnum = self.lnum
                    match_obj = self.ws_pattern.match(line)
                    indent_ws = match_obj.groups(1)[0]
                    while line.startswith(indent_ws):
                        mysuite_lns.append(line)
                        line = self.readline()
                        pos, max_pos = 0, len(line)
                        while ((line != '') and
                               (self.empty_line_pattern.match(line) != None)):
                            mysuite_lns.append(line)
                            line = self.readline()
                            pos, max_pos = 0, len(line)
                else:
                    # TODO: Shouldn't this be MyFrontIndentError?
                    raise SyntaxError("Empty mysuite block, starting on "
                                      "line %d, runs to end of file." %
                                      mysuite_lnum)
                indent_ws_len = len(indent_ws)
                if indent_ws_len <= self.indents[-1]:
                    # TODO: Shouldn't this be MyFrontIndentError?
                    raise SyntaxError("Improper indentation level at "
                                      "line %d; expected %d, got %d." %
                                      (indent_lnum, self.indents[-1],
                                       indent_ws_len))
                normalized_lns = [mysuite_ln[indent_ws_len:]
                                  if len(mysuite_ln) > indent_ws_len
                                  else (mysuite_ln[-2:]
                                        if mysuite_ln.endswith('\r\n')
                                        else mysuite_ln[-1:])
                                  for mysuite_ln in mysuite_lns]
                token = "".join(normalized_lns)
                lines = "".join(mysuite_lns)
                spos = (mysuite_lnum, indent_ws_len)
                epos = (spos[0] + len(mysuite_lns), 0)
                yield self.make_token(MYSUITE, token, spos,
                                      epos, lines)
                self.in_mysuite = False
            if self.contstr:
                if not line:
                    raise tokenize.TokenError("EOF in multi-line string",
                                              self.strstart)
                endmatch = self.endprog.match(line)
                if endmatch:
                    pos = end = endmatch.end(0)
                    yield self.make_token(
                        tokenize.STRING, self.contstr + line[:end],
                        self.strstart, (self.lnum, end), self.contline + line)
                    self.contstr = ''
                    self.needcont = 0
                    self.contline = None
                elif (self.needcont and (line[-2:] != '\\\n') and
                      (line[-3:] != '\\\r\n')):
                    yield self.make_token(
                        tokenize.ERRORTOKEN, self.contstr + line,
                        self.strstart, (self.lnum, len(line)), contline)
                    self.contstr = ''
                    self.contline = None
                    continue
                else:
                    self.contstr += line
                    self.contline += line
                    continue
            elif self.parenlev == 0 and not self.continued:
                if not line: break
                column = 0
                while pos < max_pos:
                    if line[pos] == ' ':
                        column += 1
                    elif line[pos] == '\t':
                        column = (column/self.tabsize + 1) * self.tabsize
                    elif line[pos] == '\f':
                        column = 0
                    else:
                        break
                    pos += 1
                if pos == max_pos:
                    break
                if line[pos] in '#\r\n':
                    if line[pos] == "#":
                        if sys.version_info < (2, 6):
                            yield self.make_token(
                                tokenize.COMMENT, line[pos:],
                                (self.lnum, pos), (self.lnum, len(line)),
                                line)
                        else:
                            comment_token = line[pos:].rstrip('\r\n')
                            nl_pos = pos + len(comment_token)
                            yield self.make_token(
                                tokenize.COMMENT, comment_token,
                                (self.lnum, pos),
                                (self.lnum, pos + len(comment_token)),
                                line)
                            yield self.make_token(
                                tokenize.NL, line[nl_pos:],
                                (self.lnum, nl_pos), (self.lnum, len(line)),
                                line)
                    else:
                        yield self.make_token(
                            tokenize.NL, line[pos:], (self.lnum, pos),
                            (self.lnum, len(line)), line)
                    continue
                if column > self.indents[-1]:
                    self.indents.append(column)
                    yield self.make_token(
                        tokenize.INDENT, line[:pos], (self.lnum, 0),
                        (self.lnum, pos), line)
                while column < self.indents[-1]:
                    if column not in self.indents:
                        raise IndentationError(
                            "unindent does not match any outer indentation "
                            "level", ("<tokenize>", self.lnum, pos, line))
                    self.indents.pop()
                    yield self.make_token(
                        tokenize.DEDENT, '', (self.lnum, pos),
                        (self.lnum, pos), line)
            else:
                if not line:
                    if __debug__:
                        pprint.pprint(self.__dict__)
                    raise tokenize.TokenError("EOF in multi-line statement",
                                              (self.lnum, 0))
                self.continued = 0
            while pos < max_pos:
                pseudomatch = tokenize.pseudoprog.match(line, pos)
                if pseudomatch:
                    start, end = pseudomatch.span(1)
                    spos, epos, pos = (self.lnum, start), (self.lnum, end), end
                    token, initial = line[start:end], line[start]
                    if ((initial in numchars) or
                        (initial == '.' and token != '.')):
                        yield self.make_token(tokenize.NUMBER, token, spos,
                                              epos, line)
                    elif initial in '\r\n':
                        yield self.make_token(
                            tokenize.NL if self.parenlev > 0 else
                            tokenize.NEWLINE, token, spos, epos, line)
                    elif initial == '#':
                        yield self.make_token(tokenize.COMMENT, token, spos,
                                              epos, line)
                    elif token in tokenize.triple_quoted:
                        self.endprog = tokenize.endprogs[token]
                        endmatch = self.endprog.match(line, pos)
                        if endmatch:
                            pos = endmatch.end(0)
                            token = line[start:pos]
                            yield self.make_token(tokenize.STRING, token, spos,
                                                  (self.lnum, pos), line)
                        else:
                            self.strstart = (self.lnum, start)
                            self.contstr = line[start:]
                            self.contline = line
                            break
                    elif ((initial in tokenize.single_quoted) or
                          (token[:2] in tokenize.single_quoted) or
                          (token[:3] in tokenize.single_quoted)):
                        if token[-1] == '\n':
                            self.strstart = (self.lnum, start)
                            self.endprog = (tokenize.endprogs[initial] or
                                            tokenize.endprogs[token[1]] or
                                            tokenize.endprogs[token[2]])
                            self.contstr = line[start:]
                            self.needcont = 1
                            self.contline = line
                            break
                        else:
                            yield self.make_token(tokenize.STRING, token, spos,
                                                  epos, line)
                    elif ((hasattr(initial, 'isidentifier') and
                             initial.isidentifier()) or
                            (initial in namechars)):
                        yield self.make_token(tokenize.NAME, token, spos, epos,
                                              line)
                    elif initial == '\\':
                        self.continued = 1
                    else:
                        if initial in '([{':
                            self.parenlev += 1
                        elif initial in '}])':
                            self.parenlev -= 1
                        yield self.make_token(tokenize.OP, token, spos, epos,
                                              line)
                        if (token == ':' and self.in_mysuite and
                            self.parenlev == 0):
                            cand_token = line[pos:].strip()
                            if cand_token:
                                token_with_ws_len = len(
                                    line[pos:].rstrip('\r\n'))
                                while line[pos].isspace():
                                    pos += 1
                                yield self.make_token(
                                    MYSUITE, cand_token, (self.lnum, pos),
                                    (self.lnum, epos[1] + token_with_ws_len),
                                    line)
                                pos += len(cand_token)
                                self.in_mysuite = False
                        elif self.in_myexpr:
                            open_delim = self.open_delim
                            close_delim = CLOSERS[open_delim]
                            myexpr_depth = 1
                            spos = epos
                            myexpr_lns = [line]
                            while 1:
                                while pos < max_pos:
                                    if line[pos] == open_delim:
                                        myexpr_depth += 1
                                    elif line[pos] == close_delim:
                                        myexpr_depth -= 1
                                    pos += 1
                                    if myexpr_depth <= 0:
                                        if close_delim in '}])':
                                            self.parenlev -= 1
                                        break
                                if myexpr_depth > 0:
                                    line = self.readline()
                                    myexpr_lns.append(line)
                                    pos, max_pos = 0, len(line)
                                else:
                                    assert myexpr_depth == 0
                                    break
                            epos = self.lnum, pos
                            if len(myexpr_lns) == 1:
                                token = line[spos[1]:pos]
                            else:
                                token = "".join((myexpr_lns[0][spos[1]:],
                                                 "".join(myexpr_lns[1:-2]),
                                                 myexpr_lns[-1][:pos]))
                            lines = "".join(myexpr_lns)
                            yield self.make_token(MYEXPR, token, spos, epos,
                                                  lines)
                            self.in_myexpr = False
                            del self.open_delim
                elif pos < max_pos and line[pos] == '!': # Favor != over !...
                    yield self.make_token(BANG, line[pos], (self.lnum, pos),
                                          (self.lnum, pos + 1), line)
                    pos += 1
                else:
                    yield self.make_token(
                        tokenize.ERRORTOKEN,
                        line[pos] if pos < max_pos else '', (self.lnum, pos),
                        (self.lnum, pos + 1), line)
                    pos += 1
        for indent in self.indents[1:]:
            yield self.make_token(tokenize.DEDENT, '', (self.lnum, 0),
                                  (self.lnum, 0), '')
        yield self.make_token(tokenize.ENDMARKER, '', (self.lnum, 0),
                              (self.lnum, 0), '')

    def tokenize (self):
        """Return the next token in the lexical stream."""
        ret_val = next(self.tokenizer)
        while ret_val[0] in (tokenize.NL, tokenize.COMMENT):
            ret_val = next(self.tokenizer)
        if ((ret_val[0] == tokenize.OP) and
            (ret_val[1] in pgen2.tokenizer.Tokenizer.operatorMap)):
            # This is a workaround for using the Python tokenize module.
            _, tok_str, tok_start, tok_end, tok_ln = ret_val
            tok_type = pgen2.tokenizer.Tokenizer.operatorMap[tok_str]
            ret_val = (tok_type, tok_str, tok_start, tok_end, tok_ln)
        return ret_val

# ______________________________________________________________________
# Utility function(s).

def scan_mython_file (file_obj):
    """Simple Mython scanner, returns a list of tokens, given a file object."""
    ret_val = []
    readliner = MythonReadliner(file_obj.readline)
    token_stream = MythonTokenStream(readliner)
    crnt_token = token_stream.get_token()
    ret_val.append(crnt_token)
    try:
        while crnt_token[0] != tokenize.ENDMARKER:
            if crnt_token[:2] == (tokenize.NAME, 'my'):
                token_stream.start_mysuite()
            crnt_token = token_stream.get_token()
            ret_val.append(crnt_token)
    finally:
        if __debug__:
            pprint.pprint(ret_val)
    return ret_val

# ______________________________________________________________________

def scan_python_file (readline, generator_fn = None):
    if generator_fn is None:
        # NOTE: The following is technically not legal, a "readliner"
        # passed to a MythonTokenStream should have a
        # "scan_mysuite_block()" method.  However, for scanning known
        # valid Python files, this should work fine.
        token_stream = MythonTokenStream(readline)
        tokens = token_stream.generate_tokens()
    else:
        tokens = generator_fn(readline)
    return [token for token in tokens]

# ______________________________________________________________________

def mytokenize (readline, tokeneater=getattr(tokenize, 'printtoken', None)):
    """Backward compatible function for comparison with tokenize.tokenize()

    To do a comparison on a given file between the Python and Mython
    tokenizer:

    >>> import tokenize; tokenize.tokenize(open('filename').next)

    And compare the output to:

    >>> from basil.lang.mython import mylexer; mylexer.mytokenize(\
    ... open('filename').next)
    """
    if tokeneater is None:
        def tokeneater(*tok): pprint.pprint(tok)
    for token in scan_python_file(readline):
        tokeneater(*token)

# ______________________________________________________________________

if __name__ == "__main__":
    for filename in sys.argv[1:]:
        with open(filename) as fileobj:
            pprint.pprint(scan_mython_file(fileobj))
    else:
        if __DEBUG__:
            print({'BANG' : BANG, 'myexpr' : MYEXPR, 'mysuite' : MYSUITE})

# ______________________________________________________________________
# End of mylexer.py

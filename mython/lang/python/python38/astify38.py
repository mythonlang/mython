import token
from ..python37.astify37 import My37Handler, ast


class My38Handler (My37Handler):
    def _handle_assign(self, targets, value, location):
        # FIXME: Figure out type comments.
        return ast.Assign(targets, value, None, lineno=location[0],
                          col_offset=location[1])

    def _handle_atom_token(self, token_text, token_location, children):
        token_kind = children[0][0][0]
        if token_kind in (token.STRING, token.NUMBER):
            value = ast.literal_eval(token_text)
            for child in children[1:]:
                # Invariant: this loop should never be enterred by a number
                # token.
                value += ast.literal_eval(child[0][1])
            ret_val = ast.Constant(value, None,
                                   lineno=token_location[0],
                                   col_offset=token_location[1])
        elif token_kind == token.ELLIPSIS:
            ret_val = ast.Ellipsis(lineno=token_location[0],
                                    col_offset=token_location[1])
        else:
            assert token_kind == token.NAME
            ret_val = self._handle_name(token_text, token_location)
        return ret_val

    def _get_empty_arguments(self):
        return ast.arguments([], [], None, [], [], None, [])

    #def handle_atom(self, node):
    #    ret_val = super().handle_atom(node)
    #    if isinstance(ret_val, (ast.Tuple, ast.List)):
    #        ret_val.lineno, ret_val.col_offset = node[1][0][0][2]
    #    return ret_val

    def handle_for_stmt(self, node):
        ret_val = super().handle_for_stmt(node)
        ret_val.type_comment = None
        return ret_val

    def handle_funcdef(self, node):
        # ('name', 'args', 'body', 'decorator_list', 'returns', 'type_comment')
        children = node[1]
        index = 1
        decorators = []
        assert self.is_token(children[0])
        location = children[0][0][2]
        name = children[index][0][1]
        index += 1
        params = self.handle_node(children[index])
        index += 1
        returns = None
        if self.is_token(children[index]) and children[index][0][1] == '->':
            returns = self.handle_node(children[index + 1])
            index += 2
        index += 1
        type_comment = None
        if self.is_token(children[index]):
            type_comment = self.handle_node(children[index])
            index += 1
        body = self.handle_node(children[index])
        assert index == len(children) - 1
        return ast.FunctionDef(name, params, body, decorators, returns,
                               type_comment, lineno=location[0],
                               col_offset=location[1])

    def _handle_name(self, token_text, token_location):
        if token_text in ('None', 'True', 'False'):
            return ast.Constant(eval(token_text), None,
                                lineno=token_location[0],
                                col_offset=token_location[1])
        return super()._handle_name(token_text, token_location)

    def handle_tfpdef (self, node):
        children = node[1]
        arg = children[0][0][1]
        location = children[0][0][2]
        annotation = (None if len(children) < 2
                      else self.handle_node(children[-1]))
        return ast.arg(arg, annotation, None,
                       lineno=location[0], col_offset=location[1])

    def handle_typedargslist(self, node):
        children = node[1]
        # Scan ahead real quick...
        posonlyargs_index = -1
        for index, child in enumerate(children):
            if self.is_token(child) and child[0][1] == '/':
                posonlyargs_index = index
                break
        index = 0
        # Collect positional arguments
        posonlyargs = []
        defaults = []
        while index < posonlyargs_index:
            import pudb; pudb.set_trace()
        # Get the rest...
        remaining_args = list(self._handle_typedargslist(
            ('bogus', children[index:])))
        if defaults:
            remaining_args[-1] = defaults + remaining_args[-1]
        # Reminder:
        # arguments = (arg* posonlyargs, arg* args, arg? vararg, arg* kwonlyargs,
        #              expr* kw_defaults, arg? kwarg, expr* defaults)
        return ast.arguments(posonlyargs, *remaining_args)

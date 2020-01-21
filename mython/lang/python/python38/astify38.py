from ..astify import MyHandler, ast


class My38Handler (MyHandler):
    def handle_funcdef(self, node):
        # ('name', 'args', 'body', 'decorator_list', 'returns', 'type_comment')
        children = node[1]
        location = self._get_location(children[0])
        index = 1
        decorators = []
        if not self.is_token(children[0]):
            index = 2
            decorators = self.handle_node(children[0])
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
        return ast.FunctionDef(name, params, body, decorators, returns, type_comment)

    def handle_parameters(self, node):
        children = node[1]
        if len(children) > 2:
            return self.handle_typedargslist(children[1])
        return ast.arguments([], [], None, [], [], None, [])

    def handle_typedargslist(self, node):
        children = node[1]
        index = 0
        # Collect positional arguments
        posonlyargs = []
        defaults = []
        # Collect positional/keyword args
        args = []
        # Collect vararg
        vararg = None
        # Collect kwonlyargs
        kwonlyargs = []
        kw_defaults = []
        # Collect kwarg
        kwarg = None
        # Reminder:
        # arguments = (arg* posonlyargs, arg* args, arg? vararg, arg* kwonlyargs,
        #              expr* kw_defaults, arg? kwarg, expr* defaults)
        return ast.arguments(posonlyargs, args, vararg, kwonlyargs, kw_defaults,
                             kwarg, defaults)

from ..astify import MyHandler, ast


class My36Handler(MyHandler):
    def _get_empty_arguments(self):
        return ast.arguments([], None, [], [], None, [])

    def handle_parameters(self, node):
        children = node[1]
        if len(children) > 2:
            return self.handle_typedargslist(children[1])
        return self._get_empty_arguments()

    def handle_typedargslist(self, node):
        ret_val = self._get_empty_arguments()
        children = node[1]
        index = 0
        # Collect positional/keyword args
        # TODO
        # Collect vararg
        # TODO
        # Collect kwonlyargs
        # TODO
        # Collect kwarg
        # TODO
        return ret_val

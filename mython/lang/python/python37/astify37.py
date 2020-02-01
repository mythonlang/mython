from ..python36.astify36 import My36Handler, ast


class My37Handler (My36Handler):
    def handle_async_stmt(self, node):
        children = node[1]
        assert children[0][0][1] == 'async'
        location = children[0][0][2]
        child = self.handle_node(children[1])
        args = (getattr(child, field) for field in child._fields)
        if isinstance(child, ast.FunctionDef):
            ret_val = ast.AsyncFunctionDef(*args, lineno=location[0],
                                           col_offset=location[1])
        elif isinstance(child, ast.With):
            ret_val = ast.AsyncWith(*args, lineno=location[0],
                                    col_offset=location[1])
        else:
            assert isinstance(child, ast.For)
            ret_val = ast.AsyncFor(*args, lineno=location[0],
                                   col_offset=location[1])
        return ret_val

    def handle_comp_for(self, node):
        children = node[1]
        ret_val = self.handle_node(children[-1])
        ret_val[1][0].is_async = len(children) > 1
        return ret_val

    handle_sync_comp_for = My36Handler._handle_comp_for

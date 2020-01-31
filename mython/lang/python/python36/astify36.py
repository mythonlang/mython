import token
from ..astify import MyHandler, ast


class My36Handler(MyHandler):
    def _get_empty_arguments(self):
        return ast.arguments([], None, [], [], None, [])

    def _handle_name(self, token_text, token_location):
        if token_text in ('None', 'True', 'False'):
            return ast.NameConstant(eval(token_text),
                                    lineno=token_location[0],
                                    col_offset=token_location[1])
        return super()._handle_name(token_text, token_location)

    def handle_classdef(self, node):
        children = node[1]
        location = children[0][0][2]
        class_name = children[1][0][1]
        bases = []
        keywords = []
        decorators = []
        if self.is_token(children[2]) and children[2][0][1] == "(":
            if not self.is_token(children[3]):
                assert children[3][0] == 'arglist'
                bases, keywords, _, _ = self.handle_arglist(children[3])
        return ast.ClassDef(class_name, bases, keywords,
                            self.handle_node(children[-1]),
                            decorators, # FIXME: Handle class decorators.
                            lineno=location[0], col_offset=location[1])

    def handle_dictorsetmaker(self, node):
        children = node[1]
        child_count = len(children)
        if (children[0][0][1] == '**' or
            (child_count > 2 and children[1][0][1] == ':')):
            if self.is_token(children[0]):
                key = None
                value = self.handle_node(children[1])
                index = 2
            else:
                key = self.handle_node(children[0])
                value = self.handle_node(children[2])
                index = 3
            if (index < child_count) and not self.is_token(children[index]):
                _, generators = self.handle_comp_for(children[index])
                ret_val = ast.DictComp(key, value, generators)
            else:
                keys = [key]
                values = [value]
                assert children[index][0][1] == ','
                index += 1
                while index < child_count:
                    keys.append(self.handle_node(children[index]))
                    keys.append(self.handle_node(children[index + 2]))
                    index += 4
                ret_val = ast.Dict(keys, values)
        else:
            elt = self.handle_node(children[0])
            if child_count > 1 and not self.is_token(children[1]):
                _, generators = self.handle_comp_for(children[1])
                ret_val = ast.SetComp(elt, generators)
            else:
                elts = [elt]
                for index in range(1, child_count, 3):
                    elts.append(self.handle_node(children[index + 1]))
                ret_val = ast.Set(elts)
        return ret_val

    def handle_parameters(self, node):
        children = node[1]
        if len(children) > 2:
            return self.handle_typedargslist(children[1])
        return self._get_empty_arguments()

    def handle_raise_stmt (self, node):
        children = node[1]
        child_count = len(children)
        location = children[0][0][2]
        exn_type = None
        exn_inst = None
        if child_count > 1:
            exn_type = self.handle_node(children[1])
            if child_count > 3:
                exn_inst = self.handle_node(children[3])
        return ast.Raise(exn_type, exn_inst,
                         lineno=location[0], col_offset=location[1])

    def handle_try_stmt(self, node):
        children = node[1]
        location = children[0][0][2]
        body = self.handle_node(children[2])
        handlers = []
        orelse = []
        finalbody = []
        if self.is_token(children[3]):
            assert children[3][0][1] == 'finally'
            finalbody = self.handle_node(children[-1])
        else:
            child_count = len(children)
            child_index = 3
            while ((child_index < child_count) and
                   (not self.is_token(children[child_index]))):
                except_location = self._get_location(children[child_index])
                except_results = self.handle_node(children[child_index])
                except_type = None
                except_name = None
                if len(except_results) > 0:
                    except_type = except_results[0]
                    if len(except_results) > 1:
                        except_name = except_results[1]
                except_body = self.handle_node(children[child_index + 2])
                handlers.append(
                    ast.ExceptHandler(except_type, except_name,
                                      except_body, lineno=except_location[0],
                                      col_offset=except_location[1]))
                child_index += 3
            if child_index < child_count:
                if children[child_index][0][1] == 'else':
                    orelse = self.handle_node(children[child_index + 2])
                    child_index += 3
                if child_index < child_count:
                    assert children[child_index][0][1] == 'finally'
                    finalbody = self.handle_node(children[child_index + 2])
                    child_index += 3
            assert child_index == child_count
        return ast.Try(body, handlers, orelse, finalbody, lineno=location[0],
                       col_offset=location[1])

    def handle_typedargslist(self, node):
        children = node[1]
        child_count = len(children)
        index = 0
        args = []
        defaults = []
        # Collect positional/keyword args
        while ((index < child_count) and
               (children[index][0][0] not in {token.STAR, token.DOUBLESTAR})):
            args.append(self.handle_node(children[index]))
            index += 1
            if index < child_count:
                if children[index][0][0] == token.EQUAL:
                    index += 1
                    defaults.append(self.handle_node(children[index]))
                    index += 1
                if (index < child_count and
                    children[index][0][0] == token.COMMA):
                    index += 1
        # Collect vararg
        vararg = None
        if index < child_count and children[index][0][0] == token.STAR:
            index += 1
            if index < child_count and children[index][0] == 'tfpdef':
                vararg = self.handle_tfpdef(children[index])
                index += 1
                if (index < child_count and
                    children[index][0][0] == token.COMMA):
                    index += 1
        # Collect kwonlyargs
        kwonlyargs = []
        kw_defaults = []
        while ((index < child_count) and
               (children[index][0][0] != token.DOUBLESTAR)):
            kwonlyargs.append(self.handle_node(children[index]))
            index += 1
            if index < child_count:
                if children[index][0][0] == token.EQUAL:
                    index += 1
                    kw_defaults.append(self.handle_node(children[index]))
                    index += 1
                else:
                    kw_defaults.append(None)
                if (index < child_count and
                    children[index][0][0] == token.COMMA):
                    index += 1
        # Collect kwarg
        kwarg = None
        if (index < child_count):
            assert children[index][0][0] == token.DOUBLESTAR
            index += 1
            if index < child_count and children[index][0] == 'tfpdef':
                kwarg = self.handle_tfpdef(children[index])
                index += 1
        return ast.arguments(args, vararg, kwonlyargs, kw_defaults, kwarg,
                             defaults)

    def handle_with_item(self, node):
        context_expr, optional_vars = super().handle_with_item(node)
        return ast.withitem(context_expr, optional_vars)

    def handle_with_stmt(self, node):
        children = node[1]
        location = children[0][0][2]
        items = [self.handle_with_item(child) for child in children[1:-1:2]]
        return ast.With(items, self.handle_suite(children[-1]),
                        lineno=location[0], col_offset=location[1])

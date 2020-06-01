import ast
import astor
from typing import TypeVar, Union
from copy import deepcopy
from .TypeWrapper import TypeWrapper

class CodeGenerator(ast.NodeTransformer):
    def __init__(self):
        self.level = 0
        self.symbol_table = None
        self.cur_class = None

    def gen(self, tree, symbol_table):
        self.symbol_table = symbol_table
        self.insert_typing_node(tree)
        return self.visit(tree)

    def insert_typing_node(self, tree):
        importNode = ast.Import(
            names=[ast.alias(
                asname=None,
                name="typing"
            )],
            lineno = 0,
        )
        tree.body.insert(0, importNode)

    def visit_Assign(self, node):
        body = []
        for t in node.targets:
            try:
                anno = self.get_type_name(self.get_real_type(self.get_target_type(t)))
                body.append(
                    ast.AnnAssign(
                        target=t,
                        value=node.value,
                        annotation=anno,
                        lineno=node.lineno,
                        simple=1,
                    )
                )
            except:
                body.append(
                    ast.Assign(
                        targets=[t],
                        value=node.value,
                        lineno=node.lineno,
                    )
                )
        return body

    def visit_FunctionDef(self, node):
        t = self.get_real_type(self.search(node.name))
        if t is None:
            return node

        args_type = list(t.__args__[:-1])
        body_type = t.__args__[-1]
        args_enum = enumerate(args_type, 1) if self.cur_class else enumerate(args_type)

        for i, arg in args_enum:
            node.args.args[i].annotation = self.get_type_name(arg)
        node.returns = self.get_type_name(body_type)

        if (isinstance(node, ast.FunctionDef)):
            self.symbol_table = self.symbol_table.childs[node.name]

        ast.NodeTransformer.generic_visit(self, node)

        if (isinstance(node, ast.FunctionDef)):
            self.symbol_table = self.symbol_table.parent

        return node

    def visit_ClassDef(self, node):
        if (isinstance(node, ast.ClassDef)):
            self.symbol_table = self.symbol_table.childs[node.name]

        cur_class_bak = self.cur_class
        self.cur_class = node.name

        ast.NodeTransformer.generic_visit(self, node)

        self.cur_class = cur_class_bak

        if (isinstance(node, ast.ClassDef)):
            self.symbol_table = self.symbol_table.parent

        return node

    def get_target_type(self, t):
        if isinstance(t, ast.Attribute):
            return self.get_target_type(t.value).typeof(t.attr)

        elif isinstance(t, ast.Name):
            return self.search(t.id)

    def search(self, name):
        return self.symbol_table.typeof(name)

    def get_real_type(self, wrapped_type):
        return TypeWrapper.reveal_type_var(wrapped_type.reveal())

    def get_type_name(self, t):
        # built-in type
        if hasattr(t, "__name__"):
            return ast.Name(t.__name__)
        # typing type
        elif hasattr(t, "_name"):
            return ast.Name(str(t))
        elif t is type(None):
            return ast.Name('NoneType')
        # class
        elif isinstance(t, object):
            return ast.Name(t.__name__)
        else:
            return ast.Name('typing.Any')

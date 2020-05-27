# import ast
# import astor
# from typing import TypeVar, Union
# from copy import deepcopy
# from .SymTableEntry import Class

# class CodeGenerator(ast.NodeTransformer):
#     def __init__(self):
#         self.level = 0
#         self.symbol_table = None

#     def visit_Assign(self, node):
#         return [
#             ast.AnnAssign(
#                 target=t,
#                 value=node.value,
#                 annotation=self._get_type_name(self.search(t.id)),
#                 lineno=node.lineno,
#                 simple=1,
#             )
#             for t in node.targets
#         ]

#     def visit_FunctionDef(self, node):
#         t = self.search(node.name)
#         args_type = list(t.__args__[:-1])
#         body_type = t.__args__[-1]

#         for i, arg in enumerate(args_type):
#             node.args.args[i].annotation = self._get_type_name(arg)
#         node.returns = self._get_type_name(body_type)

#         if (isinstance(node, ast.FunctionDef)):
#             self.symbol_table = self.symbol_table.childs[node.name]

#         ast.NodeTransformer.generic_visit(self, node)

#         if (isinstance(node, ast.FunctionDef)):
#             self.symbol_table = self.symbol_table.parent

#         return node

#     def gen(self, tree, symbol_table):
#         self.symbol_table = symbol_table
#         return self.visit(tree)

#     def search(self, name):
#         return self.symbol_table.get(name).reveal()

#     def _get_type_name(self, t):
#         # class
#         if isinstance(t, str):
#             return ast.Name(t)
#         try:
#             if isinstance(t(), Class):
#                 return ast.Name(t.name)
#         except:
#             pass
#         # TypeVar
#         if isinstance(t, TypeVar):
#             return self._get_type_name(t.__bound__)
#         # built-in type
#         elif hasattr(t, "__name__"):
#             return ast.Name(t.__name__)
#         # typing type
#         elif hasattr(t, "_name"):
#             return ast.Name(str(t))
#         else:
#             return ast.Name('Any')

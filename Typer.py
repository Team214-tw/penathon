import ast
from typing import *
import sys
from collections import defaultdict
import builtins
import os

TYPE_DICT = {
    "Any": Any,
    "Callable": Callable,
    "ClassVar": ClassVar,
    "Final": Final,
    "ForwardRef": ForwardRef,
    "Generic": Generic,
    "Literal": Literal,
    "Optional": Optional,
    "Protocol": Protocol,
    "Tuple": Tuple,
    "Type": Type,
    "TypeVar": TypeVar,
    "Union": Union,
    "AbstractSet": AbstractSet,
    "ByteString": ByteString,
    "Container": Container,
    "ContextManager": ContextManager,
    "Hashable": Hashable,
    "ItemsView": ItemsView,
    "Iterable": Iterable,
    "Iterator": Iterator,
    "KeysView": KeysView,
    "Mapping": Mapping,
    "MappingView": MappingView,
    "MutableMapping": MutableMapping,
    "MutableSequence": MutableSequence,
    "MutableSet": MutableSet,
    "Sequence": Sequence,
    "Sized": Sized,
    "ValuesView": ValuesView,
    "Awaitable": Awaitable,
    "AsyncIterator": AsyncIterator,
    "AsyncIterable": AsyncIterable,
    "Coroutine": Coroutine,
    "Collection": Collection,
    "AsyncGenerator": AsyncGenerator,
    "AsyncContextManager": AsyncContextManager,
    "Reversible": Reversible,
    "SupportsAbs": SupportsAbs,
    "SupportsBytes": SupportsBytes,
    "SupportsComplex": SupportsComplex,
    "SupportsFloat": SupportsFloat,
    "SupportsIndex": SupportsIndex,
    "SupportsInt": SupportsInt,
    "SupportsRound": SupportsRound,
    "ChainMap": ChainMap,
    "Counter": Counter,
    "Deque": Deque,
    "Dict": Dict,
    "DefaultDict": DefaultDict,
    "List": List,
    "OrderedDict": OrderedDict,
    "Set": Set,
    "FrozenSet": FrozenSet,
    "NamedTuple": NamedTuple,
    "TypedDict": TypedDict,
    "Generator": Generator,
    "AnyStr": AnyStr,
    "NewType": NewType,
    "NoReturn": NoReturn,
    "Text": Text,
    "int": int,
    "str": str,
    "float": float,
    "None": None,
    "bytes": bytes,
    "object": object,
    "bool": bool,
    "type": type,
    "BaseException": BaseException,
    "slice": slice,
    "bytearray": bytearray,
    "property": property,
    "memoryview": memoryview,
    "complex": complex,
    "range": range,
}

TYPING_WITH_TWO_ARGS = [Dict, Callable, DefaultDict]

symbol_table = {}


class AnnoVisitor(ast.NodeVisitor):
    def generic_visit(self, node):
        ast.NodeVisitor.generic_visit(self, node)
        # print(node, "Not Implement AnnoVisitor")

    def visit_Subscript(self, node: ast.Subscript):
        name = self.visit(node.value)
        if name == Any:
            return Any
        typ = self.visit(node.slice)
        return name[typ]

    def visit_Index(self, node: ast.Index):
        return self.visit(node.value)

    def visit_Expr(self, node: ast.Expr):
        return self.visit(node.value)

    def visit_Tuple(self, node: ast.Tuple):
        result = []
        for n in node.elts:
            result.append(self.visit(n))
        return tuple(result)

    def visit_List(self, node: ast.Tuple):
        result = []
        for n in node.elts:
            result.append(self.visit(n))
        return result

    def visit_Name(self, node: ast.Name):
        try:
            return TYPE_DICT[node.id]
        except KeyError:
            try:
                return symbol_table[node.id]
            except KeyError:
                # print(f"Warning: No {node.id}", file=sys.stderr)
                return Any

    def visit_Constant(self, node: ast.Constant):
        return node.value


class Visitor(ast.NodeVisitor):
    def __init__(self):
        self.cur_class_name = None
        self.storage = defaultdict(dict)

    def generic_visit(self, node):
        ast.NodeVisitor.generic_visit(self, node)
        # print(node, "Not Implement Visitor")

    def visit_Expr(self, node: ast.Expr):
        print(node.lineno)

    def visit_Module(self, node: ast.Module):
        for n in node.body:
            self.visit(n)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.cur_class_name = node.name
        for n in node.body:
            self.visit(n)
        self.cur_class_name = None

    def visit_AnnAssign(self, node: ast.AnnAssign):
        name = self.visit(node.target)
        typ = AnnoVisitor().visit(node.annotation)
        if self.cur_class_name is None:
            self.storage[name] = typ
        else:
            self.storage[self.cur_class_name][name] = typ
        return (name, typ)

    def visit_Name(self, node: ast.Name):
        return node.id

    def visit_arguments(self, node: ast.arguments):
        result = []
        for n in node.args:
            if n.arg == "self" or n.arg == "cls" or n.arg == "metacls":
                continue
            result.append(self.visit(n))
        return result

    def visit_arg(self, node: ast.arg):
        return AnnoVisitor().visit(node.annotation)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        args = self.visit(node.args)
        ret = AnnoVisitor().visit(node.returns)
        if self.cur_class_name is None:
            self.storage[node.name] = Callable[args, ret]
        else:
            self.storage[self.cur_class_name][node.name] = Callable[args, ret]
        return (node.name, Callable[args, ret])

    def visit_Assign(self, node: ast.Assign):
        name = self.visit(node.targets[0])
        value = self.visit(node.value)
        symbol_table[name] = value

    def visit_Constant(self, node: ast.Constant):
        return node.value

    def visit_Call(self, node: ast.Call):
        args = []
        for a in node.args:
            args.append(self.visit(a))
        kwargs = {}
        for k in node.keywords:
            key, val = self.visit(k)
            kwargs[key] = val
        if self.visit(node.func) != "TypeVar":
            raise Exception(f"Weird Function {self.visit(node.func)}")
        return TypeVar(*args, **kwargs)

    def visit_keyword(self, node: ast.keyword):
        name = node.arg
        value = self.visit(node.value)
        return (name, value)

    def visit_If(self, node: ast.If):
        if isinstance(node.test, ast.Compare) and isinstance(
            node.test.left, ast.Attribute
        ):
            if node.test.left.attr == "version_info":
                target = ast.literal_eval(node.test.comparators[0])
                current = sys.version_info
            elif node.test.left.attr == "platform":
                target = ast.literal_eval(node.test.comparators[0])
                current = sys.platform
            else:
                raise Exception("Unhandled If")
        if (
            isinstance(node.test.ops[0], ast.GtE)
            and current >= target
            or isinstance(node.test.ops[0], ast.Gt)
            and current > target
            or isinstance(node.test.ops[0], ast.LtE)
            and current <= target
            or isinstance(node.test.ops[0], ast.Lt)
            and current < target
            or isinstance(node.test.ops[0], ast.Eq)
            and current == target
            or isinstance(node.test.ops[0], ast.NotEq)
            and current != target
        ):
            return list(map(self.visit, node.body))
        else:
            return list(map(self.visit, node.orelse))

    def visit_Expr(self, node):
        pass


class Typer:
    storage = {}

    @staticmethod
    def _recursive_find_file(cur_path, splitted_name):
        if len(splitted_name) == 0:
            return "", -1, False
        new_path = os.path.join(cur_path, splitted_name[0])
        file_name, remain_len, found = Typer._recursive_find_file(
            new_path, splitted_name[1:]
        )
        if found:
            return file_name, remain_len, found
        file_name1 = os.path.join(cur_path, splitted_name[0], "__init__.pyi")
        if os.path.isfile(file_name1):
            return file_name1, len(splitted_name), True
        file_name2 = os.path.join(cur_path, splitted_name[0] + ".pyi")
        if os.path.isfile(file_name2):
            return file_name2, len(splitted_name), True
        return "", -1, False

    @staticmethod
    def _find_file(module_name):
        dirs = ["3.7", "3.6", "3", "2and3", "2"]
        for d in dirs:
            file_name, remain_len, found = Typer._recursive_find_file(
                f"typeshed/stdlib/{d}", module_name
            )
            if found:
                break
        if not found:
            raise Exception(f"{module_name} not found in typeshed")
        return file_name, remain_len

    def _record_type(self, splitted_name):
        file_name, remain_len = Typer._find_file(splitted_name[:-1])
        with open(file_name) as f:
            parsed_ast = ast.parse(f.read())
        v = Visitor()
        v.visit(parsed_ast)
        cur = self.storage
        for i in splitted_name[:-remain_len]:
            if i not in cur:
                cur[i] = {}
            cur = cur[i]
        for key, val in v.storage.items():
            cur[key] = val

    def _get_type(self, splitted_name):
        cur = self.storage
        for i in splitted_name:
            cur = cur[i]
        return cur

    def get_type(self, name):
        splitted_name = name.split(".")
        if splitted_name[0] in dir(builtins):
            splitted_name = ["builtins"] + splitted_name
        try:
            return self._get_type(splitted_name)
        except KeyError:
            self._record_type(splitted_name)
            return self._get_type(splitted_name)


if __name__ == "__main__":
    x = Typer()

    print(x.get_type("int.__add__"))
    print(x.get_type("int.__sub__"))
    print(x.get_type("list.append"))
    print(x.get_type("str.expandtabs"))
    print(x.get_type("os.path.isfile"))
    print(x.get_type("os.path.altsep"))

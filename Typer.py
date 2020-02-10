import ast
import builtins
import os
from base import FunctionDef, TypeVar
import sys


class Typer:
    def __init__(self):
        self.data = {}

    @staticmethod
    def _parse_args(node):
        from_type = []
        for i in node.args:
            if i.arg == "self":
                continue
            anno = i.annotation
            if isinstance(anno, ast.Name):
                if anno.id == "_T":
                    from_type.append(TypeVar())
                else:
                    from_type.append(anno.id)
            elif isinstance(anno, ast.Subscript):
                return (anno.value.id.lower(),)
        return tuple(from_type)

    @staticmethod
    def _parse_anno(node):
        if isinstance(node, ast.Name):
            if node.id == "_T":
                return TypeVar()
            else:
                return node.id
        elif isinstance(node, ast.Subscript):
            return node.value.id.lower()
        elif isinstance(node, ast.Constant):
            if not node.value:
                return "None"

    @staticmethod
    def _parse_func(node):
        from_type = Typer._parse_args(node.args)
        to_type = Typer._parse_anno(node.returns)
        return FunctionDef(from_type, to_type)

    @staticmethod
    def _parse_class(node):
        data = {}
        for i in node.body:
            if isinstance(i, ast.FunctionDef):
                data[i.name] = Typer._parse_func(i)
            elif isinstance(i, ast.AnnAssign):
                data[i.target.id] = Typer._parse_anno(i.annotation)
            elif isinstance(i, ast.If):
                data = {**data, **Typer._parse_if(i)}
        return data

    @staticmethod
    def _parse_if(node):
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
                return {}
        else:
            return {}
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
            return Typer._parse(node.body)
        else:
            return Typer._parse(node.orelse)

    @staticmethod
    def _parse(node):
        data = {}
        for i in node:
            if isinstance(i, ast.ClassDef):
                data[i.name] = Typer._parse_class(i)
            elif isinstance(i, ast.FunctionDef):
                data[i.name] = Typer._parse_func(i)
            elif isinstance(i, ast.If):
                data = {**data, **Typer._parse_if(i)}
            elif isinstance(i, ast.AnnAssign):
                data[i.target.id] = Typer._parse_anno(i.annotation)
        return data

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
        cur = self.data
        for i in splitted_name[:-remain_len]:
            if i not in cur:
                cur[i] = {}
            cur = cur[i]
        for key, val in Typer._parse(parsed_ast.body).items():
            cur[key] = val

    def _get_type(self, splitted_name):
        cur = self.data
        for i in splitted_name:
            cur = cur[i]
        return cur

    def get_type(self, name):
        splitted_name = name.split(".")
        if splitted_name[0] in dir(builtins):
            splitted_name = ["builtins"] + splitted_name
        try:
            self._get_type(splitted_name)
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
    # import json

    # print(json.dumps(x.data, default=lambda o: str(o)))

import ast
import os
from base import Function

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
                from_type.append(i.annotation.id)
            elif isinstance(anno, ast.Subscript):
                return ("todo",)
        return tuple(from_type)

    @staticmethod
    def _parse_ret(node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Subscript):
            return "todo"

    @staticmethod
    def _parse_func(node):
        from_type = Typer._parse_args(node.args)
        to_type = Typer._parse_ret(node.returns)
        return Function(from_type, to_type)

    @staticmethod
    def _parse_class(node):
        data = {}
        for i in node.body:
            if isinstance(i, ast.FunctionDef):
                data[i.name] = Typer._parse_func(i)
        return data

    @staticmethod
    def _parse(node):
        data = {}
        for i in node:
            if isinstance(i, ast.ClassDef):
                data[i.name] = Typer._parse_class(i)
            elif isinstance(i, ast.FunctionDef):
                data[i.name] = Typer._parse_func(i)
            elif isinstance(i, ast.If):
                data = {**data, **Typer._parse(i.body)}
                #todo parse other branches
        return data
        
    def _record_type(self, module_name):
        dirs = ["3.7", "3.6", "3", "2and3", "2"]
        for d in dirs:
            file_name = f"typeshed/stdlib/{d}/{module_name}.pyi"
            if os.path.isfile(file_name):
                with open(file_name) as f:
                    x = ast.parse(f.read())
                self.data[module_name] = Typer._parse(x.body)
                break
        
    def _get_type(self, name):
        cur = self.data
        for i in name.split("."):
            cur = cur[i]
        return cur

    def get_type(self, name):
        try:
            self._get_type(name)
        except KeyError:
            self._record_type(name.split(".")[0])
        return self._get_type(name)
        

if __name__ == "__main__":
    x = Typer()
    print(x.get_type("builtins.int.__add__"))
    print(x.get_type("builtins.int.__sub__"))
    print(x.get_type("builtins.str.expandtabs"))
    print(x.get_type("os.path.isfile"))

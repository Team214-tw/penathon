import uuid
import typing
import ast


class TypeVar:
    def __init__(self):
        self.id = uuid.uuid4()
        self.instance = typing.TypeVar(str(self.id))

    def __str__(self):
        # TypeVar
        if isinstance(self.instance, typing.TypeVar):
            return f"T{str(self.id).split('-')[0]}"
        # built-in type
        elif isinstance(self.instance, type):
            return f"{self.instance.__name__}"
        # typing
        else:
            return f"{str(self.instance)}"


class Union:
    def __init__(self, type_list):
        self.Ts = self._flatten(type_list)

    def __str__(self):
        Ts = []
        for x in self.Ts:
            # built-in type
            if isinstance(x, type):
                Ts.append(x.__name__)
            else:
                Ts.append(str(x))

        if len(Ts) == 0:
            return "None"
        if len(Ts) == 1:
            return Ts[0]
        else:
            Ts_str = ", ".join(Ts)
            return f"typing.Union[{Ts_str}]"

    def _flatten(self, parameters):
        # Flatten out Union[Union[...], ...].
        params = []
        for p in parameters:
            if isinstance(p, Union):
                params.extend(p.Ts)
            else:
                params.append(p)
        # Weed out duplicates
        return tuple(set(params))


class FunctionDef:
    def __init__(self, from_type, to_type):
        self.from_type = from_type
        self.to_type = to_type

    def __str__(self):
        return f"({tuple(map(str, self.from_type))} -> {self.to_type})"


class TypeOperator(object):
    # Todo
    def __init__(self, name, types):
        self.name = name
        self.types = types

    def __str__(self):
        num_types = len(self.types)
        if num_types == 0:
            return self.name
        elif num_types == 2:
            return "({0} {1} {2})".format(str(self.types[0]), self.name, str(self.types[1]))
        else:
            return "{0} {1}" .format(self.name, ' '.join(self.types))


class FunctionDef:
    def __init__(self, from_type, to_type):
        self.from_type = from_type
        self.to_type = to_type

    def __str__(self):
        return f"({tuple(map(str, self.from_type))} -> {self.to_type})"

def assign_convert(body):
    new_body = list()
    lineno_adj = 0
    for i in body:
        if isinstance(i, ast.Assign):
            lineno_adj -= 1
            for j in i.targets:
                lineno_adj += 1
                new_body.append(ast.Assign(targets=[j], value=i.value, lineno=i.lineno + lineno_adj))
        else:
            new_body.append(i)
    return new_body



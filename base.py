import uuid
import typing


class TypeVar:
    def __init__(self):
        self.id = uuid.uuid4()
        self.instance = None

    def __str__(self):
        if self.instance:
            return f"{str(self.instance)}"
        else:
            return f"T{str(self.id).split('-')[0]}"


class Constant:
    def __init__(self, value):
        self.T = type(value)

    def __str__(self):
        return self.T.__name__


class List:
    def __init__(self):
        self.T = TypeVar()

    def __str__(self):
        return "list"


class Dict:
    def __init__(self):
        self.T = TypeVar()

    def __str__(self):
        return "dict"


class Set:
    def __init__(self):
        self.T = TypeVar()

    def __str__(self):
        return "set"


class Tuple:
    def __init__(self):
        self.T = TypeVar()

    def __str__(self):
        return "tuple"


class Union:
    def __init__(self, type_list):
        self.Ts = type_list

    def __str__(self):
        Ts_str = ", ".join(str(x) for x in self.Ts)
        return f"Union[{Ts_str}]"


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

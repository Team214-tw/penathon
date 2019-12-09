import uuid


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


class Function:
    def __init__(self, from_type, to_type):
        self.from_type = from_type
        self.to_type = to_type

    def __str__(self):
        return f"({tuple(map(str, self.from_type))} -> {self.to_type})"


class TypeVariable:
    def __init__(self):
        self.id = uuid.uuid4()
        self.instance = None

    def __str__(self):
        if self.instance:
            return f"{str(self.instance)}"
        else:
            return f"T{str(self.id).split('-')[0]}"

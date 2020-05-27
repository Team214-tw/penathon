import typing

class TypeWrapper:
    def __init__(self, t, class_name=None):
        self.type = t
        self.class_name = class_name

        if self.is_list(): self.list_init()
        elif self.is_tuple(): self.tuple_init()

    # init
    def list_init(self):
        self.list_type = self.get_callable_ret(self.type['pop'].reveal())

    def tuple_init(self):
        self.tuple_type = self.get_callable_ret(self.type['__getitem__'].reveal()).__args__[0]

    # condition checking
    def is_list(self):
        return self.class_name == 'list'

    def is_tuple(self):
        return self.class_name == 'tuple'

    # type operation
    def typeof(self, name):
        if self.class_name is not None:
            return self.type[name]
        else:
            raise Exception("Not a class instance or class definition")

    def bound(self, t):
        if self.is_list():
            self.bound_type_var(self.list_type, t)
        elif self.is_tuple():
            self.bound_type_var(self.tuple_type, t)
    
    @staticmethod
    def get_callable_ret(t):
        return t.__args__[-1]

    @staticmethod
    def reveal_type_var(t):
        if t.__bound__ is None:
            return typing.Any
        else:
            return t.__bound__

    @staticmethod
    def bound_type_var(tv, t):
        old = tv.__bound__
        if old is not None:
            tv.__bound__ = typing.Union[old, t]
        else:
            tv.__bound__ = t

    # get real type
    def reveal(self):
        if self.is_list():
            return typing.List[self.reveal_type_var(self.list_type)]

        elif self.is_tuple():
            return typing.Tuple[self.reveal_type_var(self.tuple_type)]

        elif self.class_name:
            return self.class_name

        return self.type

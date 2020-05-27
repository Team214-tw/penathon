import typing

class TypeWrapper:
    def __init__(self, t, class_name=None):
        self.type = t
        self.class_name = class_name

        if self.is_list(): self.list_init()
        elif self.is_tuple(): self.tuple_init()
        elif self.is_set(): self.set_init()
        elif self.is_dict(): self.dict_init()

    # init
    def list_init(self):
        self.list_type = self.get_callable_ret(self.type['pop'].reveal())

    def tuple_init(self):
        self.tuple_type = self.get_callable_ret(self.type['__getitem__'].reveal()).__args__[0]

    def set_init(self):
        self.set_type = self.get_callable_ret(self.type['pop'].reveal())

    def dict_init(self):
        t = self.type['__getitem__'].reveal()
        self.key_type = self.get_callable_args(t)[0]
        self.value_type = self.get_callable_ret(t)

    # condition checking
    def is_list(self):
        return self.class_name == 'list'

    def is_tuple(self):
        return self.class_name == 'tuple'

    def is_set(self):
        return self.class_name == 'set'

    def is_dict(self):
        return self.class_name == 'dict'

    def is_class(self):
        return self.class_name is not None

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

        elif self.is_set():
            self.bound_type_var(self.set_type, t)

        elif self.is_dict():
            self.bound_type_var(self.key_type, t[0])
            self.bound_type_var(self.value_type, t[1])

    @staticmethod
    def get_callable_ret(t):
        return t.__args__[-1]

    @staticmethod
    def get_callable_args(t):
        return t.__args__[:-1]

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

        elif self.is_set():
            return typing.Set[self.reveal_type_var(self.set_type)]

        elif self.is_dict():
            key_type = self.reveal_type_var(self.key_type)
            value_type = self.reveal_type_var(self.value_type)
            return typing.Dict[key_type, value_type]

        elif self.class_name:
            return self.class_name

        return self.type

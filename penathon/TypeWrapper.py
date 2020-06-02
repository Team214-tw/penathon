import typing
import uuid

from .Constant import BASIC_TYPES, BASIC_TYPES_LIST, TYPE_DICT

CLASS_MAP = {}

class TypeWrapper:
    def __init__(self, t, class_name=None, lazy_func_info=None, need_refresh=False):
        self.type = t
        self.class_name = class_name
        self.lazy_func_info = lazy_func_info
        self.need_refresh = need_refresh

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

    def is_function(self):
        return self.is_Callable(self.type)

    def is_type_var(self):
        return isinstance(self.type, typing.TypeVar)

    def is_union(self):
        return self.is_Union(self.type)

    def can_coerce(self, t): # can self.type coerce to t
        if self.reveal() is int and t.reveal() is float:
            return True
        elif self.reveal() is int and t.reveal() is complex:
            return True
        elif self.reveal() is float and t.reveal() is complex:
            return True
        else:
            return False

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

        else:
            self.bound_type_var(self.type, t)

    # reveal TypeWrapper to real type
    def reveal(self):
        if self.is_list():
            return typing.List[self.list_type]

        elif self.is_tuple():
            return typing.Tuple[self.tuple_type, ...]

        elif self.is_set():
            return typing.Set[self.set_type]

        elif self.is_dict():
            return typing.Dict[self.key_type, self.value_type]

        elif self.class_name:
            if self.class_name in BASIC_TYPES:
                return BASIC_TYPES[self.class_name]
            else:
                try:
                    return CLASS_MAP[self.class_name]
                except KeyError:
                    CLASS_MAP[self.class_name] = type(self.class_name, (object,), {})
                    return CLASS_MAP[self.class_name]

        return self.type

    def reveal_origin(self):
        r = self.reveal()
        try:
            return r.__origin__
        except:
            if r in BASIC_TYPES_LIST:
                return r
            return type(r)

    # refresh new type variable instance
    def refresh(self):
        self.tv_map = {}
        if not isinstance(self.type, dict):
            self.type = self.refresh_recursive(self.type)

    def refresh_recursive(self, t):
        if isinstance(t, typing.TypeVar):
            try:
                return self.tv_map[str(t)]
            except KeyError:
                self.tv_map[str(t)] = typing.TypeVar(str(uuid.uuid4()))
                return self.tv_map[str(t)]

        elif TypeWrapper.is_Callable(t):
            arg_list = TypeWrapper.get_callable_args(t)
            body_type = TypeWrapper.get_callable_ret(t)
            if len(arg_list) == 1 and arg_list[0] is Ellipsis:
                arg_list = ...
            else:
                for idx, a in enumerate(arg_list):
                    arg_list[idx] = self.refresh_recursive(a)
                body_type = self.refresh_recursive(body_type)
            return typing.Callable[arg_list, body_type]

        elif TypeWrapper.is_List(t):
            list_type = TypeWrapper.get_list_type(t)
            return typing.List[self.refresh_recursive(list_type)]

        elif TypeWrapper.is_Tuple(t):
            tupleType = [self.refresh_recursive(t) for t in TypeWrapper.get_tuple_type(t)]
            return typing.Tuple[tuple(tupleType)]

        elif TypeWrapper.is_Dict(t):
            keyType = self.refresh_recursive(TypeWrapper.get_dict_type_key(t))
            valueType = self.refresh_recursive(TypeWrapper.get_dict_type_value(t))
            return typing.Dict[keyType, valueType]

        elif TypeWrapper.is_Set(t):
            setType = self.refresh_recursive(TypeWrapper.get_set_type(t))
            return typing.Set[setType]

        elif TypeWrapper.is_Union(t):
            unionType = [self.refresh_recursive(t) for t in TypeWrapper.get_union_type(t)]
            return typing.Union[tuple(unionType)]

        elif hasattr(t, '__args__') and len(t.__args__) == 1:
            try:
                type_name = t._name
                arg = self.refresh_recursive(t.__args__[0])
                return TYPE_DICT[type_name][arg]
            except:
                return t

        else:
            return t

    # helper function
    @staticmethod
    def is_Callable(t):  # caveat: can't use isinstance
        return hasattr(t, '_name') and t._name == 'Callable'

    @staticmethod
    def is_List(t):  # caveat: can't use isinstance
        return hasattr(t, '_name') and t._name == 'List'

    @staticmethod
    def is_Tuple(t):  # caveat: can't use isinstance
        return hasattr(t, '_name') and t._name == 'Tuple'

    @staticmethod
    def is_Dict(t):  # caveat: can't use isinstance
        return hasattr(t, '_name') and t._name == 'Dict'

    @staticmethod
    def is_Set(t):  # caveat: can't use isinstance
        return hasattr(t, '_name') and t._name == 'Set'

    @staticmethod
    def is_Union(t):  # caveat: can't use isinstance
        try:
            return t.__origin__._name == 'Union'
        except AttributeError:
            return False

    @staticmethod
    def has_arg(t):
        return hasattr(t, '__args__') and len(t.__args__) != 0

    @staticmethod
    def get_arg(t):
        return list(t.__args__)

    @staticmethod
    def new_type_var():
        return TypeWrapper(typing.TypeVar(str(uuid.uuid4())))

    @staticmethod
    def get_list_type(t):
        return t.__args__[0]

    @staticmethod
    def get_tuple_type(t):
        return list(t.__args__)

    @staticmethod
    def get_dict_type_key(t):
        return t.__args__[0]

    @staticmethod
    def get_dict_type_value(t):
        return t.__args__[1]

    @staticmethod
    def get_set_type(t):
        return t.__args__[0]

    @staticmethod
    def get_union_type(t):
        return list(t.__args__)

    @staticmethod
    def get_callable_ret(t):
        return t.__args__[-1]

    @staticmethod
    def get_callable_args(t):
        return list(t.__args__[:-1])

    @staticmethod
    def get_typevar_bound(t):
        return t.__bound__

    @staticmethod
    def bound_type_var(tv, t):
        if not isinstance(tv, typing.TypeVar):
            raise Exception(f"{tv} is not a type variable")
        if isinstance(tv.__bound__, typing.TypeVar):
            TypeWrapper.bound_type_var(tv.__bound__, t)
        else:
            if tv.__bound__ is not None and tv.__bound__ != t:
                raise Exception(f"Bound {t} failed. Type Variable {tv} is already bound: {tv.__bound__}")
            else:
                tv.__bound__ = t

    @staticmethod
    def reveal_type_var(t):
        if isinstance(t, typing.TypeVar):
            if t.__bound__ is None:
                return typing.Any
            else:
                return TypeWrapper.reveal_type_var(t.__bound__)

        elif TypeWrapper.is_Callable(t):
            arg_list = TypeWrapper.get_callable_args(t)
            body_type = TypeWrapper.get_callable_ret(t)
            if len(arg_list) == 1 and arg_list[0] is Ellipsis:
                arg_list = ...
            else:
                for idx, a in enumerate(arg_list):
                    arg_list[idx] = TypeWrapper.reveal_type_var(a)
                body_type = TypeWrapper.reveal_type_var(body_type)
            return typing.Callable[arg_list, body_type]

        elif TypeWrapper.is_List(t):
            list_type = TypeWrapper.get_list_type(t)
            return typing.List[TypeWrapper.reveal_type_var(list_type)]

        elif TypeWrapper.is_Tuple(t):
            tupleType = [TypeWrapper.reveal_type_var(t) for t in TypeWrapper.get_tuple_type(t)]
            return typing.Tuple[tuple(tupleType)]

        elif TypeWrapper.is_Dict(t):
            keyType = TypeWrapper.reveal_type_var(TypeWrapper.get_dict_type_key(t))
            valueType = TypeWrapper.reveal_type_var(TypeWrapper.get_dict_type_value(t))
            return typing.Dict[keyType, valueType]

        elif TypeWrapper.is_Set(t):
            setType = TypeWrapper.reveal_type_var(TypeWrapper.get_set_type(t))
            return typing.Set[setType]

        elif TypeWrapper.is_Union(t):
            unionType = [TypeWrapper.reveal_type_var(t) for t in TypeWrapper.get_union_type(t)]
            return typing.Union[tuple(unionType)]

        elif hasattr(t, '__args__') and len(t.__args__) == 1:
            try:
                type_name = t._name
                arg = TypeWrapper.reveal_type_var(t.__args__[0])
                return TYPE_DICT[type_name][arg]
            except:
                return t

        else:
            return t

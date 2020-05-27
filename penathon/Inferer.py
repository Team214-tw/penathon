import ast
import copy
import builtins
from typing import Dict, List, Set, Tuple, Union, Callable, TypeVar, Any

from .TypeWrapper import TypeWrapper, BASIC_TYPES
from .SymTable import SymTable


class Inferer:
    def __init__(self):
        self.env = SymTable('root')
        self.func_ret_type = []

    def infer(self, tree):
        for i in tree.body:
            self.infer_stmt(i)

        return self.env

    def infer_stmt(self, e):
        if isinstance(e, ast.FunctionDef):
            newSymTable = SymTable(e.name, self.env)
            self.env = newSymTable

            # save current function return type (for nested function)
            func_ret_type_bak = self.func_ret_type
            self.func_ret_type = []

            # create type variables for each argument
            argList = list()
            for i in e.args.args:
                argName = i.arg
                argTypeVar = TypeWrapper.new_type_var()
                self.env.add(argName, argTypeVar)
                argList.append(argTypeVar.reveal())

            # infer body type
            for i in e.body:
                self.infer_stmt(i)

            # generate body type
            bodyType = Union[tuple(self.func_ret_type)] if len(self.func_ret_type) else type(None)
            inferredType = TypeWrapper(Callable[argList, bodyType])

            # restore function return type
            self.func_ret_type = func_ret_type_bak

            # context switch back
            self.env = self.env.parent
            self.env.add(e.name, inferredType)

        elif isinstance(e, ast.AsyncFunctionDef):
            pass

        elif isinstance(e, ast.ClassDef):
            newSymTable = SymTable(e.name, self.env)
            self.env = newSymTable

            for i in e.body:
                self.infer_stmt(i)

            classType = TypeWrapper(self.env.env, e.name)
            self.env = self.env.parent
            self.env.add(e.name, classType)

        elif isinstance(e, ast.Return):
            valueType = self.infer_expr(e.value)
            self.func_ret_type.append(valueType.reveal())

        elif isinstance(e, ast.Delete):
            pass

        elif isinstance(e, ast.Assign):
            valueType = self.infer_expr(e.value)
            for t in e.targets:
                self.env.add(t.id, valueType)

        elif isinstance(e, ast.AugAssign):
            pass

        elif isinstance(e, ast.AnnAssign):
            pass

        elif isinstance(e, ast.For):
            pass

        elif isinstance(e, ast.AsyncFor):
            pass

        elif isinstance(e, ast.While):
            # infBodyType = []
            # self.infer_expr(e.test)
            # for i in e.body:
            #     potentialType = self.infer_stmt(i)

            # # generate body type
            # if len(infBodyType) == 0:
            #     bodyType = None
            # else:
            #     bodyType = Union[tuple(infBodyType)]

            # return bodyType
            pass

        elif isinstance(e, ast.If):
            # # infer body type
            # infBodyType = []
            # for i in e.body:
            #     potentialType = self.infer_stmt(i)
            # for i in e.orelse:
            #     potentialType = self.infer_stmt(i)

            # # generate body type
            # if len(infBodyType) == 0:
            #     bodyType = None
            # else:
            #     bodyType = Union[tuple(infBodyType)]

            # return bodyType
            pass

        elif isinstance(e, ast.With):
            pass

        elif isinstance(e, ast.AsyncWith):
            pass

        elif isinstance(e, ast.Raise):
            pass

        elif isinstance(e, ast.Try):
            # for i in e.body:
            #     potentialType = self.infer_stmt(i)

            # for i in e.handlers:
            #     #  exceptionType = self.infer_expr(i.type)
            #     #  if not isinstance(exceptionType, BaseException):
            #         #  raise Exception("Exception type does not match.")

            #     for j in i.body:
            #         potentialType = self.infer_stmt(j)
            pass

        elif isinstance(e, ast.Assert):
            pass

        elif isinstance(e, ast.Import):
            for n in e.names:
                module_name = n.name
                self.env.add_module(module_name, n.asname)

        elif isinstance(e, ast.ImportFrom):
            for n in e.names:
                module_name = f"{e.module}.{n.name}"
                self.env.add_module(module_name, n.asname)

        elif isinstance(e, ast.Global):
            pass

        elif isinstance(e, ast.Nonlocal):
            pass

        elif isinstance(e, ast.Expr):
            return self.infer_expr(e.value)

        elif isinstance(e, ast.Pass):
            pass

        elif isinstance(e, ast.Break):
            pass

        elif isinstance(e, ast.Continue):
            pass

        else:
            raise Exception(f"{e.lineno}: Unsupported syntax")

    def infer_expr(self, e):
        if isinstance(e, ast.BoolOp):
            bool_inst = self.env.typeof('bool')
            return TypeWrapper(bool_inst.env, 'bool')

        # elif isinstance(e, ast.NamedExpr):
        #     pass

        elif isinstance(e, ast.BinOp):
            leftType = self.infer_expr(e.left)
            rightType = self.infer_expr(e.right)

            # backup for error restore used
            leftOriType = leftType.type
            leftOriClass = leftType.class_name
            rightOriType = rightType.type
            rightOriClass = rightType.class_name

            # promote type if can coerce
            if leftType.can_coerce(rightType):
                leftType.type = rightType.type
                leftType.class_name = rightType.class_name
            elif rightType.can_coerce(leftType):
                rightType.type = leftType.type
                rightType.class_name = leftType.class_name

            def do(a, op_func, b):
                argList = [b.reveal()]
                resultType = TypeWrapper.new_type_var().reveal()
                callType = TypeWrapper(Callable[argList, resultType])
                funcType = a.typeof(op_func)
                self.unify(callType, funcType)
                inferedType = TypeWrapper.reveal_type_var(resultType)
                return TypeWrapper(inferedType)

            try: # left op
                return do(leftType, self._get_magic(e.op, reverse=False), rightType)
            except: # right op
                try:
                    return do(rightType, self._get_magic(e.op, reverse=True), leftType)
                except:
                    leftType.type = leftOriType
                    leftType.class_name = leftOriClass
                    rightType.type = rightOriType
                    rightType.class_name = rightOriClass
                    raise Exception(f"BinOp failed: {leftType.reveal()} {type(e.op).__name__} {rightType.reveal()}")

        elif isinstance(e, ast.UnaryOp):
            # TODO: Invert | Not | UAdd | USub, check magic function
            return self.infer_expr(e.operand)

        elif isinstance(e, ast.Lambda):
            # newSymTable = SymTable(None, self.env)
            # self.env = newSymTable

            # # create type variables for each argument
            # argList = list()
            # for i in e.args.args:
            #     argName = i.arg
            #     argTypeVar = TypeVar(self._get_tvid())
            #     self.env.write(argName, AssignSymbol(argName, argTypeVar))
            #     argList.append(argTypeVar)

            # # infer body type
            # bodyType = self.infer_expr(e.body)
            # inferredType = Callable[argList, bodyType]

            # # context switch back
            # self.env = self.env.parent

            # return inferredType
            pass

        elif isinstance(e, ast.IfExp):
            pass

        elif isinstance(e, ast.Dict):
            dict_class_def = self.env.typeof('builtins').typeof('dict')
            dict_class_inst = TypeWrapper(dict_class_def.env, class_name='dict')

            for i in range(len(e.keys)):
                key_type = self.infer_expr(e.keys[i]).reveal()
                value_type = self.infer_expr(e.values[i]).reveal()
                dict_class_inst.bound((key_type, value_type))

            return dict_class_inst

        elif isinstance(e, ast.Set):
            set_class_def = self.env.typeof('builtins').typeof('set')
            set_class_inst = TypeWrapper(set_class_def.env, class_name='set')

            for elmt in e.elts:
                set_class_inst.bound(self.infer_expr(elmt).reveal())

            return set_class_inst

        elif isinstance(e, ast.ListComp):
            pass

        elif isinstance(e, ast.SetComp):
            pass

        elif isinstance(e, ast.DictComp):
            pass

        elif isinstance(e, ast.GeneratorExp):
            pass

        elif isinstance(e, ast.Await):
            pass

        elif isinstance(e, ast.Yield):
            pass

        elif isinstance(e, ast.YieldFrom):
            pass

        elif isinstance(e, ast.Compare):
            pass

        elif isinstance(e, ast.Call):
            callType = self.infer_expr(e.func)

            if callType.is_class(): # TODO: list, tuple, dict, set arguments
                return callType

            funcType = callType
            argList = []
            for i in e.args:
                argType = self.infer_expr(i).reveal()
                argList.append(argType)
            resultType = TypeWrapper.new_type_var().reveal()
            callType = TypeWrapper(Callable[argList, resultType])

            self.unify(callType, funcType)
            inferedType = TypeWrapper.reveal_type_var(resultType)

            return TypeWrapper(inferedType)

        elif isinstance(e, ast.FormattedValue):
            pass

        elif isinstance(e, ast.JoinedStr):
            pass

        elif isinstance(e, ast.Constant):
            typeName = type(e.value).__name__
            constant_inst = self.env.typeof(typeName)
            return TypeWrapper(constant_inst.env, class_name=typeName)

        elif isinstance(e, ast.Attribute):
            valueType = self.infer_expr(e.value)
            return valueType.typeof(e.attr)

        elif isinstance(e, ast.Subscript):
            pass

        elif isinstance(e, ast.Starred):
            pass

        elif isinstance(e, ast.Name):
            if e.id in BASIC_TYPES:
                return TypeWrapper(BASIC_TYPES[e.id])
            return self.env.typeof(e.id)

        elif isinstance(e, ast.List):
            list_class_def = self.env.typeof('builtins').typeof('list')
            list_class_inst = TypeWrapper(list_class_def.env, class_name='list')

            for elmt in e.elts:
                list_class_inst.bound(self.infer_expr(elmt).reveal())

            return list_class_inst

        elif isinstance(e, ast.Tuple):
            tuple_class_def = self.env.typeof('builtins').typeof('tuple')
            tuple_class_inst = TypeWrapper(tuple_class_def.env, class_name='tuple')

            for elmt in e.elts:
                tuple_class_inst.bound(self.infer_expr(elmt).reveal())

            return tuple_class_inst

        else:
            raise Exception(f"{e.lineno}: Unsupported syntax")

    # helpers
    # -------
    def unify(self, caller, callee):
        if caller.reveal() == callee.reveal():
            return

        elif caller.is_type_var():
            caller.union(callee.reveal())

        elif callee.is_type_var():
            callee.union(caller.reveal())

        elif caller.is_function() and callee.is_function():
            caller_args = TypeWrapper.get_callable_args(caller.reveal())
            callee_args = TypeWrapper.get_callable_args(callee.reveal())
            caller_body = TypeWrapper.get_callable_ret(caller.reveal())
            callee_body = TypeWrapper.get_callable_ret(callee.reveal())

            if len(caller_args) != len(callee_args):
                raise Exception("Function args not matched")

            for i, (caller_t, callee_t) in enumerate(zip(caller_args, callee_args)):
                self.unify(TypeWrapper(caller_t), TypeWrapper(callee_t))
            self.unify(TypeWrapper(caller_body), TypeWrapper(callee_body))

        else:
            raise Exception(f"Function args: {caller.reveal()} and {callee.reveal()} are not matched")

    @staticmethod
    def _get_magic(op, reverse=None):
        if reverse:
            magics = {
                "Add": "__radd__",
                "Sub": "__rsub__",
                "Mult": "__rmul__",
                "Div": "__rdiv__",
                "Mod": "__rmod__",
                "Or": "__ror__",
                "And": "__rand__",
            }
            return magics[type(op).__name__]
        else:
            magics = {
                "Add": "__add__",
                "Sub": "__sub__",
                "Mult": "__mul__",
                "Div": "__div__",
                "Mod": "__mod__",
                "Or": "__or__",
                "And": "__and__",
            }
            return magics[type(op).__name__]


    # def _get_func_name(self, func):
    #     # a.b.c()
    #     if isinstance(func, ast.Attribute):
    #         return f"{self._get_func_name(func.value)}.{func.attr}"
    #     # a()
    #     elif isinstance(func, ast.Name):
    #         return func.id
    #     # [].append
    #     else:
    #         return type(func).__name__.lower()

    # # return original type of typing type. e.g. typing.Dict => dict
    # @staticmethod
    # def _get_original_type(t):
    #     if isinstance(t, TypeVar):
    #         t = t.__bound__
    #     try:
    #         return t.__origin__
    #     except AttributeError:
    #         return t

    # def _get_tvid(self):
    #     self.tvid += 1
    #     return f"T{str(self.tvid)}"

    # @staticmethod
    # def _unify_callable(a, b):
    #     if not isinstance(a, Callable):
    #         raise Exception(f"Expect unify type of Callable, but {type(a)} is received")

    #     if not isinstance(b, Callable):
    #         raise Exception(f"Expect unify type of Callable, but {type(b)} is received")

    #     a_args_type = list(a.__args__[:-1])
    #     a_return_type = a.__args__[-1]
    #     b_args_type = list(b.__args__[:-1])
    #     b_return_type = b.__args__[-1]

    #     if len(a_args_type) != len(b_args_type):
    #         raise Exception("Function args not matched")

    #     for i, (p, q) in enumerate(zip(a_args_type, b_args_type)):
    #         a_args_type[i], b_args_type[i] = Inferer._unify(p, q)
    #     a_return_type, b_return_type = Inferer._unify(a_return_type, b_return_type)

    #     a.__args__ = (*a_args_type, a_return_type)
    #     b.__args__ = (*b_args_type, b_return_type)

    # @staticmethod
    # def _unify(a, b):
    #     # built-in type equivalent
    #     if a == b:
    #         return a, b

    #     elif Inferer._coerce(a, b):
    #         return b, b

    #     elif Inferer._coerce(b, a):
    #         return a, a

    #     # a, b are both TypeVar, unify each bound type
    #     elif isinstance(a, TypeVar) and isinstance(b, TypeVar):
    #         ab = [a.__bound__] if a.__bound__ is not None else []
    #         ab = [*ab, b.__bound__] if b.__bound__ is not None else [*ab]
    #         if len(ab) > 0:
    #             Inferer._bound_TypeVar(a, Union[tuple(ab)])
    #             Inferer._bound_TypeVar(b, Union[tuple(ab)])
    #         return a, b

    #     # only a is TypeVar, set upper_bound of a to Union[b, a.__bound__]
    #     elif isinstance(a, TypeVar):
    #         ab = [b, a.__bound__] if a.__bound__ is not None else [b]
    #         Inferer._bound_TypeVar(a, Union[tuple(ab)])
    #         return a, b

    #     # only b is TypeVar, set upper_bound of a to Union[a, b.__bound__]
    #     elif isinstance(b, TypeVar):
    #         ab = [a, b.__bound__] if b.__bound__ is not None else [a]
    #         Inferer._bound_TypeVar(b, Union[tuple(ab)])
    #         return a, b

    #     # typing type equivalent
    #     elif hasattr(a, '_name') and hasattr(b, '_name') and a._name == b._name:
    #         return a, b

    #     else:
    #         raise Exception(f"Function args: {a} and {b} are not matched")

    # @staticmethod
    # def _bound_TypeVar(tv, t):
    #     tv.__init__(tv.__name__, bound=t)

import ast
import copy
import builtins
from typing import Dict, List, Set, Tuple, Union, Callable, TypeVar, Any

from .TypeWrapper import TypeWrapper
from .Constant import BASIC_TYPES
from .SymTable import SymTable

DEBUG = False

class Inferer:
    def __init__(self):
        self.env = SymTable('root')
        self.func_ret_type = []
        self.cur_class = None

    def infer(self, tree):
        self.infer_body(tree)
        return self.env

    def infer_body(self, e):
        for i in e.body:
            if DEBUG:
                self.infer_stmt(i)
            else:
                try:
                    self.infer_stmt(i)
                except:
                    continue


    def infer_stmt(self, e):
        if isinstance(e, ast.FunctionDef):
            self.env.add(e.name, TypeWrapper(None, lazy_func_info={
                'tree': e,
                'env': self.env,
                'cur_class': self.cur_class,
            }))

        elif isinstance(e, ast.AsyncFunctionDef):
            pass

        elif isinstance(e, ast.ClassDef):
            newSymTable = SymTable(e.name, self.env)
            self.env = newSymTable

            cur_class_bak = self.cur_class
            classType = TypeWrapper(self.env.env, e.name)
            self.cur_class = classType

            self.infer_body(e)

            # restore context
            self.cur_class = cur_class_bak
            self.env = self.env.parent
            self.env.add(e.name, classType)

        elif isinstance(e, ast.Return):
            valueType = self.infer_expr(e.value)
            self.func_ret_type.append(TypeWrapper.reveal_type_var(valueType.reveal()))

        elif isinstance(e, ast.Delete):
            pass

        elif isinstance(e, ast.Assign):
            valueType = self.infer_expr(e.value)
            for t in e.targets:
                if isinstance(t, ast.Subscript):
                    continue
                else:
                    env, name = self.infer_expr(t)
                    if name not in env:
                        env[name] = valueType

        elif isinstance(e, ast.AugAssign):
            pass

        elif isinstance(e, ast.AnnAssign):
            pass

        elif isinstance(e, ast.For):
            env, target = self.infer_expr(e.target)
            if target in env:
                raise Exception(f"{target} already has type {env[target].reveal()}")

            try:
                iter = self.infer_expr(e.iter).typeof("__iter__").reveal()
                if not TypeWrapper.is_Callable(iter):
                    raise Exception("__iter__ is not callable")
                iter_type = TypeWrapper.get_callable_ret(iter) # typing.Iterator[T]
                item_type = TypeWrapper.get_arg(iter_type)[0]
                env[target] = TypeWrapper(item_type)
            except:            
                env[target] = TypeWrapper(Any)

            self.infer_body(e)

            for n in e.orelse:
                self.infer_stmt(n)

        elif isinstance(e, ast.AsyncFor):
            pass

        elif isinstance(e, ast.While):
            self.infer_expr(e.test)

            self.infer_body(e)

            for i in e.orelse:
                self.infer_stmt(i)

        elif isinstance(e, ast.If):
            self.infer_expr(e.test)

            self.infer_body(e)

            for i in e.orelse:
                self.infer_stmt(i)

        elif isinstance(e, ast.With):
            for i in e.items:
                contextType = self.infer_expr(i.context_expr)
                if i.optional_vars:
                    env, name = self.infer_expr(i.optional_vars)
                    env[name] = contextType

            self.infer_body(e)

        elif isinstance(e, ast.AsyncWith):
            pass

        elif isinstance(e, ast.Raise):
            pass

        elif isinstance(e, ast.Try):
            self.infer_body(e)

            for i in e.handlers:
                self.infer_body(i)

            for i in e.finalbody:
                self.infer_stmt(i)

        elif isinstance(e, ast.Assert):
            pass

        elif isinstance(e, ast.Import):
            for n in e.names:
                module_name = n.name
                self.env.add_module(module_name, n.asname)

        elif isinstance(e, ast.ImportFrom):
            for n in e.names:
                module_name = f"{e.module}"
                self.env.add_module(module_name, n.asname, target=n.name)

        elif isinstance(e, ast.Global):
            env = self.env
            while env.parent is not None:
                env = env.parent

            for i in e.names:
                if i in self.env.env:
                    raise Exception(f"{i} is assigned to before global declaration")
                self.env.add(i, env.typeof(i))

        elif isinstance(e, ast.Nonlocal):
            if self.env.parent is None:
                raise Exception("nonlocal declaration not allowed at module level")
            env = self.env.parent
            if env.parent is None:
                raise Exception(f"no binding for nonlocal {e.names[0]} found")

            for i in e.names:
                if i not in env.env:
                    raise Exception(f"no binding for nonlocal {i} found")
                self.env.add(i, env.typeof(i))

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
            return bool_inst

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
                self.unify_function(callType, funcType)

            try: # left op
                do(leftType, self._get_magic(e.op, reverse=False), rightType)
                return leftType
            except: # right op
                try:
                    do(rightType, self._get_magic(e.op, reverse=True), leftType)
                    return rightType
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
            env_bak = self.env
            self.env = SymTable(None, None)

            # create type variables for each argument
            argList = list()
            for i in e.args.args:
                argName = i.arg
                argTypeVar = TypeWrapper.new_type_var()
                self.env.add(argName, argTypeVar)
                argList.append(argTypeVar.reveal())

            # generate body type
            bodyType = self.infer_expr(e.body).reveal()
            inferredType = TypeWrapper(Callable[argList, bodyType])

            # context switch back
            self.env = env_bak

            return inferredType

        elif isinstance(e, ast.IfExp):
            pass

        elif isinstance(e, ast.Dict):
            dict_class_inst = self.env.typeof('dict')
            key_type = []
            value_type = []
            for i in range(len(e.keys)):
                key_type.append(self.infer_expr(e.keys[i]).reveal())
                value_type.append(self.infer_expr(e.values[i]).reveal())
            dict_class_inst.bound((Union[tuple(key_type)], Union[tuple(value_type)]))
            return dict_class_inst

        elif isinstance(e, ast.Set):
            set_class_inst = self.env.typeof('set')
            set_type = [self.infer_expr(elmt).reveal() for elmt in e.elts]
            if len(set_type) > 0:
                set_class_inst.bound(Union[tuple(set_type)])
            return set_class_inst

        elif isinstance(e, ast.ListComp): # TODO: generator
            list_class_inst = self.env.typeof('list')
            return list_class_inst

        elif isinstance(e, ast.SetComp): # TODO: generator
            set_class_inst = self.env.typeof('set')
            return set_class_inst

        elif isinstance(e, ast.DictComp): # TODO: generator
            dict_class_inst = self.env.typeof('dict')
            return dict_class_inst

        elif isinstance(e, ast.GeneratorExp): # TODO: generator
            tuple_class_inst = self.env.typeof('tuple')
            return tuple_class_inst

        elif isinstance(e, ast.Await):
            pass

        elif isinstance(e, ast.Yield):
            pass

        elif isinstance(e, ast.YieldFrom):
            pass

        elif isinstance(e, ast.Compare):
            bool_inst = self.env.typeof('bool')
            return bool_inst

        elif isinstance(e, ast.Call):
            callee = self.infer_expr(e.func)

            if callee.is_class():
                try:
                    funcType = callee.typeof("__init__") # try to unify init
                    self.lazy_func_load(funcType)
                except:
                    return callee # create instance
            else:
                funcType = callee

            argList = []
            for i in e.args:
                argType = self.infer_expr(i).reveal()
                argList.append(argType)
            caller_ret = TypeWrapper.new_type_var().reveal()
            caller = TypeWrapper(Callable[argList, caller_ret])

            self.unify_function(caller, funcType)

            if callee.is_class():
                return callee # create instance
            else:
                return TypeWrapper(caller_ret)

        elif isinstance(e, ast.FormattedValue):
            pass

        elif isinstance(e, ast.JoinedStr):
            pass

        elif isinstance(e, ast.Constant):
            if e.value is None:
                return TypeWrapper(type(None))
            typeName = type(e.value).__name__
            constant_inst = self.env.typeof(typeName)
            return constant_inst

        elif isinstance(e, ast.Attribute):
            ctx = type(e.ctx).__name__
            if ctx == "Store":
                valueType = self.infer_expr(e.value)
                if not valueType.is_class():
                    raise Exception("Can not store variable to non class instance")
                return valueType.type, e.attr
            elif ctx == "Load":
                valueType = self.infer_expr(e.value)
                attrType = valueType.typeof(e.attr)
                if attrType.lazy_func_info is not None:
                    return self.lazy_func_load(attrType)
                return attrType
            else:
                raise Exception("Not implemented attribute operation")

        elif isinstance(e, ast.Subscript):
            ctx = type(e.ctx).__name__
            if ctx == "Store": # TODO: need unify
                pass
            elif ctx == "Load": # TODO: check index type
                valueType = self.infer_expr(e.value)
                valueRealType = TypeWrapper.reveal_type_var(valueType.reveal())

                if TypeWrapper.has_arg(valueRealType):
                    itemType = TypeWrapper.get_arg(valueRealType)
                    if TypeWrapper.is_List(valueRealType) or TypeWrapper.is_Tuple(valueRealType) or TypeWrapper.is_Set(valueRealType):
                        typeName = itemType[0].__name__
                        constant_inst = self.env.typeof(typeName)
                        return constant_inst
                    elif TypeWrapper.is_Dict(valueRealType):
                        typeName = itemType[1].__name__
                        constant_inst = self.env.typeof(typeName)
                        return constant_inst
                    else:
                        raise Exception("Not implemented load")
                else:
                    raise Exception("Not implemented load")
            else:
                raise Exception("Not implemented attribute operation")

        elif isinstance(e, ast.Starred):
            pass

        elif isinstance(e, ast.Name):
            ctx = type(e.ctx).__name__
            if ctx == "Store":
                return self.env.env, e.id
            elif ctx == "Load":
                if e.id in BASIC_TYPES:
                    return TypeWrapper(BASIC_TYPES[e.id])
                nameType = self.env.typeof(e.id)
                if isinstance(nameType, SymTable):
                    return TypeWrapper(nameType.env, e.id)
                elif nameType.lazy_func_info is not None:
                    return self.lazy_func_load(nameType)
                return nameType
            else:
                raise Exception("Not implemented name operation")

        elif isinstance(e, ast.List):
            list_class_inst = self.env.typeof('list')
            list_type = [self.infer_expr(elmt).reveal() for elmt in e.elts]
            if len(list_type) > 0:
                list_class_inst.bound(Union[tuple(list_type)])
            return list_class_inst

        elif isinstance(e, ast.Tuple):
            tuple_class_inst = self.env.typeof('tuple')
            tuple_type = [self.infer_expr(elmt).reveal() for elmt in e.elts]
            if len(tuple_type) > 0:
                tuple_class_inst.bound(Union[tuple(tuple_type)])
            return tuple_class_inst

        else:
            raise Exception(f"{e.lineno}: Unsupported syntax")

    def lazy_func_load(self, func_type):
        try:
            e = func_type.lazy_func_info['tree']
            env = func_type.lazy_func_info['env']
            cur_class = func_type.lazy_func_info['cur_class']

            # context save
            env_bak = self.env
            self.env = SymTable(e.name, env)
            cur_class_bak = self.cur_class
            self.cur_class = cur_class
            func_ret_type_bak = self.func_ret_type
            self.func_ret_type = []

            # check is infering class
            if self.cur_class is not None:
                self.env.add(e.args.args[0].arg, self.cur_class)
                args = e.args.args[1:]
            else:
                args = e.args.args

            # infer args type
            argList = []
            default_start = len(args) - len(e.args.defaults)
            for i, arg in enumerate(args):
                argName = arg.arg
                if i >= default_start:
                    argType = self.infer_expr(e.args.defaults[i - default_start])
                else:
                    argType = TypeWrapper.new_type_var()
                self.env.add(argName, argType)
                argList.append(argType.reveal())

            # infer body type
            self.infer_body(e)

            # generate body type
            if self.cur_class is not None and e.name == "__init__":
                bodyType = type(None)
            else:
                bodyType = Union[tuple(self.func_ret_type)] if len(self.func_ret_type) else type(None)
            func_type.type = Callable[argList, bodyType]
            func_type.lazy_func_info = None

            return func_type
        finally:
            # restore context
            self.func_ret_type = func_ret_type_bak
            self.env = env_bak
            self.cur_class = cur_class_bak


    # helpers
    # -------
    def unify_function(self, caller: TypeWrapper, callee: TypeWrapper):
        caller_args = TypeWrapper.get_callable_args(caller.reveal())
        callee_args = TypeWrapper.get_callable_args(callee.reveal())
        caller_body = TypeWrapper.get_callable_ret(caller.reveal())
        callee_body = TypeWrapper.get_callable_ret(callee.reveal())

        for caller_t, callee_t in zip(caller_args, callee_args):
            if caller_t is Ellipsis or callee_t is Ellipsis:
                break
            self.unify_arg(TypeWrapper(caller_t), TypeWrapper(callee_t))
        self.unify_ret(TypeWrapper(caller_body), TypeWrapper(callee_body))

    def unify_arg(self, caller, callee):
        if caller.is_type_var() and callee.is_type_var():
            callee.bound(caller.reveal())
        elif issubclass(caller.reveal_origin(), callee.reveal_origin()):
            if TypeWrapper.has_arg(caller.reveal()) and TypeWrapper.has_arg(callee.reveal()):
                caller_args = TypeWrapper.get_arg(caller.reveal())
                callee_args = TypeWrapper.get_arg(callee.reveal())
                for caller_t, callee_t in zip(caller_args, callee_args):
                    if caller_t is Ellipsis or callee_t is Ellipsis:
                        break
                    self.unify_arg(TypeWrapper(caller_t), TypeWrapper(callee_t))
        else:
            self.unify(caller, callee)

    def unify_ret(self, caller, callee):
        if caller.is_type_var() and callee.is_type_var():
            caller.bound(callee.reveal())
        elif issubclass(caller.reveal_origin(), callee.reveal_origin()):
            if TypeWrapper.has_arg(caller.reveal()) and TypeWrapper.has_arg(callee.reveal()):
                caller_args = TypeWrapper.get_arg(caller.reveal())
                callee_args = TypeWrapper.get_arg(callee.reveal())
                for caller_t, callee_t in zip(caller_args, callee_args):
                    if caller_t is Ellipsis or callee_t is Ellipsis:
                        break
                    self.unify_ret(TypeWrapper(caller_t), TypeWrapper(callee_t))
        else:
            self.unify(caller, callee)

    def unify(self, caller, callee):
        if caller.is_type_var():
            caller.bound(callee.reveal())
        elif callee.is_type_var():
            callee.bound(caller.reveal())
        elif TypeWrapper.reveal_type_var(caller.reveal()) == TypeWrapper.reveal_type_var(callee.reveal()):
            return
        elif callee.is_union():
            unionType = TypeWrapper.reveal_type_var(TypeWrapper.get_arg(callee.reveal()))
            callerType = TypeWrapper.reveal_type_var(caller.reveal())
            if callerType in unionType:
                return
            else:
                raise Exception(f"Function args: {caller.reveal()} and {callee.reveal()} are not matched")
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


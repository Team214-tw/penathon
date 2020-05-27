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
        self.cur_class = None

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

            # check is infering class
            if self.cur_class is not None:
                self.env.add(e.args.args[0].arg, self.cur_class)
                argList = []
                for i in e.args.args[1:]:
                    argName = i.arg
                    argTypeVar = TypeWrapper.new_type_var()
                    self.env.add(argName, argTypeVar)
                    argList.append(argTypeVar.reveal())
            else:
                argList = []
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

            # restore context
            self.func_ret_type = func_ret_type_bak
            self.env = self.env.parent
            self.env.add(e.name, inferredType)

        elif isinstance(e, ast.AsyncFunctionDef):
            pass

        elif isinstance(e, ast.ClassDef):
            newSymTable = SymTable(e.name, self.env)
            self.env = newSymTable

            cur_class_bak = self.cur_class
            classType = TypeWrapper(self.env.env, e.name)
            self.cur_class = classType

            for i in e.body:
                self.infer_stmt(i)

            # restore context
            self.cur_class = cur_class_bak
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
                if isinstance(t, ast.Subscript):
                    continue
                else:
                    env, name = self.infer_expr(t)
                    env[name] = valueType

        elif isinstance(e, ast.AugAssign):
            pass

        elif isinstance(e, ast.AnnAssign):
            pass

        elif isinstance(e, ast.For):
            # iter = self.infer_expr(e.iter)
            env, target = self.infer_expr(e.target)
            if target in env:
                raise Exception(f"{target} already has type {env[target].reveal()}")
            env[target] = TypeWrapper(Any)

            for n in e.body:
                self.infer_stmt(n)

            for n in e.orelse:
                self.infer_stmt(n)

        elif isinstance(e, ast.AsyncFor):
            pass

        elif isinstance(e, ast.While):
            self.infer_expr(e.test)

            for i in e.body:
                self.infer_stmt(i)

            for i in e.orelse:
                self.infer_stmt(i)

        elif isinstance(e, ast.If):
            self.infer_expr(e.test)

            for i in e.body:
                self.infer_stmt(i)

            for i in e.orelse:
                self.infer_stmt(i)

        elif isinstance(e, ast.With):
            for i in e.items:
                contextType = self.infer_expr(i.context_expr)
                if i.optional_vars:
                    env, name = self.infer_expr(i.optional_vars)
                    env[name] = contextType

            for i in e.body:
                self.infer_stmt(i)

        elif isinstance(e, ast.AsyncWith):
            pass

        elif isinstance(e, ast.Raise):
            pass

        elif isinstance(e, ast.Try):
            for i in e.body:
                self.infer_stmt(i)

            for i in e.handlers:
                for j in i.body:
                    self.infer_stmt(j)

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
                self.unify(callType, funcType)

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

            for i in range(len(e.keys)):
                key_type = self.infer_expr(e.keys[i]).reveal()
                value_type = self.infer_expr(e.values[i]).reveal()
                dict_class_inst.bound((key_type, value_type))

            return dict_class_inst

        elif isinstance(e, ast.Set):
            set_class_inst = self.env.typeof('set')

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
            callee = self.infer_expr(e.func)

            if callee.is_class():
                try:
                    funcType = callee.typeof("__init__") # try to unify init
                except:
                    return callee
            else:
                funcType = callee

            argList = []
            for i in e.args:
                argType = self.infer_expr(i).reveal()
                argList.append(argType)
            caller_ret = TypeWrapper.new_type_var().reveal()
            caller = TypeWrapper(Callable[argList, caller_ret])

            self.unify(caller, funcType)

            if callee.is_class():
                return callee
            else:
                inferedType = TypeWrapper.reveal_type_var(caller_ret)
                return TypeWrapper(inferedType)

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
                return valueType.typeof(e.attr)
            else:
                raise Exception("Not implemented attribute operation")

        elif isinstance(e, ast.Subscript):
            pass

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
                return nameType
            else:
                raise Exception("Not implemented name operation")

        elif isinstance(e, ast.List):
            list_class_inst = self.env.typeof('list')

            for elmt in e.elts:
                list_class_inst.bound(self.infer_expr(elmt).reveal())

            return list_class_inst

        elif isinstance(e, ast.Tuple):
            tuple_class_inst = self.env.typeof('tuple')

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

        elif caller.is_type_var() and callee.is_type_var():
            callerType = TypeWrapper.get_typevar_bound(caller.reveal())
            calleeType = TypeWrapper.get_typevar_bound(callee.reveal())
            unionType = Union[tuple(filter(None, [callerType, calleeType]))]
            caller.union(unionType)
            callee.union(unionType)

        elif caller.is_type_var():
            caller.union(callee.reveal())

        elif callee.is_type_var():
            callee.union(caller.reveal())

        elif caller.is_function() and callee.is_function():
            caller_args = TypeWrapper.get_callable_args(caller.reveal())
            callee_args = TypeWrapper.get_callable_args(callee.reveal())
            caller_body = TypeWrapper.get_callable_ret(caller.reveal())
            callee_body = TypeWrapper.get_callable_ret(callee.reveal())

            # if len(caller_args) != len(callee_args):
            #     raise Exception("Function args not matched")

            for caller_t, callee_t in zip(caller_args, callee_args):
                if caller_t is Ellipsis or callee_t is Ellipsis:
                    break
                self.unify(TypeWrapper(caller_t), TypeWrapper(callee_t))
            self.unify(TypeWrapper(caller_body), TypeWrapper(callee_body))

        elif callee.is_union():
            unionType = TypeWrapper.reveal_type_var(TypeWrapper.get_arg(callee))
            callerType = TypeWrapper.reveal_type_var(caller.reveal())
            if caller.reveal() in unionType:
                return

        elif issubclass(caller.reveal_origin(), callee.reveal_origin()):
            if TypeWrapper.has_arg(caller) and TypeWrapper.has_arg(callee):
                caller_args = TypeWrapper.get_arg(caller)
                callee_args = TypeWrapper.get_arg(callee)
                for caller_t, callee_t in zip(caller_args, callee_args):
                    self.unify(TypeWrapper(caller_t), TypeWrapper(callee_t))

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


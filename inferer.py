import ast
import copy

from typing import Dict, List, Set, Tuple, Union, Callable, TypeVar, Any
from Typer import Typer
from preprocessor import assign_convert


class Inferer:
    def __init__(self):
        self.env = dict()
        self.seeker = Typer()
        self.visitReturn = False
        self.tvid = 0 # type variable id

    def infer_stmt(self, e):
        if isinstance(e, ast.FunctionDef):
            envBak = copy.deepcopy(self.env)

            # create type variables for each argument
            argList = list()
            for i in e.args.args:
                argName = i.arg
                argTypeVar = TypeVar(self._get_tvid())
                self.env[argName] = argTypeVar
                argList.append(argTypeVar)

            # infer body type
            infBodyType = []
            for i in e.body:
                potentialType = self.infer_stmt(i)
                if self.visitReturn:
                    infBodyType.append(potentialType)
                    self.visitReturn = False

            # generate body type
            if len(infBodyType) == 0:
                bodyType = None
            else:
                bodyType = Union[tuple(infBodyType)]
            inferredType = Callable[argList, bodyType]

            # context switch back
            self.env = envBak
            self.env[e.name] = inferredType

            return inferredType

        elif isinstance(e, ast.AsyncFunctionDef):
            pass

        elif isinstance(e, ast.ClassDef):
            pass

        elif isinstance(e, ast.Return):
            self.visitReturn = True
            return self.infer_expr(e.value)

        elif isinstance(e, ast.Delete):
            pass

        elif isinstance(e, ast.Assign):
            valueType = self.infer_expr(e.value)
            for t in e.targets:
                varName = t.id
                # variable may not exist in context, or may be a TypaVar
                if isinstance(self.env.get(varName), TypeVar):
                    tv = self.env[varName]
                    tv.__init__(tv.__name__, bound=valueType)
                else:
                    self.env[varName] = valueType
            return valueType

        elif isinstance(e, ast.AugAssign):
            pass

        elif isinstance(e, ast.AnnAssign):
            pass

        elif isinstance(e, ast.For):
            pass

        elif isinstance(e, ast.AsyncFor):
            pass

        elif isinstance(e, ast.While):
            pass

        elif isinstance(e, ast.If):
            # infer body type
            infBodyType = []
            for i in e.body:
                potentialType = self.infer_stmt(i)
                if self.visitReturn:
                    infBodyType.append(potentialType)
            for i in e.orelse:
                potentialType = self.infer_stmt(i)
                if self.visitReturn:
                    infBodyType.append(potentialType)

            # generate body type
            if len(infBodyType) == 0:
                bodyType = None
            else:
                bodyType = Union[tuple(infBodyType)]

            return bodyType

        elif isinstance(e, ast.With):
            pass

        elif isinstance(e, ast.AsyncWith):
            pass

        elif isinstance(e, ast.Raise):
            pass

        elif isinstance(e, ast.Try):
            pass

        elif isinstance(e, ast.Assert):
            pass

        elif isinstance(e, ast.Import):
            for i in e.names:
                asname = i.asname or i.name
                self.env[asname] = i.name

        elif isinstance(e, ast.ImportFrom):
            for i in e.names:
                asname = i.asname or i.name
                func_name = f"{e.module}.{i.name}"
                try:
                    self.env[asname] = self.seeker.get_type(func_name)
                except KeyError:
                    raise Exception(f"Type not found: {funcName}")
            return e, TypeVar(self._get_tvid())

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
            pass

        # elif isinstance(e, ast.NamedExpr):
        #     pass

        elif isinstance(e, ast.BinOp):
            # get op function from left side
            leftType = self.infer_expr(e.left)
            rightType = self.infer_expr(e.right)
            funcName = self._get_magic(e.op)
            try:
                leftOriType = self._get_original_type(leftType).__name__.lower()
                funcType = self.seeker.get_type(f"{leftOriType}.{funcName}")
            except KeyError:
                raise Exception(f"{leftType} object has no method {funcName}")

            # infer and perform type coercion
            argList = [
                rightType,
            ]
            resultType = TypeVar(self._get_tvid())
            self._unify_callable(Callable[argList, resultType], funcType)

            return resultType

        elif isinstance(e, ast.UnaryOp):
            pass

        elif isinstance(e, ast.Lambda):
            envBak = copy.deepcopy(self.env)

            # create type variables for each argument
            argList = list()
            for i in e.args.args:
                argName = i.arg
                argTypeVar = TypeVar(self._get_tvid())
                self.env[argName] = argTypeVar
                argList.append(argTypeVar)

            # infer body type
            bodyType = self.infer_expr(e.body)
            inferredType = Callable[argList, bodyType]

            # context switch back
            self.env = envBak

            return inferredType

        elif isinstance(e, ast.IfExp):
            pass

        elif isinstance(e, ast.Dict):
            if len(e.keys) == 0:
                keyType = Any
            else:
                keyType = []
                for i in e.keys:
                    keyType.append(self.infer_expr(i))
                keyType = Union[tuple(keyType)]

            if len(e.values) == 0:
                valueType = Any
            else:
                valueType = []
                for i in e.values:
                    valueType.append(self.infer_expr(i))
                valueType = Union[tuple(valueType)]

            return Dict[keyType, valueType]

        elif isinstance(e, ast.Set):
            return Set

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
            # get function type
            funcName = self._get_func_name(e.func)
            funcType = self.infer_expr(ast.Name(funcName))

            # infer call type
            argList = list()
            for i in e.args:
                argType = self.infer_expr(i)
                argList.append(argType)
            resultType = TypeVar(self._get_tvid())

            # infer def type and result type
            self._unify_callable(Callable[argList, resultType], funcType)

            return resultType

        elif isinstance(e, ast.FormattedValue):
            pass

        elif isinstance(e, ast.JoinedStr):
            pass

        elif isinstance(e, ast.Constant):
            return type(e.value)

        elif isinstance(e, ast.Attribute):
            pass

        elif isinstance(e, ast.Subscript):
            pass

        elif isinstance(e, ast.Starred):
            pass

        elif isinstance(e, ast.Name):
            if e.id in self.env:
                return self.env[e.id]
            else:
                try:
                    func_name = self._original_func_name(e.id)
                    return self.seeker.get_type(func_name)
                except KeyError:
                    raise Exception(f"Unbound var {e.id}")

        elif isinstance(e, ast.List):
            bodyType = []
            for elt in e.elts:
                bodyType.append(self.infer_expr(elt))
            bodyType = tuple(bodyType)
            return List[Union[bodyType]] if len(bodyType) > 0 else List

        elif isinstance(e, ast.Tuple):
            bodyType = []
            for elt in e.elts:
                bodyType.append(self.infer_expr(elt))
            bodyType = tuple(bodyType)
            return Tuple[Union[bodyType]] if len(bodyType) > 0 else Tuple

        else:
            raise Exception(f"{e.lineno}: Unsupported syntax")

    # helpers
    # -------
    def _get_func_name(self, func):
        # a.b.c()
        if isinstance(func, ast.Attribute):
            return f"{self._get_func_name(func.value)}.{func.attr}"
        # a()
        elif isinstance(func, ast.Name):
            return func.id
        # [].append
        else:
            return type(func).__name__.lower()

    # a.append => list.append
    def _original_func_name(self, name):
        splitted_name = name.split(".")
        for i, s in enumerate(splitted_name):
            if s in self.env:
                ts = self.env[s]
                # str in context cases: import time as T
                if not isinstance(ts, str):
                    ts = self._get_original_type(ts).__name__.lower()
                splitted_name[i] = ts
        return ".".join(splitted_name)

    # return original type of typing type. e.g. typing.Dict => dict
    @staticmethod
    def _get_original_type(t):
        if isinstance(t, TypeVar):
            t = t.__bound__
        try:
            return t.__origin__
        except AttributeError:
            return t

    def _get_tvid(self):
        self.tvid += 1
        return f"T{str(self.tvid)}"

    @staticmethod
    def _unify_callable(a, b):
        a_args_type = a.__args__[:-1]
        a_return_type = a.__args__[-1]
        b_args_type = b.__args__[:-1]
        b_return_type = b.__args__[-1]

        if len(a_args_type) != len(b_args_type):
            raise Exception("Function args not matched")

        for p, q in zip(a_args_type, b_args_type):
            Inferer._unify(p, q)
        Inferer._unify(a_return_type, b_return_type)

    @staticmethod
    def _unify(a, b):
        # built-in type equivalent
        if a == b:
            return

        # a, b are both TypeVar, unify each bound type
        elif isinstance(a, TypeVar) and isinstance(b, TypeVar):
            ab = []
            if a.__bound__ is not None: ab.append(a.__bound__) 
            if b.__bound__ is not None: ab.append(b.__bound__) 
            if len(ab) > 0:
                a.__init__(a.__name__, bound=Union[tuple(ab)])
                b.__init__(b.__name__, bound=Union[tuple(ab)])

        # only a is TypeVar, bound b to a
        elif isinstance(a, TypeVar):
            ab = [b]
            if a.__bound__ is not None: ab.append(a.__bound__)
            a.__init__(a.__name__, bound=Union[tuple(ab)])

        # only b is TypeVar, bound a to b
        elif isinstance(b, TypeVar):
            ab = [a]
            if b.__bound__ is not None: ab.append(b.__bound__)
            b.__init__(b.__name__, bound=Union[tuple(ab)])

        # typing type equivalent
        elif a._name == b._name:
            return

        else:
            raise Exception(f"Function args: {a} and {b} are not matched")

    @staticmethod
    def _get_magic(op):
        magics = {
            'Add': '__add__',
            'Sub': '__sub__',
            'Mult': '__mul__',
            'Div': '__div__',
            'Mod': '__mod__',
            'Or': '__or__',
            'And': '__and__',
        }
        return magics[type(op).__name__]

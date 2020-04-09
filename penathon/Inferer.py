import ast
import copy
from typing import Dict, List, Set, Tuple, Union, Callable, TypeVar, Any

from .Typer import Typer
from .CodeGenerator import CodeGenerator
from .Preprocessor import Preprocessor

PARENT_ENV = 0

TYPE = 1
TYPE_CLASS = 0

CLASS_NAME = 2


class Inferer:
    def __init__(self):
        self.env = {0: 0}
        self.seeker = Typer()
        self.cg = CodeGenerator()
        self.preprocessor = Preprocessor()
        self.visitReturn = False
        self.tvid = 0  # type variable id

    def _search_env(self, target):
        this_env = self.env
        while True:
            if target in this_env:
                return this_env[target]
            elif isinstance(this_env[PARENT_ENV], dict):
                this_env = this_env[PARENT_ENV]
            else:
                break
        return None

    def infer(self, tree):
        mtree = self.preprocessor.preprocess(tree)  # modified tree

        for i in mtree.body:
            inferedType = self.infer_stmt(i)
            if isinstance(inferedType, TypeVar):
                print(i.lineno, f"{inferedType} => {inferedType.__bound__}")
            else:
                print(i.lineno, inferedType)

        return mtree

    def infer_stmt(self, e):
        if isinstance(e, ast.FunctionDef):
            self.env = {
                PARENT_ENV: self.env
            }

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
            self.env = self.env[PARENT_ENV]
            self.env[e.name] = inferredType

            self.cg.gen_functionDef(e, inferredType)

            return inferredType

        elif isinstance(e, ast.AsyncFunctionDef):
            pass

        elif isinstance(e, ast.ClassDef):
            self.env = {
                PARENT_ENV: self.env,
                TYPE: TYPE_CLASS
            }

            infBodyType = []
            for i in e.body:
                _ = self.infer_stmt(i)

            classType = self.env
            classType[CLASS_NAME] = e.name

            self.env = self.env[PARENT_ENV]
            self.env[e.name] = classType
            print(self.env)

        elif isinstance(e, ast.Return):
            self.visitReturn = True
            return self.infer_expr(e.value)

        elif isinstance(e, ast.Delete):
            pass

        elif isinstance(e, ast.Assign):
            # ast.Assign transform to AnnAssign during preprocessing
            pass

        elif isinstance(e, ast.AugAssign):
            pass

        elif isinstance(e, ast.AnnAssign):
            valueType = self.infer_expr(e.value)
            varName = e.target.id

            if isinstance(self._search_env(varName), TypeVar):
                tv = self._search_env(varName)
                tv.__init__(tv.__name__, bound=valueType)
            else:
                self.env[varName] = valueType

            # for original ast.Assign node
            if e.annotation is None:
                self.cg.gen_assign(e, valueType)

            return valueType

        elif isinstance(e, ast.For):
            pass

        elif isinstance(e, ast.AsyncFor):
            pass

        elif isinstance(e, ast.While):
            infBodyType = []
            self.infer_expr(e.test)
            for i in e.body:
                potentialType = self.infer_stmt(i)
                if self.visitReturn:
                    infBodyType.append(potentialType)

            # generate body type
            if len(infBodyType) == 0:
                bodyType = None
            else:
                bodyType = Union[tuple(infBodyType)]

            return bodyType

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
            for i in e.body:
                potentialType = self.infer_stmt(i)

            for i in e.handlers:
                #  exceptionType = self.infer_expr(i.type)
                #  if not isinstance(exceptionType, BaseException):
                    #  raise Exception("Exception type does not match.")

                for j in i.body:
                    potentialType = self.infer_stmt(j)


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
                    raise Exception(f"Type not found: {func_name}")

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
            leftType = self.infer_expr(e.left)
            rightType = self.infer_expr(e.right)

            if Inferer._coerce(leftType, rightType):
                leftType = rightType

            funcName = self._get_magic(e.op)
            try:
                leftOriType = self._get_original_type(
                    leftType).__name__.lower()
                funcType = self.seeker.get_type(f"{leftOriType}.{funcName}")
            except KeyError:
                raise Exception(f"{leftType} object has no method {funcName}")

            argList = [rightType]
            resultType = TypeVar(self._get_tvid())
            self._unify_callable(Callable[argList, resultType], funcType)

            return resultType.__bound__

        elif isinstance(e, ast.UnaryOp):
            pass

        elif isinstance(e, ast.Lambda):
            self.env = {
                PARENT_ENV: self.env
            }

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
            self.env = self.env[PARENT_ENV]

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

            return resultType.__bound__

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
            name_path = e.id.split(".")
            if self._search_env(name_path[0]):
                if (name_path) == 1:
                    return self._search_env(e.id)
                else:
                    now = self._search_env(name_path[0])
                    try:
                        for i in name_path[1:]:
                            now = now[i]
                        return now
                    except KeyError:
                        raise Exception(f"Unbound var {e.id}")
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
            if self._search_env(s):
                ts = self._search_env(s)
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
    def _unify_callable(_a, _b):
        a = _a
        b = _b
        if isinstance(a, dict):
            a =  a["__init__"]
            a_args_type = list(a.__args__[1:-1])
            a_args_type = list(a.__args__[:-1])
            a_return_type = _a[CLASS_NAME]
            #  a_return_type = _a
        else:
            a_args_type = list(a.__args__[:-1])
            a_return_type = a.__args__[-1]

        if isinstance(b, dict):
            b = b["__init__"]
            b_args_type = list(b.__args__[1:-1])
            b_return_type = _b[CLASS_NAME]
        else:
            b_args_type = list(b.__args__[:-1])
            b_return_type = b.__args__[-1]

        #  if not isinstance(a, Callable):
            #  raise Exception(
                #  f"Expect unify type of Callable, but {type(a)} is received")

        #  if not isinstance(b, Callable):
            #  raise Exception(
                #  f"Expect unify type of Callable, but {type(b)} is received")


        if len(a_args_type) != len(b_args_type):
            raise Exception("Function args not matched")

        for i, (p, q) in enumerate(zip(a_args_type, b_args_type)):
            a_args_type[i], b_args_type[i] = Inferer._unify(p, q)
        a_return_type, b_return_type = Inferer._unify(
            a_return_type, b_return_type)

        a.__args__ = (*a_args_type, a_return_type)
        b.__args__ = (*b_args_type, b_return_type)

    @staticmethod
    def _unify(a, b):
        # built-in type equivalent
        if a == b:
            return a, b

        elif Inferer._coerce(a, b):
            return b, b

        elif Inferer._coerce(b, a):
            return a, a

        # a, b are both TypeVar, unify each bound type
        elif isinstance(a, TypeVar) and isinstance(b, TypeVar):
            ab = [a.__bound__] if a.__bound__ is not None else []
            ab = [*ab, b.__bound__] if b.__bound__ is not None else [*ab]
            if len(ab) > 0:
                Inferer._bound_TypeVar(a, Union[tuple(ab)])
                Inferer._bound_TypeVar(b, Union[tuple(ab)])
            return a, b

        # only a is TypeVar, set upper_bound of a to Union[b, a.__bound__]
        elif isinstance(a, TypeVar):
            ab = [b, a.__bound__] if a.__bound__ is not None else [b]
            Inferer._bound_TypeVar(a, Union[tuple(ab)])
            return a, b

        # only b is TypeVar, set upper_bound of a to Union[a, b.__bound__]
        elif isinstance(b, TypeVar):
            ab = [a, b.__bound__] if b.__bound__ is not None else [a]
            Inferer._bound_TypeVar(b, Union[tuple(ab)])
            return a, b

        # typing type equivalent
        elif a._name == b._name:
            return a, b

        else:
            raise Exception(f"Function args: {a} and {b} are not matched")

    @staticmethod
    def _bound_TypeVar(tv, t):
        tv.__init__(tv.__name__, bound=t)

    @staticmethod
    def _get_magic(op):
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

    # check p can coerce to q
    @staticmethod
    def _coerce(p, q):
        if p is int and q is float:
            return True

        elif p is int and q is complex:
            return True

        elif p is float and q is complex:
            return True

        elif isinstance(p, TypeVar):
            return Inferer._coerce(p.__bound__, q)

        else:
            return False
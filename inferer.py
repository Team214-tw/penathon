import ast
import copy

from base import Constant, Dict, Function, List, Set, Tuple, TypeVar, Union
from Typer import Typer


class Inferer:
    def __init__(self):
        self.env = dict()
        self.seeker = Typer()

    def infer_stmt(self, e):
        if isinstance(e, ast.FunctionDef):
            envBak = copy.deepcopy(self.env)

            # create type variables for each argument
            argList = list()
            for i in e.args.args:
                argName = i.arg
                argTypeVar = TypeVar()
                self.env[argName] = argTypeVar
                argList.append(argTypeVar)

            # infer body type
            infBodyType = []
            for i in e.body:
                if isinstance(i, ast.Return):
                    infBodyType.append(self.infer_stmt(i))
                else:
                    self.infer_stmt(i)

            # generate body type
            if len(infBodyType) == 0:
                bodyType = None
            elif len(infBodyType) == 1:
                bodyType = infBodyType[0]
            else:
                bodyType = Union(infBodyType)
            inferredType = Function(from_type=argList, to_type=bodyType)

            # context switch back
            self.env = envBak
            self.env[e.name] = inferredType

            return inferredType

        elif isinstance(e, ast.AsyncFunctionDef):
            pass

        elif isinstance(e, ast.ClassDef):
            pass

        elif isinstance(e, ast.Return):
            return self.infer_expr(e.value)

        elif isinstance(e, ast.Delete):
            pass

        elif isinstance(e, ast.Assign):
            valueType = self.infer_expr(e.value)
            for t in e.targets:
                varName = t.id
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
            pass

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
                self.env[asname] = f"{e.module}.{i.name}"

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

        elif isinstance(e, ast.NamedExpr):
            pass

        elif isinstance(e, ast.BinOp):
            # get op function from left side
            leftType = self.infer_expr(e.left)
            rightType = self.infer_expr(e.right)
            funcName = self._get_magic(e.op)
            try:
                funcType = self.seeker.get_type(f"{leftType}.{funcName}")
            except KeyError:
                raise Exception(f"{leftType} object has no method {funcName}")

            # infer and perform type coercion
            argList = (rightType,)
            resultType = TypeVar()
            self._unify(Function(argList, resultType), funcType)

            return resultType

        elif isinstance(e, ast.UnaryOp):
            pass

        elif isinstance(e, ast.Lambda):
            envBak = copy.deepcopy(self.env)

            # create type variables for each argument
            argList = list()
            for i in e.args.args:
                argName = i.arg
                argTypeVar = TypeVar()
                self.env[argName] = argTypeVar
                argList.append(argTypeVar)

            # infer body type
            infBodyType = []
            for i in e.body:
                if isinstance(i, ast.Return):
                    infBodyType.append(self.infer_stmt(i))
                else:
                    self.infer_stmt(i)

            # generate body type
            if len(infBodyType) == 0:
                bodyType = None
            elif len(infBodyType) == 1:
                bodyType = infBodyType[0]
            else:
                bodyType = Union(infBodyType)
            inferredType = Function(from_type=argList, to_type=bodyType)

            # context switch back
            self.env = envBak

            return inferredType

        elif isinstance(e, ast.IfExp):
            pass

        elif isinstance(e, ast.Dict):
            return Dict()

        elif isinstance(e, ast.Set):
            return Set()

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
                argType = infer(i)
                argList.append(argType)
            resultType = TypeVar()

            # infer def type and result type
            self._unify(Function(argList, resultType), funcType)

            return resultType

        elif isinstance(e, ast.FormattedValue):
            pass

        elif isinstance(e, ast.JoinedStr):
            pass

        elif isinstance(e, ast.Constant):
            return Constant(value=e.value)

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
                # typer = Typer()
                # try:
                #     funcType = typer.get_type(e.id)
                #     return funcType
                # except KeyError:
                #     raise Exception(f"Unbound var {e.id}")
                raise Exception(f"Unbound var {e.id}")

        elif isinstance(e, ast.List):
            return List()

        elif isinstance(e, ast.Tuple):
            return Tuple()

        else:
            raise Exception(f"{e.lineno}: Unsupported syntax")

    # helper
    @staticmethod
    def _unify(a, b):
        # Type Seeker will seek str type
        if str(a) == str(b):
            return

        if isinstance(a, TypeVar):
            a.instance = b

        elif isinstance(b, TypeVar):
            b.instance = a

        elif isinstance(a, Function) and isinstance(b, Function):
            if len(a.from_type) != len(b.from_type):
                raise Exception("Function args not matched")
            for p, q in zip(a.from_type, b.from_type):
                Inferer._unify(p, q)
            Inferer._unify(a.to_type, b.to_type)

        else:
            raise Exception(f"Function args: {a} and {b} are not matched")

    @staticmethod
    def _get_func_name(func):
        # a.b.c()
        if isinstance(func, ast.Attribute):
            return f"{Inferer._get_func_name(func.value)}.{func.attr}"
        # a()
        elif isinstance(func, ast.Name):
            return func.id
        else:
            raise Exception("Cannot get function name")

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

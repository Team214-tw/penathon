import ast
import copy
from typing import Dict, List, Set, Tuple, Union, Callable, TypeVar, Any

from .Typer import Typer
from .CodeGenerator import CodeGenerator
from .Preprocessor import Preprocessor
from .SymTable import SymTable
from .SymTableEntry import *
from .Helper import Helper


class Inferer:
    def __init__(self):
        self.env = SymTable('root')
        self.seeker = Typer()
        self.preprocessor = Preprocessor()
        self.helper = Helper()
        self.visitReturn = False
        self.Return = None
        self.tvid = 0  # type variable id

    def infer(self, tree):
        # mtree = self.preprocessor.preprocess(tree)  # modified tree

        for i in tree.body:
            inferedType = self.infer_stmt(i)
            if isinstance(inferedType, TypeVar):
                print(i.lineno, f"{inferedType} => {inferedType.__bound__}")
            else:
                print(i.lineno, inferedType)

        return self.env

    def infer_stmt(self, e):
        if isinstance(e, ast.FunctionDef):
            newSymTable = SymTable(e.name, self.env)
            self.env = newSymTable

            # create type variables for each argument
            argList = list()
            for i in e.args.args:
                argName = i.arg
                argTypeVar = self.helper.create_type_var()
                self.env.write(argName, AssignSymbol(argName, argTypeVar))
                argList.append(argTypeVar)

            # infer body type
            infBodyType = []
            for i in e.body:
                potentialType = self.infer_stmt(i)
                if self.visitReturn:
                    infBodyType.append(self.Return)
                    self.visitReturn = False

            # generate body type
            if len(infBodyType) == 0:
                bodyType = None
            else:
                bodyType = Union[tuple(infBodyType)]
            inferredType = Callable[argList, bodyType]

            # context switch back
            self.env = self.env.parent
            self.env.add(e, inferredType)

            return inferredType

        elif isinstance(e, ast.AsyncFunctionDef):
            pass

        elif isinstance(e, ast.ClassDef):
            newSymTable = SymTable(self.env)
            self.env = newSymTable
            for i in e.body:
                potentialType = self.infer_stmt(i)
            classType = ClassDefSymbol(e.name, self.env)
            self.env.parent.add(e, classType)
            self.env = self.env.parent
            return classType

        elif isinstance(e, ast.Return):
            if self.visitReturn:
                self.Return = Union[(self.Return, self.infer_expr(e.value))]
            else:
                self.Return = self.Return, self.infer_expr(e.value)
                self.visitReturn = True
                self.Return = self.infer_expr(e.value)
            return self.infer_expr(e.value)

        elif isinstance(e, ast.Delete):
            pass

        elif isinstance(e, ast.Assign):
            valueType = self.infer_expr(e.value)
            self.env.add(e, valueType)
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
            infBodyType = []
            self.infer_expr(e.test)
            for i in e.body:
                potentialType = self.infer_stmt(i)

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
            for i in e.orelse:
                potentialType = self.infer_stmt(i)

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
            self.env.add(e)

        elif isinstance(e, ast.ImportFrom):
            self.env.add(e)

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

            if self.helper.can_coerce(leftType, rightType):
                leftType = rightType

            funcName = self.helper.reveal_magic_func(e.op)
            try:
                leftOriType = self.helper.reveal_original_type(leftType).__name__.lower()
                funcType = self.seeker.get_type(f"{leftOriType}.{funcName}")
            except KeyError:
                raise Exception(f"{leftType} object has no method {funcName}")

            argList = [rightType]
            resultType = self.helper.create_type_var()
            self._unify_callable(Callable[argList, resultType], funcType)

            return self.helper.reveal_real_type(resultType)

        elif isinstance(e, ast.UnaryOp):
            pass

        elif isinstance(e, ast.Lambda):
            newSymTable = SymTable(None, self.env)
            self.env = newSymTable

            # create type variables for each argument
            argList = list()
            for i in e.args.args:
                argName = i.arg
                argTypeVar = self.helper.create_type_var()
                self.env.write(argName, AssignSymbol(argName, argTypeVar))
                argList.append(argTypeVar)

            # infer body type
            bodyType = self.infer_expr(e.body)
            inferredType = Callable[argList, bodyType]

            # context switch back
            self.env = self.env.parent

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
            funcName = self.helper.reveal_real_func_name(e.func)

            # built-in function call
            if funcName == 'list':
                return self.infer_expr(ast.List(elts=e.args))
            elif funcName == 'set':
                return self.infer_expr(ast.Set(elts=e.args))
            elif funcName == 'tuple':
                return self.infer_expr(ast.Tuple(elts=e.args))
            elif funcName == 'dict':
                return Dict  # TODO

            funcType = self.env.typeof(funcName)
            funcType = self.helper.reveal_real_type(funcType)
            if not self.helper.is_callable(funcType):
                return None

            # infer call type
            argList = list()
            for i in e.args:
                argType = self.infer_expr(i)
                argList.append(argType)
            resultTypeVar = self.helper.create_type_var()

            # infer def type and result type
            self._unify_callable(Callable[argList, resultTypeVar], funcType)

            return self.helper.reveal_real_type(resultTypeVar)

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
            return self.env.typeof(e.id)

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
    def _unify_callable(self, a, b):
        if not isinstance(a, Callable):
            raise Exception(f"Expect unify type of Callable, but {type(a)} is received")

        if not isinstance(b, Callable):
            raise Exception(f"Expect unify type of Callable, but {type(b)} is received")

        a_args_type = list(a.__args__[:-1])
        a_return_type = a.__args__[-1]
        b_args_type = list(b.__args__[:-1])
        b_return_type = b.__args__[-1]

        if len(a_args_type) != len(b_args_type):
            raise Exception("Function args not matched")

        for i, (p, q) in enumerate(zip(a_args_type, b_args_type)):
            a_args_type[i], b_args_type[i] = self._unify(p, q)
        a_return_type, b_return_type = self._unify(a_return_type, b_return_type)

        a.__args__ = (*a_args_type, a_return_type)
        b.__args__ = (*b_args_type, b_return_type)

    def _unify(self, a, b):
        # built-in type equivalent
        if a == b:
            return a, b

        elif self.helper.can_coerce(a, b):
            return b, b

        elif self.helper.can_coerce(b, a):
            return a, a

        # a, b are both TypeVar, unify each bound type
        elif isinstance(a, TypeVar) and isinstance(b, TypeVar):
            ab = [a.__bound__] if a.__bound__ is not None else []
            ab = [*ab, b.__bound__] if b.__bound__ is not None else [*ab]
            if len(ab) > 0:
                self.helper.bound_type_var(a, Union[tuple(ab)])
                self.helper.bound_type_var(b, Union[tuple(ab)])
            return a, b

        # only a is TypeVar, set upper_bound of a to Union[b, a.__bound__]
        elif isinstance(a, TypeVar):
            ab = [b, a.__bound__] if a.__bound__ is not None else [b]
            self.helper.bound_type_var(a, Union[tuple(ab)])
            return a, b

        # only b is TypeVar, set upper_bound of a to Union[a, b.__bound__]
        elif isinstance(b, TypeVar):
            ab = [a, b.__bound__] if b.__bound__ is not None else [a]
            self.helper.bound_type_var(b, Union[tuple(ab)])
            return a, b

        # typing type equivalent
        elif hasattr(a, '_name') and hasattr(b, '_name') and a._name == b._name:
            return a, b

        else:
            raise Exception(f"Function args: {a} and {b} are not matched")

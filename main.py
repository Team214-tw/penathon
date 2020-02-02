import ast
import copy
import uuid
import astor
from argparse import ArgumentParser
from dataclasses import dataclass, field
from typing import Literal, Dict, Any, Union
from Typer import Typer
from base import Function, TypeVariable


class Context:
    env = dict()


def unify(a, b):
    if a == b:
        return

    if isinstance(a, TypeVariable):
        a.instance = b

    elif isinstance(b, TypeVariable):
        b.instance = a

    elif isinstance(a, Function) and isinstance(b, Function):
        if len(a.from_type) != len(b.from_type):
            raise Exception("Function args not matched")
        for p, q in zip(a.from_type, b.from_type):
            unify(p, q)
        unify(a.to_type, b.to_type)
    else:
        raise Exception("Function args not matched")


def get_magic(op):
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


def get_func_name(ctx, func):
    if 'attr' in dir(func):
        return f"{get_func_name(ctx, func.value)}.{func.attr}"
    elif isinstance(func, ast.Name):
        return func.id
    else:
        return type(func).__name__.lower()


def infer(ctx, e):
    # if isinstance(e, type):
    #     return e

    if isinstance(e, ast.Name):
        if e.id in ctx.env:
            return ctx.env[e.id]
        else:
            raise Exception(f"Unbound var {e.id}")
            # typer = Typer()
            # try:
            #     funcType = typer.get_type(e.id)
            #     return funcType
            # except KeyError:
            #     raise Exception(f"Unbound var {e.id}")

    # Base Case
    elif isinstance(e, ast.List):
        return 'list'  # undone

    elif isinstance(e, ast.Dict):
        return 'dict'  # undone

    elif isinstance(e, ast.Set):
        return 'set'  # undone

    elif isinstance(e, ast.Tuple):
        return 'tuple'  # undone

    elif isinstance(e, ast.Attribute):
        return 'attribute'  # undone

    elif isinstance(e, ast.Constant):
        return type(e.value).__name__  # undone

    # Top-level
    elif isinstance(e, ast.Expr):
        return infer(ctx, e.value)

    elif isinstance(e, ast.Assign):
        valueType = infer(ctx, e.value)
        for t in e.targets:
            ctx.env[t.id] = valueType
        return valueType

    elif isinstance(e, ast.FunctionDef):
        newCtx = copy.deepcopy(ctx)

        # create type variables for each argument
        argList = list()
        for i in e.args.args:
            argName = i.arg
            argTypeVar = TypeVariable()
            newCtx.env[argName] = argTypeVar
            argList.append(argTypeVar)

        # infer
        bodyType = infer(newCtx, e.body)
        inferredType = Function(from_type=argList, to_type=bodyType)
        ctx.env[e.name] = inferredType  # undone

        # generate type informations
        for i, argTypeVar in enumerate(argList):
            if isinstance(argTypeVar.instance, str):  # undone
                e.args.args[i].annotation = ast.Name(argTypeVar.instance)
        if isinstance(bodyType, str):  # undone
            e.returns = ast.Name(bodyType)

        return inferredType

    elif isinstance(e, ast.Import):
        for i in e.names:
            asname = i.asname or i.name
            ctx.env[asname] = i.name  # undone typeseeker?

    elif isinstance(e, ast.ImportFrom):
        for i in e.names:
            asname = i.asname or i.name
            ctx.env[asname] = f"{e.module}.{i.name}"  # undone typeseeker?

    elif isinstance(e, ast.Return):
        return infer(ctx, e.value)

    # Expression
    elif isinstance(e, ast.Lambda):
        newCtx = copy.deepcopy(ctx)

        argList = list()
        for i in e.args.args:
            argName = i.arg
            argTypeVar = TypeVariable()
            newCtx.env[argName] = argTypeVar
            argList.append(argTypeVar)

        bodyType = infer(newCtx, e.body)
        inferredType = Function(argList, bodyType)
        return inferredType

    elif isinstance(e, ast.Call):
        func_name = get_func_name(ctx, e.func)
        funcType = infer(ctx, ast.Name(func_name))
        argList = list()
        for i in e.args:
            argType = infer(ctx, i)
            argList.append(argType)
        resultType = TypeVariable()
        unify(Function(argList, resultType), funcType)
        return resultType

    # elif isinstance(e, ast.BinOp):
    #     left_type = infer(ctx, e.left)
    #     right_type = infer(ctx, e.right)
    #     func_name = get_magic(e.op)
    #     typer = Typer()
    #     try:
    #         funcType = typer.get_type(f"{left_type}.{func_name}")
    #     except KeyError:
    #         raise Exception(f"{left_type} object has no method {func_name}")

    #     argList = (right_type,)
    #     resultType = TypeVariable()
    #     unify(Function(argList, resultType), funcType)
    #     if resultType.instance:
    #         return resultType.instance
    #     else:
    #         return resultType

    # elif isinstance(e, ast.BoolOp):
    #     left_type = infer(ctx, e.values[0])
    #     right_type = infer(ctx, e.values[1])
    #     func_name = get_magic(e.op)
    #     typer = Typer()
    #     try:
    #         funcType = typer.get_type(f"{left_type}.{func_name}")
    #     except KeyError:
    #         raise Exception(f"{left_type} object has no method {func_name}")

    #     argList = (right_type,)
    #     resultType = TypeVariable()
    #     print(Function(argList, resultType), funcType)
    #     unify(Function(argList, resultType), funcType)
    #     if resultType.instance:
    #         return resultType.instance
    #     else:
    #         return resultType

    # Union type
    elif isinstance(e, list):  # undone
        return infer(ctx, e[0].value)

    else:
        pass


def main():
    parser = ArgumentParser()
    parser.add_argument("input", help="input file")
    args = parser.parse_args()
    input_file = args.input
    with open(input_file) as f:
        x = ast.parse(f.read())

    ctx = Context()
    for i in x.body:
        print(i.lineno, infer(ctx, i))
    print(astor.to_source(x), end="")


if __name__ == "__main__":
    main()

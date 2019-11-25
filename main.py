import ast
import copy
import uuid
from argparse import ArgumentParser
from dataclasses import dataclass, field
from typing import Literal, Dict, Any, Union
from Typer import Typer
from base import Function


class Context:
    env = dict()
    #  class_methods = dict()
    class_methods = {
        float: {
            '__add__': Function((float,), float),
            '__sub__': Function((float,), float),
            '__mult__': Function((float,), float),
            '__div__': Function((float,), float),
            '__mod__': Function((float,), float),
        },
        int: {
            '__add__': Function((int,), int),
            '__sub__': Function((int,), int),
            '__mult__': Function((int,), int),
            '__div__': Function((int,), int),
            '__mod__': Function((int,), int),
            '__eq__': Function((int,), int),
        },
    }


class TypeVariable:
    def __init__(self):
        self.id = uuid.uuid4()
        self.instance = None

    def __str__(self):
        if self.instance:
            return f"{str(self.instance)}"
        else:
            return f"T{str(self.id).split('-')[0]}"


def unify(a, b):
    if a == b:
        return

    if isinstance(a, TypeVariable):
        if a != b:
            a.instance = b

    elif isinstance(b, TypeVariable):
        if a != b:
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
    }
    return magics[type(op).__name__]


def infer(ctx, e):
    if isinstance(e, type):
        return e

    elif isinstance(e, ast.Constant):
        return type(e.value).__name__

    elif isinstance(e, ast.BinOp):
        left_type = infer(ctx, e.left)
        right_type = infer(ctx, e.right)
        func_name = get_magic(e.op)
        typer = Typer()
        funcType = typer.get_type(f"builtins.{left_type}.{func_name}")
        argList = (right_type,)
        resultType = TypeVariable()
        unify(Function(argList, resultType), funcType)
        if resultType.instance:
            return resultType.instance
        else:
            return resultType

    elif isinstance(e, ast.Name):
        if e.id in ctx.env:
            return ctx.env[e.id]
        else:
            raise Exception(f"Unbound var {e.id}")

    elif isinstance(e, ast.FunctionDef):
        newCtx = copy.deepcopy(ctx)
        argList = list()
        for i in e.args.args:
            argName = i.arg
            argType = TypeVariable()
            newCtx.env[argName] = argType
            argList.append(argType)

        bodyType = infer(newCtx, e.body)
        inferredType = Function(argList, bodyType)
        ctx.env[e.name] = inferredType
        return inferredType

    elif isinstance(e, list):
        for i in e:
            if isinstance(i, ast.Return):
                return infer(ctx, i.value)
            else:
                infer(ctx, i)

    elif isinstance(e, ast.Lambda):
        newCtx = copy.deepcopy(ctx)
        argList = list()
        for i in e.args.args:
            argName = i.arg
            argType = TypeVariable()
            newCtx.env[argName] = argType
            argList.append(argType)

        bodyType = infer(newCtx, e.body)
        inferredType = Function(argList, bodyType)
        return inferredType

    elif isinstance(e, ast.Call):
        funcType = infer(ctx, e.func)
        argType = infer(ctx, e.args[0])
        argList = list()
        for i in e.args:
            argType = infer(ctx, i)
            argList.append(argType)
        resultType = TypeVariable()
        unify(Function(argList, resultType), funcType)
        return resultType

    elif isinstance(e, ast.Assign):
        ctx.env[e.targets[0].id] = infer(ctx, e.value)
        return ctx.env[e.targets[0].id]

    elif isinstance(e, ast.Expr):
        return infer(ctx, e.value)


def main():
    parser = ArgumentParser()
    parser.add_argument("input", help="input file")
    args = parser.parse_args()
    input_file = args.input
    with open(input_file) as f:
        x = ast.parse(f.read())

    ctx = Context()
    for i in x.body:
        if isinstance(i, ast.Assign):
            print(i.lineno, infer(ctx, i))
        else:
            print(i.lineno, infer(ctx, i))


if __name__ == "__main__":
    main()

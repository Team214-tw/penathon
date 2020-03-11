import ast
import copy
import astor
import typing
from argparse import ArgumentParser
from inferer import Inferer


def main():
    parser = ArgumentParser()
    parser.add_argument("input", help="input file")
    args = parser.parse_args()
    input_file = args.input
    with open(input_file) as f:
        x = ast.parse(f.read())

    inferer = Inferer()
    for i in x.body:
        inferedType = inferer.infer_stmt(i)
        if isinstance(inferedType, typing.TypeVar):
            print(i.lineno, f"{inferedType} => {inferedType.__bound__}")
        else:
            print(i.lineno, inferedType)
    # print(astor.to_source(x), end="")


if __name__ == "__main__":
    main()

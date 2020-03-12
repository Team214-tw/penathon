import ast
import copy
import astor
import typing
from argparse import ArgumentParser
from inferer import Inferer
from preprocessor import assign_convert


def main():
    parser = ArgumentParser()
    parser.add_argument("input", help="input file")
    args = parser.parse_args()
    input_file = args.input
    with open(input_file) as f:
        x = ast.parse(f.read())

    inferer = Inferer()
    x.body = assign_convert(x.body)
    result = copy.deepcopy(x)
    result.body = list()
    for i in x.body:
        tmp, inferredType = inferer.infer_stmt(i)
        result.body.append(tmp)
        if isinstance(inferredType, typing.TypeVar):
            print(i.lineno, f'{inferredType} -> {inferredType.__bound__}')
        else:
            print(i.lineno, inferredType)
    print("--------------")
    print(astor.to_source(result), end="")


if __name__ == "__main__":
    main()

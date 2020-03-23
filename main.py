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
    tree_with_type = inferer.infer(x)
    print(astor.to_source(tree_with_type), end='')


if __name__ == "__main__":
    main()

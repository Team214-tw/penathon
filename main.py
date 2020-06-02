import ast
import copy
import astor
import typing
from argparse import ArgumentParser
from penathon.Inferer import Inferer
from penathon.CodeGenerator import CodeGenerator


def main():
    parser = ArgumentParser()
    parser.add_argument("input", help="input file")
    args = parser.parse_args()
    input_file = args.input
    with open(input_file) as f:
        x = ast.parse(f.read())

    inferer = Inferer()
    cg = CodeGenerator()
    symbol_table = inferer.infer(x)
    symbol_table.print()
    tree_with_type = cg.gen(x, symbol_table)
    # print('-----')
    print(astor.to_source(tree_with_type), end='')


if __name__ == "__main__":
    main()

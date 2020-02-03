import ast


class Inferer:
    def __init__(self):
        env = dict()

    def infer_stmt(self, e):
        if isinstance(e, ast.FunctionDef):
            pass

        elif isinstance(e, ast.AsyncFunctionDef):
            pass

        elif isinstance(e, ast.ClassDef):
            pass

        elif isinstance(e, ast.Return):
            pass

        elif isinstance(e, ast.Delete):
            pass

        elif isinstance(e, ast.Assign):
            pass

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
            pass

        elif isinstance(e, ast.ImportFrom):
            pass

        elif isinstance(e, ast.Global):
            pass

        elif isinstance(e, ast.Nonlocal):
            pass

        elif isinstance(e, ast.Expr):
            pass

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
            pass

        elif isinstance(e, ast.UnaryOp):
            pass

        elif isinstance(e, ast.Lambda):
            pass

        elif isinstance(e, ast.IfExp):
            pass

        elif isinstance(e, ast.Dict):
            pass

        elif isinstance(e, ast.Set):
            pass

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
            pass

        elif isinstance(e, ast.FormattedValue):
            pass

        elif isinstance(e, ast.JoinedStr):
            pass

        elif isinstance(e, ast.Constant):
            pass

        elif isinstance(e, ast.Attribute):
            pass

        elif isinstance(e, ast.Subscript):
            pass

        elif isinstance(e, ast.Starred):
            pass

        elif isinstance(e, ast.Name):
            pass

        elif isinstance(e, ast.List):
            pass

        elif isinstance(e, ast.Tuple):
            pass

        else:
            raise Exception(f"{e.lineno}: Unsupported syntax")

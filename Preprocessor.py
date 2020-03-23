import ast


class Preprocessor(ast.NodeTransformer):
    def visit_Assign(self, node):
        return [
            ast.AnnAssign(
                target=t,
                value=node.value,
                annotation=None,  # type will be determined by Inferer
                lineno=node.lineno,
                simple=1,
            )
            for t in node.targets
        ]

    def preprocess(self, tree):
        return self.visit(tree)

import ast


def assign_convert(body):
    new_body = list()
    lineno_adj = 0
    for i in body:
        if isinstance(i, ast.Assign):
            lineno_adj -= 1
            for j in i.targets:
                lineno_adj += 1
                new_body.append(
                    ast.Assign(targets=[j], value=i.value, lineno=i.lineno + lineno_adj)
                )
        else:
            new_body.append(i)
    return new_body


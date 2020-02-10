def foo_with_multiple_body(a):
    a = 1
    if True:
        return 2.5
    else:
        return [True, 2.5]
    return a

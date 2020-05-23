def a(aa):
    def b(c):
        if True:
            return True
        else:
            return 3
        return c
    b(1.0)
    return b(aa)
a(3)
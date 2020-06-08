class foo:
    a = 4
    def __init__(self):
        return None


class bar:
    def __init__(self):
        self.c = 1

    def num(self):
        return self.c

    def inc(self, a):
        return 1

a = foo()
b = bar()
c = b.num()

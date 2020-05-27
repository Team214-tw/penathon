def b():
    return a()

def a():
    return 1

b()

class A():
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def B(self):
        return self.c

a = A(1, 2, True)
c = a.B()
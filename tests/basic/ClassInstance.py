class A():
    pass

a = A()
a.b = 1
c = a.b

b = A()
d = b.b # should not get b
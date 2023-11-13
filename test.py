class A():
    def __init__(self):
        self.a = 'abc'
        self.b = 'def'

    def getA():
        return self.a

    def getB():
        return self.b

    def auth(self):
        print("a: ", self.getA())
        print("b: ", self.getB())

clas = A()
clas.auth()


class A():

    a: str

    def __init__(self, a):
            self.a = a
            print(a)
    def __init__(self, _A: A):
            self.a = A.a
            print("copy constructor: a=%s" %self.a)

if __name__ == "__main__":
    x = A("foo")
    y = A(x)




from cogs import task, argument
from cogs.log import log, fail

@task
def Factorial(n):
    """calculate n!

    This task calculates the value of the factorial of the given
    positive number `n`.  Factorial of n, also known as n!, is
    defined by the formula:

        n! = 1*2*...*(n-1)*n
    """
    try:
        n = int(n)
    except ValueError:
        raise fail("n must be an integer")
    if n < 1:
        raise fail("n must be positive")
    f = 1
    for k in range(2, n+1):
        f *= k
    log("{}! = `{}`", n, f)

@task
class Fibonacci:
    """calculate the n-th Fibonacci number

    The n-th Fibonacci number `F_n` is defined by:

        F_0 = 0
        F_1 = 1
        F_n = F_{n-1}+F_{n-2} (n>1)
    """

    n = argument(int)

    def __init__(self, n):
        if n < 0:
            raise ValueError("n must be non-negative")
        self.n = n

    def __call__(self):
        p, q = 0, 1
        for k in range(self.n):
            p, q = p+q, p
        log("F_{} = `{}`", self.n, p)


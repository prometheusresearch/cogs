
from cogs import task
import os

@task
def Hello(name=None):
    """greet someone (if not specified, the current user)"""
    if name is None:
        # `os.getlogin()` does not work when the script is not started
        # by a login shell.
        # name = os.getlogin()
        name = os.environ['USER']
    print "Hello, %s!" % name.capitalize()


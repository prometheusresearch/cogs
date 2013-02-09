
from cogs import env, task, setting
import os

@setting
def Default_Name(name=None):
    """the name to use for greetings (if not set: login name)"""
    if name is None or name == '':
        name = os.getlogin()
    if not isinstance(name, str):
        raise ValueError("a string value is expected")
    env.add(default_name=name)

@task
def Hello_With_Configuration(name=None):
    if name is None:
        name = env.default_name
    print "Hello, %s!" % name.capitalize()


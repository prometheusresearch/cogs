
from cogs import task, argument, option
import sys, os

@task
class Write_Hello:

    name = argument(default=None)
    output = option(key='o', default=None)

    def __init__(self, name, output):
        if name is None:
            name = os.environ['USER']
        self.name = name
        if output is None:
            self.file = sys.stdout
        else:
            self.file = open(output, 'w')

    def __call__(self):
        self.file.write("Hello, %s!\n" % self.name.capitalize())



from setuptools import setup

setup(
    name='Cogs-Hello',
    version='0.1',
    description="""A Cogs task to greet somebody""",
    packages=['cogs'],
    namespace_packages=['cogs'],
    package_dir={'': 'src'},
    install_requires=['Cogs'],
    entry_points={ 'cogs.extensions': ['Hello = cogs.hello'] },
)


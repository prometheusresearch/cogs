#
# Copyright (c) 2012, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from setuptools import setup, find_packages


NAME = "DDT"
VERSION = "0.1.1" # FIXME: synchronize with `ddt.__version__`?
DESCRIPTION = """Development, Deployment and Testing automation toolkit"""
LONG_DESCRIPTION = open('README', 'r').read()
AUTHOR = """Kirill Simonov (Prometheus Research, LLC)"""
LICENSE = "MIT"
PACKAGES = find_packages()
PACKAGE_DIR = {'': 'src'}
INSTALL_REQUIRES = ['setuptools', 'PyYAML']
ENTRY_POINTS = {
    'console_scripts': [
        'ddt = ddt.run:run',
    ],
    'ddt.extensions': [],
}


setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      author=AUTHOR,
      license=LICENSE,
      packages=PACKAGES,
      package_dir=PACKAGE_DIR,
      install_requires=INSTALL_REQUIRES,
      entry_points=ENTRY_POINTS)



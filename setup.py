#
# Copyright (c) 2012, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from setuptools import setup, find_packages


NAME = "Cogs"
VERSION = "0.1.2"
DESCRIPTION = """A toolkit for developing command-line utilities in Python"""
LONG_DESCRIPTION = open('README', 'r').read()
AUTHOR = """Kirill Simonov (Prometheus Research, LLC)"""
AUTHOR_EMAIL = "xi@resolvent.net"
LICENSE = "MIT"
CLASSIFIERS = [
    "Development Status :: 2 - Pre-Alpha",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Intended Audience :: System Administrators",
    "License :: OSI Approved :: MIT License",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 2 :: Only",
    "Topic :: Utilities",
]
PACKAGES = find_packages('src')
PACKAGE_DIR = {'': 'src'}
INSTALL_REQUIRES = ['setuptools', 'PyYAML']
ENTRY_POINTS = {
    'console_scripts': [
        'cogs = cogs:run',
    ],
    'cogs.extensions': [],
}


setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      author=AUTHOR,
      license=LICENSE,
      classifiers=CLASSIFIERS,
      packages=PACKAGES,
      package_dir=PACKAGE_DIR,
      install_requires=INSTALL_REQUIRES,
      entry_points=ENTRY_POINTS)



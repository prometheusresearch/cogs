#
# Copyright (c) 2013, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from setuptools import setup, find_packages


NAME = "Cogs"
VERSION = "0.1.3"
DESCRIPTION = """Toolkit for developing command-line utilities in Python"""
LONG_DESCRIPTION = open('README', 'r').read()
AUTHOR = """Kirill Simonov (Prometheus Research, LLC)"""
AUTHOR_EMAIL = "xi@resolvent.net"
LICENSE = "MIT"
CLASSIFIERS = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Intended Audience :: System Administrators",
    "License :: OSI Approved :: MIT License",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 3",
    "Topic :: Utilities",
]
PACKAGES = find_packages('src')
PACKAGE_DIR = {'': 'src'}
INSTALL_REQUIRES = ['setuptools', 'PyYAML']
ENTRY_POINTS = {
    'console_scripts': [
        'cogs = cogs.run:main',
    ],
    'cogs.extensions': [],
}
USE_2TO3 = True


setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      author=AUTHOR,
      license=LICENSE,
      classifiers=CLASSIFIERS,
      packages=PACKAGES,
      package_dir=PACKAGE_DIR,
      install_requires=INSTALL_REQUIRES,
      entry_points=ENTRY_POINTS,
      use_2to3=USE_2TO3)



#
# Copyright (c) 2013, Prometheus Research, LLC
# Released under MIT license, see `LICENSE` for details.
#


from setuptools import setup, find_packages


NAME = "Cogs"
VERSION = "0.4.2"
DESCRIPTION = """Toolkit for developing command-line utilities in Python"""
LONG_DESCRIPTION = open('README', 'r').read()
AUTHOR = """Kirill Simonov (Prometheus Research, LLC)"""
AUTHOR_EMAIL = "xi@resolvent.net"
LICENSE = "MIT"
URL = "http://bitbucket.org/prometheus/cogs"
DOWNLOAD_URL = "http://pypi.python.org/pypi/Cogs"
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
NAMESPACE_PACKAGES = ['cogs']
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
      author_email=AUTHOR_EMAIL,
      license=LICENSE,
      url=URL,
      download_url=DOWNLOAD_URL,
      classifiers=CLASSIFIERS,
      packages=PACKAGES,
      package_dir=PACKAGE_DIR,
      namespace_packages=NAMESPACE_PACKAGES,
      install_requires=INSTALL_REQUIRES,
      entry_points=ENTRY_POINTS,
      use_2to3=USE_2TO3)



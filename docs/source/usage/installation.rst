

Installation
==============


To install from PyPI run::

  pip install pyprotolinc

Alternatively, or for delevoplement clone (or download) the repository from https://github.com/mseehafer/PyProtolinc.git and
run::

  pip install -e .

from the root directory of the repository.


To build the docs locally cd into the *docs* subdirectory and run::

  pip install -r requirements.txt
  make html

On windows I needed to install *pandoc* and this worked using the conda package manager.

Building a distribution locally works via::

  python -m build
  twine upload dist/*

if *build* and *twine* are also installed.

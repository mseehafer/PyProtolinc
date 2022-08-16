

Installation
==============


To install from PyPI run::

  pip install pyprotolinc


Install for Development
--------------------------

Alternatively, or for delevoplement clone (or download) the repository from https://github.com/mseehafer/PyProtolinc.git and
run::

  pip install -e .

from the root directory of the repository.

Building the Documentation
----------------------------

To build the docs locally *cd* into the *docs* subdirectory and run::

  pip install -r requirements.txt
  make html

On windows I needed to install *pandoc* as well and this worked using the conda package manager.

Tests
----------

Python test are configured and can be run by running ``pytest`` from the root directory.

Some tests of the C++ code using the `gtest <https://github.com/google/googletest>`_
are provided. To run those one needs to install ``cMake`` (e.g. from `here <https://cmake.org/download/>`_) 
and ``gtest``. On Windows I got ``gtest`` to run by first installing `vcpkg <https://vcpkg.io/en/index.html>`_  and then intsalling it via::
    
  vcpkg.exe install gtest:x64-windows

(when leaving the ``x64-windows`` out I got the x86 version installed at first). On Linux I was able to download ``gtest`` using conan (``pip install conan`` and then ``conan install gtest``) - I did
not manage to do that on Windows so that now the configurations are a bit different. To build and run the C++ tests proceed as follows::

   cd src\pyprotolinc\actuarial\c_src

When running for the first time configure the build as follows::
  
  cmake -B build -DCMAKE_TOOLCHAIN_FILE="D:\programming\vcpkg\scripts\buildsystems\vcpkg.cmake"

Then to build and run the tests::

    cmake --build build --target tests & build\tests\Debug\tests.exe



Uploading a new Version to PyPI
---------------------------------
Building a distribution locally works via::

  python -m build
  twine upload dist/*

if *build* and *twine* are also installed.

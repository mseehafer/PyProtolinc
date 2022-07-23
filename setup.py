import platform
from distutils.core import setup
from distutils.extension import Extension
from setuptools import find_packages

from Cython.Build import cythonize
import numpy


IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    extra_compile_args = ['/openmp']
    extra_link_args = ['/openmp']
else:
    extra_compile_args = ['-fopenmp', '-std=c++11', '-O3']
    extra_link_args = ['-fopenmp', '-std=c++11']


extensions = [
    Extension("pyprotolinc._actuarial",
              ["src/pyprotolinc/actuarial/valuation.pyx",
               "src/pyprotolinc/actuarial/c_src/c_valuation.cpp"],
              include_dirs=["src/pyprotolinc/actuarial/c_src",
                            numpy.get_include()],
              extra_compile_args=extra_compile_args,
              extra_link_args=extra_link_args
              )
]

setup(
    name='PyProtolinc',
    version='0.1.6',
    description='Projection Tool for Life Insurance Cash Flows',
    author='Martin Seehafer',
    keywords = 'actuarial, projection, life, insurance',
    license = 'MIT',
    url = 'https://github.com/mseehafer/PyProtolinc',
    zip_safe=False,
    include_package_data=True,
    package_data={"pyprotolinc.actuarial": ["src/pyprotolinc/actuarial/valuation.pyx"]},
    packages= find_packages(where = 'src'),
    package_dir = {'':'src'},
    python_requires = ">=3.6",
    ext_modules=cythonize(extensions),
    install_requires=[
        'numpy',
        'pandas',
        'xlrd',
        'cython',
        'pyyaml',
        'fire',
        'requests',
        'openpyxl',
    ],
    entry_points={
        'console_scripts': [
            'pyprotolinc=pyprotolinc.main:main',
            'protolinc=pyprotolinc.main:main']
    }
)

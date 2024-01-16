import platform
from distutils.core import setup
from distutils.extension import Extension
from setuptools import find_packages

from Cython.Build import cythonize
import numpy


# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.rst").read_text()


IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    extra_compile_args = ['/openmp', '/Ox']
    extra_link_args = []
else:
    extra_compile_args = ['-fopenmp', '-std=c++11', '-O3']
    extra_link_args = ['-fopenmp', '-std=c++11']


extensions = [
    Extension("pyprotolinc._actuarial",
              ["src/pyprotolinc/actuarial/valuation.pyx",
               ],
              include_dirs=["src/pyprotolinc/actuarial/c_src/modules",
                            numpy.get_include()],
              extra_compile_args=extra_compile_args,
              extra_link_args=extra_link_args
              )
]

setup(
    name='PyProtolinc',
    version='0.1.7',
    description='Projection Tool for Life Insurance Cash Flows',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author='Martin Seehafer',
    keywords='actuarial, projection, cash flows, life, insurance',
    license='MIT',
    url='https://github.com/mseehafer/PyProtolinc',
    zip_safe=False,
    include_package_data=True,
    package_data={"pyprotolinc.actuarial": [
        "src/pyprotolinc/actuarial/valuation.pyx",
        "src/pyprotolinc/actuarial/crisk_factors.pxd",
        "src/pyprotolinc/actuarial/providers.pxd",
        "src/pyprotolinc/actuarial/portfolio.pxd"]
        },
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires=">=3.9",
    ext_modules=cythonize(extensions, language_level=3),
    install_requires=[
        'numpy==1.23.1',
        'pandas',
        'xlrd',
        'cython>=3.0.5',
        'pyyaml',
        'fire',
        'requests',
        'openpyxl',
        'pytest',
    ],
    entry_points={
        'console_scripts': [
            'pyprotolinc=pyprotolinc.main:main',
            'protolinc=pyprotolinc.main:main']
    }
)

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import shutil

import sys
sys.path.insert(0, os.path.abspath('../../src'))
sys.path.append("breathe")


# Follow the link for a workaround that show how to include notebooks outside the
# toc tree directory
# https://github.com/spatialaudio/nbsphinx/issues/170

print("Copy example notebooks into docs/_examples")


def all_but_ipynb_and_png(dir, contents):
    result = []
    for c in contents:
        if os.path.isfile(os.path.join(dir, c)) and (not c.endswith(".ipynb")) and (not c.upper().endswith(".PNG")):
            result += [c]
    return result


project_root = os.path.abspath('../..')
# shutil.copyfile(os.path.join(project_root, "tests/notebooks/ModelBuilding.ipynb"),
#                 os.path.join(project_root, "docs/source/examples/ModelBuilding.ipynb"))
shutil.rmtree(os.path.join(project_root, "docs/source/examples/example_nbs"), ignore_errors=True)
shutil.copytree(os.path.join(project_root, "examples"),
                os.path.join(project_root, "docs/source/examples/example_nbs"),
                ignore=all_but_ipynb_and_png)

# -- Project information -----------------------------------------------------

project = 'PyProtolinc'
copyright = '2022, Martin Seehafer'
author = 'Martin Seehafer'

# The full version, including alpha/beta/rc tags
release = '0.0.1'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'nbsphinx',
    'sphinx_rtd_theme',
    'sphinx_gallery.load_style',
    'breathe'
]

# suppress_warnings = [
#     'nbsphinx',
# ]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"
# html_theme = 'alabaster'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']


# nbsphinx_execute = 'never'
# nbsphinx_kernel_name = 'python'

breathe_projects = {"PyProtolinc-Core": "../../src/pyprotolinc/actuarial/c_src/docs/xml/"}
breathe_default_project = "PyProtolinc-Core"

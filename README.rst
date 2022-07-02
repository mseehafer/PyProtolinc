
About Protolinc
=======================================================================

An Extensible Projection Tool for Life Insurance Cash Flows.
-------------------------------------------------------------
This package allows to project future cash flows for portfolios of life insurance 
policies. It comes with a number of built-in standard products but can also be used
to project custom products by the user. 


Documentation
^^^^^^^^^^^^^^^^

For extended documentation cf. https://protolinc.readthedocs.io/en/latest/index.html.


Project Objectives
----------------------

The key objective for *Protolinc* is to model cash flows for a variety of simple life and health insurance
products, also beyond stylized textbook examples.

The tool should provide a command line interface which can be used with configuration as well as an extensible
programming API which can be used to adapt to own purposes.

Calculations should be laid out to deal with portfolios of insureds in a batch style and an attempt shall be made
that forecast projections for reasonably large portfolios (of, say, a few 10s or 100s of thousands of policies)
can be made in an acceptable amount of time (seconds or up to a few minutes rather than hours).


Basic Usage
----------------

Installation
^^^^^^^^^^^^^^^^


To install from PyPI run::

  pip install protolinc

Clone (or download) the repository run::

  pip install -e .

from the root directory of the repository.

Quickstart
^^^^^^^^^^^^^^^^

Usage is illustrated in detail by the prepared use cases in the *examples* folder. To test those *cd* into the respective
subfolder and run the tool from the command line::

  protolinc run

This will pick up the configuration file (*config.yml*) in the working directory (which points to the portfolio file in the subdirectory
*portfolio*) and write the (aggregate) result of the computation into a
csv file in the subfolder *results*. To view these copy the Excel file *results_viewer_generic.xlsx* from the examples folder into the working folder and
rename it to *results_viewer_generic.xlsx* and import the data from the CSV file. Now one can start playing around by changing the configuration.



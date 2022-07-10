
About PyProtolinc
=======================================================================

An Actuarial Projection Tool for Life Insurance Cash Flows.
-------------------------------------------------------------
This package allows to project future cash flows for portfolios of life & health insurance 
policies. It comes with a number of built-in standard products but can also be used
to project custom products by the user. 


Documentation
^^^^^^^^^^^^^^^^

For extended documentation cf. https://pyprotolinc.readthedocs.io/en/latest/index.html.


Project Objectives
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The key objective for *PyProtolinc* is to model cash flows for a variety of simple life and health insurance
products, going forward also beyond stylized textbook examples.

The tool should provide a command line interface which can be used with configuration files as well as an extensible
programming API which provides flexibility to adapt to own purposes.

Calculations should be laid out to deal with portfolios of insureds in a batch style and an attempt shall be made
that forecast projections for reasonably large portfolios (of, say, a few 10s or 100s of thousands of policies)
can be made in an acceptable amount of time (seconds or up to a few minutes rather than hours).


Basic Usage
----------------

Installation
^^^^^^^^^^^^^^^^


To install from PyPI run::

  pip install -U pyprotolinc

Alternatively, or for delevoplement clone (or download) the repository from https://github.com/mseehafer/PyProtolinc.git and
run::

  pip install -e .

from the root directory of the repository.

Quickstart
^^^^^^^^^^^^^^^^

Usage is illustrated in detail by the prepared use cases in the *examples* folder. To try those out *cd* into the respective
subfolder and run the tool from the command line::

  pyprotolinc run

This will pick up the configuration file (*config.yml*) in the working directory (which points to the portfolio file
in the subdirectory *portfolio*) and initiate a projection run. Once completed the (aggregate) results of the computation
are written into a CSV file in the subfolder *results*. Now one can start playing around by changing the configuration.
Note that the examples are commented in the documentation, cf. https://pyprotolinc.readthedocs.io/en/latest/examples/intro.html .



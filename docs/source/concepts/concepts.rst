


Concepts
============


The core of the tool is a projection kernel which implements a generic (Markov) multi state evolution process.
Projections are based on one of the built-in (or a self-provided) *state models*, a set of compatible 
*state transition providers*, a *product definition*
and a *portfolio of insureds*.
Model runs can be specified in code or using *yaml* configuration files.


.. include:: state_models.rst

.. include:: portfolios.rst

.. include:: assumptions.rst

.. include:: products.rst

.. include:: config_and_run.rst

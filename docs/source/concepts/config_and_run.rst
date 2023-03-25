



Configuration and Runs
-------------------------

To start a run of ``pyprotolinc`` we have to combine various relevant information for the projection kernel
in a configuration object.



Configuration
^^^^^^^^^^^^^^^^^^^^^^^^

The main configuration object is ``pyprotolinc.RunConfig`` and its ``__init__`` method has the following signature::

    def __init__(self,
                 state_model_name: str,
                 working_directory: Path = ".",
                 model_name: str = "GenericMultiState",
                 years_to_simulate: int = 120,
                 steps_per_month: int = 1,
                 portfolio_path: Optional[str] = None,
                 assumptions_path: Optional[str] = None,
                 outfile: str = "ncf_out_generic.csv",
                 portfolio_cache: Optional[str] = None,
                 profile_out_dir: Optional[str] = None,
                 portfolio_chunk_size: int = 20000,
                 use_multicore: bool = False,
                 kernel_engine: str = "PY",
                 max_age: int = 120
                 ) -> None:


Most of the parameters have sensible defaults but one has to provide a ``state_model_name``. Besides that the following applies:

* if ``portfolio_path`` is not provided a portfolio must be injected into the runner directly
* if ``assumptions_path`` is not provided an ``AssumptionSetWrapper`` must be injected into the runner directly

A convenient way to create an ``RunConfig`` object is by reading it from a yaml file, e.g. like this::

    run_cfg2 = pyprotolinc.get_config_from_file("../config.yml")

The structure of the yaml file closely mimics the structur of the object with some additional grouping. This is a valid example::

    io:
    portfolio_cache: "portfolio/portfolio_cache"
    profile_out_dir: "."

    # kernel engine is "C" or "PY"
    kernel:
    engine: "C"  # "PY" / "C"
    max_age: 119

    model:
    # Type of Model to be run, currently only "GenericMultiState" is supported
    type: "GenericMultiState"
    
    # generic settings
    years_to_simulate: 119
    steps_per_month: 1
    use_multicore: true  # true / false

    run_type_specs:

      GenericMultiState:

        state_model: "DeferredAnnuityStates"
        assumptions_spec:  "di_assumptions.yml"
        outfile: "results/ncf_out_generic.csv"
        portfolio_path: "portfolio_small3.xlsx"
        portfolio_chunk_size: 8192


In this case the configuration object can be created as follows::

    run_cfg2 = pyprotolinc.get_config_from_file("../config.yml")


Runs
^^^^^^^^^^^^^^^^^^^^^^^^

Calculation runs can be triggered by two methods in the module ``pyprotolinc.main``: either ``project_cashflows`` or ``project_cashflows_cli``.

If using the latter all data must be delivered via the config file path or object. The former allows
to inject some objects programmatically. 

Here is an example: Assume that a portfolio file has been read into a *pandas.DataFrame* ``df`` and an *AssumptionSetWrapper* ``asw`` 
has been constructed. Then the following will trigger a run using these objects::

    project_cashflows(run_cfg, df, asw, export_to_file=False)

Alternatively, if a configuration file exists then::

    project_cashflows_cli(path_to_config)

will trigger a run using the specification in the configuration file. Alternatively a (complete) ``RunConfig`` object can be provided to either of the methods.

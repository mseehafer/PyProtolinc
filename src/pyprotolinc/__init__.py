
from typing import Optional
import os.path
from pathlib import Path
import yaml


# gloabl constants
MAX_AGE = 119


class RunConfig:
    """ The RunConfig object.

    :param str model_name: Name of the model to be used in the run.
    :param int years_to_simulate: Max. simulation period in years.
    :param int steps_per_month: Number of steps a month is divided into in the simulation.
    :param str state_model_name: The name of the the states set.
    :param str portfolio_path: Path to portfolio file
    :param str assumptions_path: Path to assumptions config file
    :param str outfile: Path of the results file.
    :param str portfolio_cache: Path to the caching directory for portfolios
    :param str profile_out_dir: Path where to store profiling output.
    :param int portfolio_chunk_size: Size of the chunks the portfolio is broken into.
    :param bool use_multicore: Flag to indicate if multiprocessing shall be used.
    :param str kernel_engine: Use 'PY' or 'C' to select the Python or C++ engine
    :param int max_age: Max. age that is used when projecting (only C++)
    """
    def __init__(self,
                 state_model_name: str,
                 working_directory: Path = Path("."),
                 model_name: str = "GenericMultiState",
                 years_to_simulate: int = 119,
                 steps_per_month: int = 1,
                 portfolio_path: Optional[str] = None,
                 assumptions_path: Optional[str] = None,
                 outfile: str = "ncf_out_generic.csv",
                 portfolio_cache: Optional[str] = None,
                 profile_out_dir: Optional[str] = None,
                 portfolio_chunk_size: int = 20000,
                 use_multicore: bool = False,
                 kernel_engine: str = "PY",
                 max_age: int = 119
                 ) -> None:
        self.working_directory = working_directory
        self.model_name = model_name
        self.years_to_simulate = years_to_simulate
        self.portfolio_path = portfolio_path
        self.assumptions_path = assumptions_path
        self.steps_per_month = steps_per_month
        self.state_model_name = state_model_name
        self.timestep_duration = 1.0 / (12.0 * steps_per_month)
        self.outfile = outfile
        self.portfolio_cache = portfolio_cache
        self.profile_out_dir = profile_out_dir
        self.portfolio_chunk_size = portfolio_chunk_size
        self.use_multicore = use_multicore
        self.kernel_engine = kernel_engine.upper()
        self.max_age = max_age

        # make sure that relative paths are interpreted relative to the working directory
        if portfolio_cache and not os.path.isabs(portfolio_cache):
            self.portfolio_cache = os.path.join(self.working_directory, portfolio_cache)

        if portfolio_path and not os.path.isabs(portfolio_path):
            self.portfolio_path = os.path.join(self.working_directory, portfolio_path)

        if profile_out_dir and not os.path.isabs(profile_out_dir):
            self.profile_out_dir = os.path.join(self.working_directory, profile_out_dir)

    def __repr__(self) -> str:
        return str(self.__dict__)


def get_config_from_file(config_file: str) -> RunConfig:
    """ Returns a ``RunConfig`` object from the file.

        :param str config_file: Path to the config file to be loaded.

        :return: Configration object.
        :rtype: RunConfig
    """

    # load config file data
    with open(config_file, 'r') as conf_file:
        config_raw = yaml.safe_load(conf_file)

        chosen_type = config_raw["model"]["type"]
        run_type_spec = config_raw["run_type_specs"][chosen_type]

    working_dir = Path(config_file).parent.absolute()

    return RunConfig(
        run_type_spec.get("state_model"),
        working_dir,
        config_raw["model"]["type"],
        config_raw["model"]["years_to_simulate"],
        config_raw["model"]["steps_per_month"],
        run_type_spec["portfolio_path"],
        run_type_spec["assumptions_spec"],
        run_type_spec["outfile"],
        config_raw["io"]["portfolio_cache"],
        config_raw["io"]["profile_out_dir"],
        run_type_spec["portfolio_chunk_size"],
        config_raw["model"]["use_multicore"],
        config_raw["kernel"]["engine"],
        config_raw["kernel"]["max_age"],
    )

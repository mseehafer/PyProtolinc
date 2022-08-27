
import yaml


# gloabl constants
MAX_AGE = 119


class RunConfig:
    """ The RunConfig object.

    :param str model_name: 
        Name of the model to be used in the run.
    years_to_simulate : int
        Max. simulation period in years.
    steps_per_month : int
        Number of steps a month is divided into in the simulation.
    state_model_name : str
        The name of the the states set.
    portfolio_path : str
        Path to portfolio file
    assumptions_path : str
        Path to assumptions config file
    outfile : str
        Path of the results file.
    portfolio_cache : str
        Path to the caching directory for portfolios
    profile_out_dir : str
        Path where to store profiling output.
    portfolio_chunk_size : str
        Size of the chunks the portfolio is broken into.
    use_multicore : bool
        Flag to indicate if multiprocessing shall be used.
    """
    def __init__(self,
                 model_name: str,
                 years_to_simulate: int,
                 steps_per_month: int,
                 state_model_name: str,
                 portfolio_path: str,
                 assumptions_path: str,
                 outfile: str,
                 portfolio_cache: str,
                 profile_out_dir: str,
                 portfolio_chunk_size: int,
                 use_multicore: bool
                 ):
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

    def __repr__(self):
        return str(self.__dict__)


def get_config_from_file(config_file: str):
    """ Return a ``RunConfig`` object from the file.

        :param str config_file: Path to the config file to be loaded.

        :return: Configration object.
        :rtype: RunConfig
    """

    # load config file data
    with open(config_file, 'r') as conf_file:
        config_raw = yaml.safe_load(conf_file)

        chosen_type = config_raw["model"]["type"]
        run_type_spec = config_raw["run_type_specs"][chosen_type]

    return RunConfig(
        config_raw["model"]["type"],
        config_raw["model"]["years_to_simulate"],
        config_raw["model"]["steps_per_month"],
        run_type_spec.get("state_model"),
        run_type_spec["portfolio_path"],
        run_type_spec["assumptions_spec"],
        run_type_spec["outfile"],
        config_raw["io"]["portfolio_cache"],
        config_raw["io"]["profile_out_dir"],
        run_type_spec["portfolio_chunk_size"],
        config_raw["model"]["use_multicore"]
    )


import os
import yaml

import protolinc.assumptions
import protolinc.models


# _DEFAULT_TABLES_PATH = os.path.abspath(os.path.join(protolinc.assumptions.__path__[0],
#                                                     "tables"))


# some constants
MAX_AGE = 119


class RunConfig:

    def __init__(self,
                 model_name,
                 years_to_simulate,
                 steps_per_month,
                 state_model_name,
                 portfolio_path,
                 assumptions_path,
                 outfile,
                 portfolio_cache,
                 profile_out_dir,
                 portfolio_chunk_size,
                 use_multicore
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


def get_config_from_file(config_file):
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

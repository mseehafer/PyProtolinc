""" Main entry point of the command line runner. """

import time
import logging
import cProfile
import pstats
import io
import os
from datetime import datetime
from multiprocessing import Pool, cpu_count

import gc

import numpy as np
import pandas as pd
import fire

from pyprotolinc import get_config_from_file
from pyprotolinc.portfolio import PortfolioLoader, Portfolio
from pyprotolinc.results import export_results
from pyprotolinc.runner import Projector
from pyprotolinc.models import ModelBuilder, _STATE_MODELS
from pyprotolinc.models.model_config import get_model_by_name
from pyprotolinc.assumptions.iohelpers import AssumptionsLoaderFromConfig
from pyprotolinc.models.model_multistate_generic import adjust_state_for_generic_model
from pyprotolinc.product import product_class_lookup
from pyprotolinc.utils import download_dav_tables


# logging.basicConfig(filename='runlog.txt', format='%(levelname)s - %(asctime)s - %(name)s - %(message)s', level=logging.DEBUG)
logging.basicConfig(format='%(levelname)s - %(asctime)s - %(name)s - %(message)s', level=logging.DEBUG)

# module level logger
logger = logging.getLogger(__name__)


def create_model(model_class, state_model_name, assumptions_file):

    loader = AssumptionsLoaderFromConfig(assumptions_file)

    state_model_class = None
    if model_class.STATES_MODEL is None:
        state_model_class = _STATE_MODELS[state_model_name]

    model_builder = ModelBuilder(model_class, state_model_class)

    loader.load(model_builder)
    model = model_builder.build()

    adjust_state_for_generic_model(model, state_model_name)

    return model


def project_cashflows(run_config, df_portfolio_overwrite=None, export_to_file=True):
    """ The main calculation rountine, can also be called as library function. If
        a dataframe is passed it will be used to build the portfolio object,
        otherwise the portfolio will be obtained from th run-config.

        :run_conig                 The run configuration object.
        :df_portfolio_overwrite    An optional dataframe that will be used instead
                                   of the configured portfolio if provided
        :export_to_file            Boolean flag to indicate if the results should be written
                                   to a file (as specified in the config object)
        
        Returns: Dictionary containing the result vectors.
    """
    t = time.time()

    logger.info("Multistate run with config: %s", str(run_config))

    rows_for_state_recorder = ()  # (0, 1, 2)
    num_timesteps = run_config.years_to_simulate * 12 * run_config.steps_per_month

    model = create_model(get_model_by_name(run_config.model_name), run_config.state_model_name, run_config.assumptions_path)

    if df_portfolio_overwrite is None:
        portfolio_loader = PortfolioLoader(run_config)
        portfolio = portfolio_loader.load(model.states_model)
    else:
        portfolio = Portfolio(None, model.states_model, df_portfolio_overwrite)

    # split into subportfolios
    subportfolios = portfolio.split_by_product_and_month_in_year(chunk_size=run_config.portfolio_chunk_size)

    # container for the results of the different sub-portfolios
    results_arrays = []

    # projections
    if run_config.use_multicore and len(subportfolios) > 1:

        num_processes = min(cpu_count(), len(subportfolios))

        PARAMS = [(run_config, model, num_timesteps, sub_ptf, rows_for_state_recorder, chunk_index+1, len(subportfolios))
                  for chunk_index, sub_ptf in enumerate(subportfolios)]
        logger.info("Executions in parallel wit %s processes and %s units", num_processes, len(PARAMS))
        pool = Pool(num_processes)

        for projector_results in pool.starmap(_project_subportfolio, PARAMS):
            results_arrays.append(projector_results)

    else:
        logger.info("Executions in single process for %s units", len(subportfolios))
        for sp_ind, sub_ptf in enumerate(subportfolios):

            logger.info("Projecting subportfolio {} / {}".format(1 + sp_ind, len(subportfolios)))
            projector_results = _project_subportfolio(run_config, model, num_timesteps, sub_ptf, rows_for_state_recorder, sp_ind + 1, len(subportfolios))
            results_arrays.append(projector_results)

            gc.collect()

    # here we would need to combine the results again
    logger.debug("Combining results from subportfolios")
    res_combined = dict(results_arrays[0])
    for res_ind in range(1, len(results_arrays)):
        res_set = results_arrays[res_ind]
        for key, val in res_set.items():
            if key not in ("YEAR", "QUARTER", "MONTH"):
                res_combined[key] = res_combined[key] + res_set[key]

    # export result
    if export_to_file:
        export_results(res_combined, run_config.outfile)

    elapsed = time.time() - t
    logger.info("Elapsed time %s seconds.", round(elapsed, 1))

    return res_combined


def _project_subportfolio(run_config, model, num_timesteps, portfolio, rows_for_state_recorder,
                          chunk_index, num_chunks):
    proj_state = model.new_state_instance(num_timesteps, portfolio, rows_for_state_recorder=rows_for_state_recorder)

    assert portfolio.homogenous_wrt_product, "Subportfolio should have identical portfolios in all rows"
    product_name = portfolio.products.iloc[0]
    product_class = product_class_lookup(product_name)
    assert model.states_model == product_class.STATES_MODEL, "State-Models must be consistent for the product and the run"
    product = product_class(portfolio)

    projector = Projector(run_config,
                          portfolio,
                          model,
                          proj_state,
                          product,
                          rows_for_state_recorder=rows_for_state_recorder,
                          chunk_index=chunk_index,
                          num_chunks=num_chunks)

    projector.run()
    return projector.get_results_dict()


def project_cashflows_cli(config_file='config.yml', multi_processing_overwrite=None):
    """ Perform a projection run. """
    run_config = get_config_from_file(config_file)
    if multi_processing_overwrite is not None:
        run_config.use_multicore = multi_processing_overwrite
    project_cashflows(run_config)


def profile(config_file='config.yml', multi_processing_overwrite=None):
    """ Run and and export a CSV file with runtime statistics.   """

    run_config = get_config_from_file(config_file)

    if multi_processing_overwrite is not None:
        run_config.use_multicore = multi_processing_overwrite

    pr = cProfile.Profile()

    # here we call the program
    pr.enable()
    project_cashflows(run_config)
    pr.disable()

    result = io.StringIO()
    pstats.Stats(pr, stream=result).print_stats()
    result = result.getvalue()
    # chop the string into a csv-like buffer
    result = 'ncalls' + result.split('ncalls')[-1]
    result = '\n'.join([','.join(line.rstrip().split(None, 5)) for line in result.split('\n')])
    df = pd.read_csv(io.StringIO(result))

    # filter for package  methods with positive runtime
    df_filtered = df[(df["filename:lineno(function)"].str.contains("pyprotolinc")) &
                     (df.cumtime > 0)].copy()

    # shorten the location by the common prefix
    start_pos = df_filtered["filename:lineno(function)"].str.find("pyprotolinc").unique()[0]
    df_filtered["filename:lineno(function)"] = df_filtered["filename:lineno(function)"].str.slice(start_pos)

    ct = datetime.now().strftime('%d-%m-%Y_%H_%M_%S')
    output_file = os.path.join(run_config.profile_out_dir, "profile_{}.xlsx".format(ct))

    df_filtered.index = np.arange(1, 1 + len(df_filtered))
    df_filtered.to_excel(output_file)
    logger.info("Statistics written to %s", output_file)


def main():
    fire.Fire({
        "run": project_cashflows_cli,
        "profile": profile,
        "download_dav_tables": download_dav_tables
    })


if __name__ == "__main__":
    project_cashflows_cli()
    # run_config = get_config_from_file(config_file='config.yml')
    # print(run_config)

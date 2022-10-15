
import time
import pandas as pd
import pyprotolinc._actuarial as actuarial
from pyprotolinc.models.model_disability_multistate import MultiStateDisabilityStates
from pyprotolinc.portfolio import Portfolio


def test_c_run():

    # construct assumption set
    provider05 = actuarial.ConstantRateProvider(0.5)
    provider02 = actuarial.ConstantRateProvider(0.2)
    acs = actuarial.AssumptionSet(2)
    acs.add_provider_const(0, 1, provider02)
    acs.add_provider_const(1, 0, provider05)

    # get a portfolio
    # py_portfolio = Portfolio("examples/03_mortality/portfolio/portfolio_small.xlsx", states_model=MortalityStates)
    py_portfolio = Portfolio("examples/04_two_state_disability/portfolio/portfolio_med.xlsx", states_model=MultiStateDisabilityStates)
    # py_portfolio = Portfolio("examples/04_two_state_disability/portfolio/portfolio_big.xlsx", states_model=MultiStateDisabilityStates)
    # py_portfolio = Portfolio("examples/04_two_state_disability/portfolio/portfolio_small.xlsx", states_model=MultiStateDisabilityStates)

    c_portfolio = actuarial.build_c_portfolio(py_portfolio)
    time_step = actuarial.TimeStep.MONTHLY  # actuarial.TimeStep.MONTHLY  # QUARTERLY   # TODO: test if we get back a result set with this timestep

    # not really a test but at least a check if it fails
    print("Start calc...")
    t = time.time()
    output_columns, result = actuarial.py_run_c_valuation(acs, c_portfolio, time_step)
    # do stuff
    elapsed = time.time() - t
    print("Done, time elapsed=", elapsed)

    print(output_columns)
    # print(result[:15, :])
    # print("ok")

    df = pd.DataFrame(data=result, columns=output_columns)
    df.to_excel("out.xlsx")


def test_c_run_with_config():

    # class RunConfig:
    #     """ The RunConfig object.

    #     :param str model_name: Name of the model to be used in the run.
    #     :param int years_to_simulate: Max. simulation period in years.
    #     :param int steps_per_month: Number of steps a month is divided into in the simulation.
    #     :param str state_model_name: The name of the the states set.
    #     :param str portfolio_path: Path to portfolio file
    #     :param str assumptions_path: Path to assumptions config file
    #     :param str outfile: Path of the results file.
    #     :param str portfolio_cache: Path to the caching directory for portfolios
    #     :param str profile_out_dir: Path where to store profiling output.
    #     :param int portfolio_chunk_size: Size of the chunks the portfolio is broken into.
    #     :param bool use_multicore: Flag to indicate if multiprocessing shall be used.
    #     """
    #     def __init__(self,
    #                 model_name: str,
    #                 years_to_simulate: int,
    #                 steps_per_month: int,
    #                 state_model_name: str,
    #                 portfolio_path: str,
    #                 assumptions_path: str,
    #                 outfile: str,
    #                 portfolio_cache: str,
    #                 profile_out_dir: str,
    #                 portfolio_chunk_size: int,
    #                 use_multicore: bool
    #                 ):    

    # construct assumption set
    provider05 = actuarial.ConstantRateProvider(0.5)
    provider02 = actuarial.ConstantRateProvider(0.2)
    acs = actuarial.AssumptionSet(2)
    acs.add_provider_const(0, 1, provider02)
    acs.add_provider_const(1, 0, provider05)

    # get a portfolio
    # py_portfolio = Portfolio("examples/03_mortality/portfolio/portfolio_small.xlsx", states_model=MortalityStates)
    py_portfolio = Portfolio("examples/04_two_state_disability/portfolio/portfolio_med.xlsx", states_model=MultiStateDisabilityStates)
    # py_portfolio = Portfolio("examples/04_two_state_disability/portfolio/portfolio_big.xlsx", states_model=MultiStateDisabilityStates)
    # py_portfolio = Portfolio("examples/04_two_state_disability/portfolio/portfolio_small.xlsx", states_model=MultiStateDisabilityStates)

    c_portfolio = actuarial.build_c_portfolio(py_portfolio)
    time_step = actuarial.TimeStep.MONTHLY  # actuarial.TimeStep.MONTHLY  # QUARTERLY   # TODO: test if we get back a result set with this timestep

    # not really a test but at least a check if it fails
    print("Start calc...")
    t = time.time()
    output_columns, result = actuarial.py_run_c_valuation(acs, c_portfolio, time_step)
    # do stuff
    elapsed = time.time() - t
    print("Done, time elapsed=", elapsed)

    print(output_columns)
    # print(result[:15, :])
    # print("ok")

    df = pd.DataFrame(data=result, columns=output_columns)
    df.to_excel("out.xlsx")


test_c_run_with_config()

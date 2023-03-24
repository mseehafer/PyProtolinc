
import time
import pandas as pd

import pyprotolinc._actuarial as actuarial
from pyprotolinc.models.state_models import MultiStateDisabilityStates
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
    output_columns, result = actuarial.py_run_c_valuation(acs, c_portfolio, time_step, 120)
    # do stuff
    elapsed = time.time() - t
    print("Done, time elapsed=", elapsed)

    print(output_columns)
    # print(result[:15, :])
    # print("ok")

    df = pd.DataFrame(data=result, columns=output_columns)
    df.to_excel("out.xlsx")


def test_c_run_with_config():

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
    output_columns, result = actuarial.py_run_c_valuation(acs, c_portfolio, time_step, 120)
    elapsed = time.time() - t
    print("Done, time elapsed=", elapsed)

    print(output_columns)
    # print(result[:15, :])
    # print("ok")

    df = pd.DataFrame(data=result, columns=output_columns)
    df.to_excel("out.xlsx")


test_c_run_with_config()

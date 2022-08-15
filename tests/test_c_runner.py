

# import pytest
# import numpy as np
from os import times_result
import pyprotolinc._actuarial as actuarial
from pyprotolinc.models.model_mortality import MortalityStates
# from pyprotolinc.models.model_annuity_runoff import AnnuityRunoffStates
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

    c_portfolio = actuarial.build_c_portfolio(py_portfolio)
    time_step = actuarial.TimeStep.QUARTERLY #actuarial.TimeStep.MONTHLY  # QUARTERLY   # TODO: test if we get back a result set with this timestep

    # not really a test but at least a check if it fails
    result = actuarial.py_run_c_valuation(acs, c_portfolio, time_step)


    print(result[:15, :].astype(int))
    # print(result[:15,:])
    # print("ok")


test_c_run()

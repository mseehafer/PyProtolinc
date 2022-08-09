
from pyprotolinc.models.model_mortality import MortalityStates
from pyprotolinc.models.model_disability_multistate import MultiStateDisabilityStates
from pyprotolinc.portfolio import Portfolio

from pyprotolinc._actuarial import build_c_portfolio


def test_portfolio_load():

    print("Loading portfolio from file")
    py_portfolio = Portfolio("examples/03_mortality/portfolio/portfolio_small.xlsx", states_model=MortalityStates)

    print("Building C-Portfolio")
    c_portfolio = build_c_portfolio(py_portfolio)

    print(len(c_portfolio))

    assert len(c_portfolio) == len(py_portfolio)
    print(c_portfolio.get_info(0))
    return c_portfolio


def test_portfolio_load_big():

    print("Loading portfolio from file")
    py_portfolio = Portfolio("examples/04_two_state_disability/portfolio/portfolio_med.xlsx", states_model=MultiStateDisabilityStates)
    #py_portfolio = Portfolio("examples/04_two_state_disability/portfolio/portfolio_big.xlsx", states_model=MultiStateDisabilityStates)

    print("Building C-Portfolio")
    c_portfolio = build_c_portfolio(py_portfolio)

    print(len(c_portfolio))

    assert len(c_portfolio) == len(py_portfolio)
    print(c_portfolio.get_info(0))
    return c_portfolio


# test_portfolio_load()
# test_portfolio_load_big()
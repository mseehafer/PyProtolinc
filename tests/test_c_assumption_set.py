
import numpy as np
import pyprotolinc._actuarial as actuarial
from pyprotolinc.assumptions.iohelpers import AssumptionsLoaderFromConfig

# from pyprotolinc.models import ModelBuilder
# from pyprotolinc.models.model_multistate_generic import GenericMultiStateModel, adjust_state_for_generic_model
# from pyprotolinc.models.model_disability_multistate import MultiStateDisabilityStates
from pyprotolinc.assumptions.providers import AssumptionType


def test_assumption_set_const():

    provider05 = actuarial.ConstantRateProvider(0.5)
    provider02 = actuarial.ConstantRateProvider(0.2)

    acs = actuarial.AssumptionSet(2)

    acs.add_provider_const(0, 1, provider02)
    acs.add_provider_const(1, 0, provider05)

    rates = acs.get_single_rateset([0] * len(actuarial.CRiskFactors))

    assert np.array_equal(rates, np.array([0, 0.2, 0.5, 0]))


def test_assumption_set_std():

    vals2D = np.array([
        [1, 2, 3],
        [4, 5, 6]], dtype=np.float64)
    offsets = np.zeros(2, dtype=np.int32)
    providerS = actuarial.StandardRateProvider([actuarial.CRiskFactors.Gender, actuarial.CRiskFactors.Age], vals2D, offsets)

    provider02 = actuarial.ConstantRateProvider(0.2)

    acs = actuarial.AssumptionSet(2)
    acs.add_provider_const(0, 1, provider02)
    acs.add_provider_std(1, 0, providerS)

    rates = acs.get_single_rateset([2, 1, 0, 0, 0])
    # print(rates)

    assert np.array_equal(rates, np.array([0, 0.2, 6, 0]))  # 0.2 from constant, age=2, gender=1 imply second row, third col

    providerS2 = actuarial.StandardRateProvider([actuarial.CRiskFactors.Age, actuarial.CRiskFactors.Gender], vals2D, offsets)

    acs.add_provider_std(1, 1, providerS2)
    rates = acs.get_single_rateset([1, 0, 0, 0, 0])
    # print(rates)

    assert np.array_equal(rates, np.array([0, 0.2, 2, 4]))  # 0.2 from constant
                                                            # third position: age=1, gender=0 imply first row, second col (->2)
                                                            # fourth position: age=1, gender=0 imply second row=1, first col (-> 4)


def test_assumption_set_from_file():
    states_dimension = 4
    assumption_config_loader = AssumptionsLoaderFromConfig(r"tests\di_assumptions.yml", states_dimension)
    acs: actuarial.AssumptionSet = assumption_config_loader.load().build_assumption_set(AssumptionType.BE)

    # define the risk factors
    # Age, Gender, CalendarYear, SmokerStatus, YearsDisabledIfDisabledAtStart
    risk_factor_values = (32, 1, 2023, 1, -1)
    rates = acs.get_single_rateset(risk_factor_values).reshape((states_dimension, states_dimension))
    # print(rates)

    # order of the states :
    # ACTIVE = 0
    # DIS1 = 1
    # DIS2 = 2
    # DEATH = 3
    # LAPSED = 4

    target = np.array([[0.0, 0.0, 0.049, 0.000725],
                       [0.0, 0.0, 0.0,   0.06],
                       [0.0, 0.0, 0.0,   0.0],
                       [0.0, 0.0, 0.0,   0.0]])

    assert np.array_equal(rates, target)


if __name__ == "__main__":
    test_assumption_set_from_file()
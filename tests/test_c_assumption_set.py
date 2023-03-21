
import numpy as np
import pyprotolinc._actuarial as actuarial
from pyprotolinc.assumptions.iohelpers import AssumptionsLoaderFromConfig

from pyprotolinc.models import ModelBuilder
from pyprotolinc.models.model_multistate_generic import GenericMultiStateModel, adjust_state_for_generic_model
from pyprotolinc.models.model_disability_multistate import MultiStateDisabilityStates
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

    assert np.array_equal(rates, np.array([0, 0.2, 2, 4]))   # 0.2 from constant
                                                             # third position: age=1, gender=0 imply first row, second col (->2)
                                                             # furth position: age=1, gender=0 imply second row=1, first col (-> 4)


def test_assumption_set_from_file():
    # build the model as in example 4
    mb = ModelBuilder(GenericMultiStateModel, MultiStateDisabilityStates)
    ass_config_loader = AssumptionsLoaderFromConfig(r"tests\di_assumptions.yml")
    ass_config_loader.load(mb)

    import pyprotolinc.models.model_config   # needed for the code that is run on importing
    model: GenericMultiStateModel = mb.build()
    adjust_state_for_generic_model(model, 'MultiStateDisabilityStates')

    print(model.MODEL_NAME)
    print(model.states_model)
    print(model.known_states)

    # build the assumption set for the BE
    states_dim = len(model.known_states)
    acs = actuarial.AssumptionSet(states_dim)
    non_trivial_state_transitions_be = model.get_non_trivial_state_transitions(AssumptionType.BE)
    for (from_state, to_state) in non_trivial_state_transitions_be:
        provider = model.rates_provider_matrix_be[from_state][to_state]

        print(from_state, to_state, provider.get_risk_factors())

        if isinstance(provider, actuarial.ConstantRateProvider):
            acs.add_provider_const(from_state, to_state, provider)
        elif isinstance(provider, actuarial.StandardRateProvider):
            acs.add_provider_std(from_state, to_state, provider)

    # define the risk factors
    # Age, Gender, CalendarYear, SmokerStatus, YearsDisabledIfDisabledAtStart
    risk_factor_values = (31, 1, 2022, 3, 0)
    rates = acs.get_single_rateset(risk_factor_values).reshape((states_dim, states_dim))
    print(rates)

    # order of the states :
    # ACTIVE = 0
    # DIS1 = 1
    # DIS2 = 2
    # DEATH = 3
    # LAPSED = 4

    target = np.array([[0.,      0.03,    0.03,    0.000674, 0.05],
                       [0.2,     0.,      0.2,     0.06,     0.],
                       [0.01,    0.1,     0.,      0.2,      0.],
                       [0.,      0.,      0.,      0.,       0.],
                       [0.,      0.,      0.,      0.,       0.]])

    assert np.array_equal(rates, target)


if __name__ == "__main__":
    test_assumption_set_from_file()
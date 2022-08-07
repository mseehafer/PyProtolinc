
import numpy as np
import pyprotolinc._actuarial as actuarial


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
                                                            # furth position: age=1, gender=0 imply second row=1, first col (-> 4)

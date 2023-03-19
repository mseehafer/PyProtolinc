import numpy as np
import pyprotolinc._actuarial as act
from pyprotolinc.riskfactors.risk_factors import Gender, SmokerStatus


def test_slicing2d():
    std_prvdr_2d = act.StandardRateProvider(rfs=[act.CRiskFactors.Gender, act.CRiskFactors.Age],
                                            values=np.array([[0.1, 0.2, 0.3],
                                                            [1.1, 1.2, 1.3]]),
                                            offsets=np.zeros(2, dtype=np.int32))
    # x1 = std_prvdr_2d.slice(gender=1)
    # print("OUT:", x1.get_values())
    # print("OUT:", std_prvdr_2d.slice(gender=0).get_values())

    assert np.array_equal(std_prvdr_2d.slice(gender=0).get_values(), np.array([0.1, 0.2, 0.3]))
    assert np.array_equal(std_prvdr_2d.slice(gender=1).get_values(), np.array([1.1, 1.2, 1.3]))

    assert np.array_equal(std_prvdr_2d.slice(age=0).get_values(), np.array([0.1, 1.1]))
    assert np.array_equal(std_prvdr_2d.slice(age=1).get_values(), np.array([0.2, 1.2]))
    assert np.array_equal(std_prvdr_2d.slice(age=2).get_values(), np.array([0.3, 1.3]))

    assert np.array_equal(std_prvdr_2d.slice().get_values(), np.array([0.1, 0.2, 0.3, 1.1, 1.2, 1.3]))

    assert np.array_equal(std_prvdr_2d.slice(age=0, gender=0).get_values(), np.array([0.1]))
    assert np.array_equal(std_prvdr_2d.slice(age=0, gender=1).get_values(), np.array([1.1]))
    assert np.array_equal(std_prvdr_2d.slice(gender=0, age=1).get_values(), np.array([0.2]))
    assert np.array_equal(std_prvdr_2d.slice(gender=1, age=1).get_values(), np.array([1.2]))
    assert np.array_equal(std_prvdr_2d.slice(age=2, gender=0).get_values(), np.array([0.3]))
    assert np.array_equal(std_prvdr_2d.slice(age=2, gender=1).get_values(), np.array([1.3]))


# std_prvdr_2d = act.StandardRateProvider(rfs=[act.CRiskFactors.Gender, act.CRiskFactors.Age],
#                                             values=np.array([[0.1, 0.2, 0.3],
#                                                             [1.1, 1.2, 1.3]]),
#                                             offsets=np.zeros(2, dtype=int))
# print(std_prvdr_2d.slice(age=0, gender=0).get_values())

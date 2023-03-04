import pytest
import pickle
import numpy as np
import pyprotolinc._actuarial as actuarial


def test_constant_provider():
    provider0 = actuarial.ConstantRateProvider()
    providerC = actuarial.ConstantRateProvider(0.6)

    print(provider0.get_rate(), providerC.get_rate())

    assert provider0.get_rate() == 0
    assert providerC.get_rate() == 0.6

    assert np.array_equal(np.array([0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, ]), providerC.get_rates(8))
    assert np.array_equal(np.array([0.6, 0.6]), providerC.get_rates(2))


def test_std_2d():

    # vals1D = np.array([1, 2, 3], dtype=np.float64)
    vals2D = np.array([
        [1, 2, 3],
        [4, 5, 6]], dtype=np.float64)

    offsets = np.zeros(2, dtype=np.int32)
    # dimension mismatch should produce an exception

    providerS = actuarial.StandardRateProvider([actuarial.CRiskFactors.Gender, actuarial.CRiskFactors.Age], vals2D, offsets)

    # test get rates
    assert providerS.get_rate([0, 0]) == 1
    assert providerS.get_rate([0, 1]) == 2
    assert providerS.get_rate([0, 2]) == 3
    assert providerS.get_rate([1, 0]) == 4
    assert providerS.get_rate([1, 1]) == 5
    assert providerS.get_rate([1, 2]) == 6

    gender = np.array([0, 1, 0, 1, 0, 1], dtype=np.int32)
    age = np.array([0, 0, 1, 1, 2, 2], dtype=np.int32)

    assert np.array_equal(np.array([1., 4., 2., 5., 3., 6.]), providerS.get_rates(len(gender), age=age, gender=gender))

    assert providerS.__repr__() == "<CStandardRateProvider with RF (Gender, Age)>"

    # check for out of range exception
    with pytest.raises(IndexError):
        gender2 = np.array([0, 1, 0, 1, 0, 1], dtype=np.int32)
        age2 = np.array([0, 0, 1, 3, 2, 2], dtype=np.int32)

        providerS.get_rates(len(gender2), age=age2, gender=gender2)


def test_pickle_constant_rate_provider():
    rate = 0.02
    const_prov = actuarial.ConstantRateProvider(rate)
    const_prov2 = pickle.loads(pickle.dumps(const_prov))

    assert const_prov2.get_rate() == rate


def test_standard_rate_provider_getters():
    # create a provider
    vals2D = np.array([
        [1, 2, 3],
        [4, 5, 6]], dtype=np.float64)

    offsets = np.zeros(2, dtype=np.int32)
    offsets[0] = 2
    providerS = actuarial.StandardRateProvider([actuarial.CRiskFactors.Gender, actuarial.CRiskFactors.Age], vals2D, offsets)

    assert providerS.get_shape() == (2, 3)
    assert np.array_equal(providerS.get_offsets(), offsets)
    np.array_equal(providerS.get_values().reshape(providerS.get_shape()), vals2D)


def test_pickle_standard_rate_provider():
    # create a provider
    vals2D = np.array([
        [1, 2, 3],
        [4, 5, 6]], dtype=np.float64)

    offsets = np.zeros(2, dtype=np.int32)
    offsets[0] = 2
    providerS = actuarial.StandardRateProvider([actuarial.CRiskFactors.Gender, actuarial.CRiskFactors.Age], vals2D, offsets)

    # pickle and load again
    serialized = pickle.dumps(providerS)
    providerS2 = pickle.loads(serialized)

    # check that we get the same pickle bytes again
    assert serialized == pickle.dumps(providerS2)

    # check shape
    assert providerS2.get_shape() == providerS.get_shape()
    # check values
    assert np.array_equal(providerS2.get_values().reshape(providerS2.get_shape()), vals2D)
    # check offsets
    assert np.array_equal(providerS2.get_offsets(), offsets)

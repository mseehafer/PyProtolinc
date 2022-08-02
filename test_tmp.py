import numpy as np
import pyprotolinc._actuarial as actuarial

provider0 = actuarial.ConstantRateProvider()
providerC = actuarial.ConstantRateProvider(0.6)

print(provider0.get_rate(), providerC.get_rate())

assert provider0.get_rate() == 0
assert providerC.get_rate() == 0.6

print(providerC.get_rates(8), providerC.get_rates(2))

# vals1D = np.array([1, 2, 3], dtype=np.float64)
vals2D = np.array([
    [1, 2, 3],
    [4, 5, 6]], dtype=np.float64)

offsets = np.zeros(2, dtype=int)
# dimension mismatch should produce an exception

providerS = actuarial.StandardRateProvider(vals2D, offsets)


# test get rates
assert providerS.get_rate([0, 0]) == 1
assert providerS.get_rate([0, 1]) == 2
assert providerS.get_rate([0, 2]) == 3
assert providerS.get_rate([1, 0]) == 4
assert providerS.get_rate([1, 1]) == 5
assert providerS.get_rate([1, 2]) == 6


print("Output:", providerS.get_rate([0, 1]))

providerS.add_risk_factor(actuarial.CRiskFactors.Gender)
providerS.add_risk_factor(actuarial.CRiskFactors.Age)
# should produce an exception: providerS.add_risk_factor(actuarial.CRiskFactors.Age)

gender = np.array([0, 1, 0, 1, 0, 1], dtype=int)
age = np.array([0, 0, 1, 1, 2, 2], dtype=int)

print()
print()
print(providerS.get_rates(len(gender), age=age, gender=gender))

assert np.array_equal(np.array([1., 4., 2., 5., 3., 6.]), providerS.get_rates(len(gender), age=age, gender=gender))

print(providerS)
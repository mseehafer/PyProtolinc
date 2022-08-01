import numpy as np
import pyprotolinc._actuarial as actuarial

providerS = actuarial.AssumptionsProvider("STANDARD")

vals1D = np.array([1, 2, 3], dtype=np.float64)
vals2D = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float64)

providerS._set_values1D(vals1D)


providerS._set_values2D(vals2D)
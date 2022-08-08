

import pytest
import numpy as np
import pyprotolinc._actuarial as actuarial


def test_c_run():

    # construct assumption set
    provider05 = actuarial.ConstantRateProvider(0.5)
    provider02 = actuarial.ConstantRateProvider(0.2)
    acs = actuarial.AssumptionSet(2)
    acs.add_provider_const(0, 1, provider02)
    acs.add_provider_const(1, 0, provider05)

    # not really a test but at least a check if it fails
    actuarial.py_run_c_valuation(acs)

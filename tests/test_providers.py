
import os

import numpy as np
import pytest

from pyprotolinc.utils import download_dav_tables
from pyprotolinc.assumptions.dav2004r import DAV2004R, DAV2004R_B20
from pyprotolinc.assumptions.dav2008t import DAV2008T
import pyprotolinc.models.risk_factors as risk_factors


def test_dav2004r_b20(tmp_path):
    """ Test for the rates provider class for the B20 table. """

    # download the DAV tables
    download_dav_tables(target_dir=tmp_path)
    print(tmp_path)

    # set up the test cases
    birthyear = np.array([1940, 1949], dtype=np.int16)
    gender = np.array([risk_factors.Gender.M, risk_factors.Gender.F], dtype=np.int16)
    ages = np.array([40, 50], dtype=np.int16)
    
    b20 = DAV2004R_B20(os.path.join(tmp_path, "tables", "Germany_Annuities_DAV2004R"))
    provider = b20.rates_provider()
    provider.initialize(years_of_birth=birthyear, gender=gender)

    # test with different selection factors
    select_male = [0.670538, 0.876209, 0.876209, 0.876209, 0.876209, 1, 1]
    select_female = [0.712823, 0.79823, 0.79823, 0.79823, 0.79823, 1, 1]
    for k in range(7):
        yearsdisabledifdisabledatstart = np.array([k, k], dtype=np.int16)

        rates = provider.get_rates(length=len(ages),
                                   age=ages,
                                   gender=gender,
                                   yearsdisabledifdisabledatstart=yearsdisabledifdisabledatstart)

        print("k =", k, rates)
        assert rates[0] == pytest.approx(select_male[k] * 0.001648)
        assert rates[1] == pytest.approx(select_female[k] * 0.001645)
    
    # check the risk factor list
    assert set(provider.get_risk_factors()) == {risk_factors.YearsDisabledIfDisabledAtStart, risk_factors.Gender, risk_factors.Age}




# distutils: language = c++

import cython
from cython.operator cimport dereference
import numpy as np

from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr, make_shared

cimport numpy as np
import pandas as pd

# # should go into .pxd file?
# cdef extern from "providers.h":

#     cdef cppclass CBaseRatesProvider:

#         void get_rates(double *out_array, int length) const
#         void get_risk_factors() const
#         string to_string() const

#     cdef cppclass CZeroRateProvider:

#         void get_rates(double *out_array, int length) const
#         void get_risk_factors() const
#         string to_string() const

#     cdef cppclass CConstantRateProvider:

#         CConstantRateProvider(double)
#         CConstantRateProvider()
#         void set_rate(double rate)
#         void get_rates(double *out_array, int length) const
#         void get_risk_factors() const
#         string to_string() const


# def provider_wrapper(int _len, double val):
#     cdef CConstantRateProvider const_prov
#     cdef np.ndarray[double, ndim=1, mode="c"] output = np.zeros(_len)

#     const_prov.set_rate(val)

#     const_prov.get_rates(<double*> output.data, _len)
#     return output

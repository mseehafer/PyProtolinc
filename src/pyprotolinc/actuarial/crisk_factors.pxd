# distutils: language = c++
import cython


# should go into .pxd file?
cdef extern from "risk_factors.h":

    cdef const unsigned NUMBER_OF_RISK_FACTORS

    cpdef enum class CRiskFactors(int):
        Age,
        Gender,
        CalendarYear,
        SmokerStatus,
        YearsDisabledIfDisabledAtStart,
    
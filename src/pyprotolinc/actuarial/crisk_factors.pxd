# distutils: language = c++
import cython


# should go into .pxd file?
cdef extern from "risk_factors.h":

    cpdef enum class CRiskFactors(int):
        Age,
        Gender,
        CalendarYear,
        SmokerStatus,
        YearsDisabledIfDisabledAtStart,
    
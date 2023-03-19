from abc import ABC, abstractmethod

import numpy as np

# from pyprotolinc.assumptions.providers import ZeroRateProvider
# from pyprotolinc.assumptions.providers import ConstantRateProvider
# from pyprotolinc.assumptions.providers import StandardRateProvider
import pyprotolinc._actuarial as act  # type: ignore
from pyprotolinc.assumptions.providers import BaseRatesProvider


class AbstrAssumptionsTable(ABC):
    """ Abstract base class for the assumption table classes. """

    @abstractmethod
    def rates_provider(self) -> BaseRatesProvider:
        pass


class ScalarAssumptionsTable(AbstrAssumptionsTable):
    """ Represents a 0-dimensional (i.e. scalar) assumption. """

    def __init__(self, const_value: float):
        self.const_value = const_value

    def rates_provider(self) -> BaseRatesProvider:
        b: BaseRatesProvider = act.ConstantRateProvider(self.const_value)
        return b
        # if self.const_value == 0:
        #     return ZeroRateProvider()
        # else:
        #     return ConstantRateProvider(self.const_value)


class AssumptionsTable1D(AbstrAssumptionsTable):
    """ Represents a 1D assumption table. """

    def __init__(self, values, risk_factor_class, offset=0):
        self.offset = offset
        # assert values is a numpy array
        shape = values.shape
        dims = len(shape)
        if dims == 2:
            if shape[0] > 1 and shape[1] > 1:
                raise Exception("Wrong dimension passed in for 1D assumptions table: {}".format(str(shape)))
            elif shape[1] == 1:
                values = values.reshape((shape[0],))
            else:
                values = values.reshape((shape[1],))
        elif dims > 2:
            raise Exception("Wrong dimension passed in for 1D assumptions table: {}".format(str(shape)))

        req_length = risk_factor_class.required_length()
        if req_length is not None:
            assert req_length == len(values), "Required length of assumptions does not fit for {}".format(
                risk_factor_class.__name__
            )
        self.values = values.astype(np.float64)
        self.risk_factor_class = risk_factor_class

    def rates_provider(self):
        # return StandardRateProvider(self.values, (self.risk_factor_class,), offsets=(self.offset,))
        return act.StandardRateProvider(rfs=[self.risk_factor_class.get_CRiskFactor()],
                                        values=self.values,
                                        offsets=np.array([self.offset, ], dtype=np.int32))


class AssumptionsTable2D(AbstrAssumptionsTable):
    """ Represents a 2D assumption table. """

    def __init__(self, values, risk_factor_class_v, risk_factor_class_h, v_offset=0, h_offset=0):
        self.v_offset = v_offset
        self.h_offset = h_offset
        # assert values is a numpy array
        shape = values.shape
        if len(shape) != 2:
            raise Exception("Wrong dimension passed in for 1D assumptions table: {}".format(str(shape)))

        req_length_v = risk_factor_class_v.required_length()
        req_length_h = risk_factor_class_h.required_length()
        if req_length_v is not None:
            assert req_length_v == shape[0], "Vertical length of assumptions does not fit for {}".format(
                risk_factor_class_v.__name__
            )
        if req_length_h is not None:
            assert req_length_h == shape[1], "Horizontal length of assumptions does not fit for {}".format(
                risk_factor_class_h.__name__
            )

        self.values = values.astype(np.float64)

        self.risk_factor_class_v = risk_factor_class_v
        self.risk_factor_class_h = risk_factor_class_h

    def rates_provider(self):
        # return StandardRateProvider(self.values, (self.risk_factor_class_v, self.risk_factor_class_h),
        #                            offsets=(self.v_offset, self.h_offset))

        return act.StandardRateProvider(rfs=[self.risk_factor_class_v.get_CRiskFactor(),
                                        self.risk_factor_class_h.get_CRiskFactor()],
                                        values=self.values,
                                        offsets=np.array((self.v_offset, self.h_offset), dtype=np.int32))

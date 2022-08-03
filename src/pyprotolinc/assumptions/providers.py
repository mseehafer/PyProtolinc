""" Assumption provider classes are used to obtain
    rates for a set of (vectorized) risk factors
    during a simulation run."""

import logging
from enum import IntEnum, unique
import numpy as np

# module level logger
logger = logging.getLogger(__name__)


@unique
class AssumptionType(IntEnum):
    """ We distinguish between best estimate (BE) and reserving assumptions (RES). """
    BE = 0
    RES = 1


class BaseRatesProvider:
    """ Base class for `rates providers`."""

    def get_rates(self, length):
        raise Exception("Method <get_rate> must be overwritten in subclass")

    def initialize(self, **kwargs):
        """ The ìnitialize hook can be used for setup actions. """
        # print(self.__class__.__name__, "Init-Hook")
        pass

    def get_risk_factors(self):
        """ This method returns an iterable of the relevant risk factors. """
        return ()


class ZeroRateProvider(BaseRatesProvider):

    def get_rates(self, length, **kwargs):
        return np.zeros(length)

    def __repr__(self):
        return "<ZeroRateProvider>"


class ConstantRateProvider(BaseRatesProvider):

    def __init__(self, const_rate):
        self.const_rate = const_rate

    def get_rates(self, length, **kwargs):
        return np.ones(length) * self.const_rate

    def __repr__(self):
        return "<ConstantRateProvider with constant {}>".format(self.const_rate)


class StandardRateProvider(BaseRatesProvider):
    """ Rates provider class is used to return the rates
        given a selector array for each risk factor. """

    def __init__(self, values, risk_factors, offsets=None):
        """ Data to be provided is an n-dimensional numpy array and an iterable of RiskFactors."""
        self.num_dimensions = len(values.shape)
        self.offsets = offsets
        if offsets is not None:
            assert len(self.offsets) == self.num_dimensions
        else:
            self.offsets = [0] * self.num_dimensions
        assert self.num_dimensions == len(risk_factors), "Number of risk factors and dimension of values must agree!"
        assert self.num_dimensions >= 0 and self.num_dimensions < 4, "Number of dimensions must be between 0 and 3"
        self.values = np.copy(values)

        self.max_indexes = [i - 1 for i in self.values.shape]

        # store the risk factor classes and names
        self.risk_factor_classes = list(risk_factors)
        self.risk_factor_names = [rf.__name__.lower() for rf in risk_factors]

    def get_risk_factors(self):
        """ This method returns an iterable of the relevant risk factors. """
        return self.risk_factor_classes

    def get_rates(self, length=None, **kwargs):
        """ Rates are returned, the arguments must agree with the risk factors and
            contain numpy arrays that are used to index the values tensor. """

        attr = {k.lower(): v for (k, v) in kwargs.items()}

        # leave this is only in `diagnosis mode`
        # check for unknown risk factors provided
        # unknown_rfs = attr.keys() - set(self.risk_factors)
        # if unknown_rfs:
        #    logger.debug("Risk factors unknown for this provider: {}, expected only {}"
        #                 .format(str(unknown_rfs), self.risk_factors))

        # order the selectors
        selectors = []
        for rf_name in self.risk_factor_names:
            selectors.append(attr[rf_name])

        if self.num_dimensions == 0:
            return self.values[0]
        elif self.num_dimensions == 1:
            if selectors[0].min() - self.offsets[0] < 0:
                raise Exception("Negative assumption index")

            return self.values[np.minimum(selectors[0] - self.offsets[0], self.max_indexes[0]),]
        elif self.num_dimensions == 2:
            if (selectors[0].min() - self.offsets[0] < 0 or
               selectors[1].min() - self.offsets[1] < 0):
                raise Exception("Negative assumption index")

            return self.values[np.minimum(selectors[0] - self.offsets[0], self.max_indexes[0]),
                               np.minimum(selectors[1] - self.offsets[1], self.max_indexes[1])]
        elif self.num_dimensions == 3:
            if (selectors[0].min() - self.offsets[0] < 0 or
               selectors[1].min() - self.offsets[1] < 0 or
               selectors[2].min() - self.offsets[2] < 0):
                raise Exception("Negative assumption index")

            return self.values[np.minimum(selectors[0] - self.offsets[0], self.max_indexes[0]),
                               np.minimum(selectors[1] - self.offsets[1], self.max_indexes[1]),
                               np.minimum(selectors[2] - self.offsets[2], self.max_indexes[2])]

        print(self.num_dimensions)
        raise Exception("Method must be implemented in subclass.")

    def __repr__(self):
        return "<StandardRateProvider with factors ({})>".format(str(self.risk_factor_names))


class AssumptionTimestepAdjustment:
    """ The class converts yearly decrements to decrements applicable for fractions
        of the year. """

    def __init__(self, timestep, num_MultiStateDisabilityStates, num_insureds):
        self.timestep = timestep
        self.num_MultiStateDisabilityStates = num_MultiStateDisabilityStates
        self.num_insureds = num_insureds

        # Construct some auxiliary indexes.
        # First an index consisting of 5(=num_MultiStateDisabilityStates) zeros followed by
        # 5 ones followed by 5 twos etc.
        # The process continues until num_insureds - 1
        self.first_ind = np.arange(1, 1 + num_insureds, dtype=np.int32)\
                           .reshape((num_insureds, 1))\
                           .dot(np.ones((1, num_MultiStateDisabilityStates), dtype=np.int32))\
                           .reshape(num_MultiStateDisabilityStates * num_insureds) - 1

        # Secondly an index consisting of the sequence 0, 1, 2, 3, 4 (num_MultiStateDisabilityStates - 1) repeated for each insured
        self.other_ind = np.ones((num_insureds, 1), dtype=np.int32)\
                           .dot(np.arange(1, 1 + num_MultiStateDisabilityStates, dtype=np.int32)
                                  .reshape((1, num_MultiStateDisabilityStates)))\
                           .reshape(num_MultiStateDisabilityStates * num_insureds) - 1

    def adjust_simple(self, A):
        """ Adjust the matrix A as follows:

            Multiply the decrements by self.timestep to adjust for the fraction of the year. Then fill the diagonals such
            that the target transition MultiStateDisabilityStates add up to 1 for each insured and starting-state.
        """

        A_per_step = np.nan_to_num(A) * self.timestep
        row_sums = A_per_step.sum(axis=2)
        A_per_step[self.first_ind, self.other_ind, self.other_ind] = 1 - row_sums.reshape(self.num_MultiStateDisabilityStates * self.num_insureds)
        return A_per_step

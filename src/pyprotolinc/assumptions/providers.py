""" Assumption provider classes are used to obtain
    rates for a set of (vectorized) risk factors
    during a simulation run."""

from abc import ABCMeta, abstractmethod
from typing import Optional, Any, Union
import logging
from enum import IntEnum, unique
import numpy as np
import numpy.typing as npt

from pyprotolinc.riskfactors.risk_factors import RiskFactor
import pyprotolinc._actuarial as actuarial  # type: ignore


# module level logger
logger = logging.getLogger(__name__)


@unique
class AssumptionType(IntEnum):
    """ Distinguish between best estimate (BE) and reserving assumptions (RES). """
    BE = 0
    RES = 1


class BaseRatesProvider(metaclass=ABCMeta):
    """ Base class for `rates providers`."""

    @abstractmethod
    def get_rates(self, length: int) -> npt.NDArray[np.float64]:
        raise Exception("Method <get_rate> must be overwritten in subclass")

    @abstractmethod
    def initialize(self, **kwargs: Any) -> None:
        """ The initialize hook can be used for setup actions. """
        pass

    @abstractmethod
    def get_risk_factors(self) -> list[type[RiskFactor]]:
        """ This method returns an iterable of the relevant risk factors. """
        return list()


class ZeroRateProvider(BaseRatesProvider):

    def get_rates(self, length: int, **kwargs: Any) -> npt.NDArray[np.float64]:
        return np.zeros(length)

    def __repr__(self) -> str:
        return "<ZeroRateProvider>"


class ConstantRateProvider(BaseRatesProvider):

    def __init__(self, const_rate: float) -> None:
        self.const_rate = const_rate

    def get_rates(self, length: int, **kwargs: Any) -> npt.NDArray[np.float64]:
        return np.ones(length) * self.const_rate

    def __repr__(self) -> str:
        return "<ConstantRateProvider with constant {}>".format(self.const_rate)


class StandardRateProvider(BaseRatesProvider):
    """ Rates provider class is used to return the rates
        given a selector array for each risk factor. """

    def __init__(self,
                 values: npt.NDArray[np.float64],
                 risk_factors: list[type[RiskFactor]],
                 offsets_in: Optional[Union[npt.NDArray[np.int32], tuple[int]]] = None) -> None:
        """ Data to be provided is an n-dimensional numpy array and an iterable of RiskFactors."""
        self.num_dimensions = len(values.shape)

        # copy offsets into numpy array
        self.offsets: npt.NDArray[np.int32] = np.zeros(self.num_dimensions, dtype=np.int32)
        if offsets_in is not None:
            assert len(offsets_in) == self.num_dimensions
            for k in range(self.num_dimensions):
                self.offsets[k] = offsets_in[k]

        assert self.num_dimensions == len(risk_factors), "Number of risk factors and dimension of values must agree!"
        assert self.num_dimensions >= 0 and self.num_dimensions < 4, "Number of dimensions must be between 0 and 3"

        self.values: npt.NDArray[np.float64] = np.copy(values)

        self.max_indexes = [i - 1 for i in self.values.shape]

        # store the risk factor classes and names
        self.risk_factor_classes = list(risk_factors)
        self.risk_factor_names = [rf.__name__.lower() for rf in risk_factors]

    def get_risk_factors(self) -> list[type[RiskFactor]]:
        """ This method returns an iterable of the relevant risk factors. """
        return self.risk_factor_classes

    def get_rates(self, length: int = -1, **kwargs: Any) -> npt.NDArray[np.float64]:
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
            val: float = self.values[0]
            return val * np.ones(1)
        elif self.num_dimensions == 1:
            if selectors[0].min() - self.offsets[0] < 0:
                raise Exception("Negative assumption index")
            # this might not be the correct type but silences the numpy warning
            # when returning the sliced array directly
            a1: npt.NDArray[np.float64] = self.values[np.minimum(selectors[0] - self.offsets[0], self.max_indexes[0]), ]  # ignore: type
            return a1
        elif self.num_dimensions == 2:
            if (selectors[0].min() - self.offsets[0] < 0 or
               selectors[1].min() - self.offsets[1] < 0):
                raise Exception("Negative assumption index")
            a2: npt.NDArray[np.float64] = self.values[np.minimum(selectors[0] - self.offsets[0], self.max_indexes[0]),
                                                      np.minimum(selectors[1] - self.offsets[1], self.max_indexes[1])]
            return a2
        elif self.num_dimensions == 3:
            if (selectors[0].min() - self.offsets[0] < 0 or
               selectors[1].min() - self.offsets[1] < 0 or
               selectors[2].min() - self.offsets[2] < 0):
                raise Exception("Negative assumption index")
            a3: npt.NDArray[np.float64] = self.values[np.minimum(selectors[0] - self.offsets[0], self.max_indexes[0]),
                                                      np.minimum(selectors[1] - self.offsets[1], self.max_indexes[1]),
                                                      np.minimum(selectors[2] - self.offsets[2], self.max_indexes[2])]
            return a3

        print(self.num_dimensions)
        raise Exception("Method must be implemented in subclass.")

    def __repr__(self) -> str:
        return "<StandardRateProvider with factors ({})>".format(str(self.risk_factor_names))


class AssumptionTimestepAdjustment:
    """ The class converts yearly decrements to decrements applicable for fractions
        of the year. """

    def __init__(self, timestep: float, num_MultiStateDisabilityStates: int, num_insureds: int) -> None:
        """ : timestep   - length of the timestep to adjust the assumptions to. """
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

    def adjust_simple(self, A: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """ Adjust the matrix A as follows:

            Multiply the decrements by self.timestep to adjust for the fraction of the year. Then fill the diagonals such
            that the target transition MultiStateDisabilityStates add up to 1 for each insured and starting-state.
        """

        A_per_step = np.nan_to_num(A) * self.timestep
        row_sums = A_per_step.sum(axis=2)
        A_per_step[self.first_ind, self.other_ind, self.other_ind] = 1 - row_sums.reshape(self.num_MultiStateDisabilityStates * self.num_insureds)
        return A_per_step


class AssumptionSetWrapper:
    """ Wraps an assumption set for both the C and the PY engines."""

    def __init__(self, dim: int) -> None:
        self._dim = dim

        self.be_transitions: dict[int, dict[int, BaseRatesProvider]] = {}
        self.res_transitions: dict[int, dict[int, BaseRatesProvider]] = {}

    def add_transition(self, be_or_res: str, from_state: int, to_state: int, rates_provider: BaseRatesProvider) -> "AssumptionSetWrapper":
        """ Add a new transition provider. """

        assert int(from_state) >= 0 and int(from_state) < self._dim, "Unknown state: {}".format(from_state)
        assert int(to_state) >= 0 and int(to_state) < self._dim, "Unknown state: {}".format(to_state)

        if be_or_res.upper() == "BE":
            transitions = self.be_transitions
        elif be_or_res.upper() == "RES":
            transitions = self.res_transitions
        else:
            raise Exception("Argument `be_or_res` must have value `BE` or `RES`, not {}".format(be_or_res.upper()))

        this_trans = transitions.get(from_state)
        if this_trans is None:
            this_trans = {}
            transitions[from_state] = this_trans

        prov_old = this_trans.get(to_state)
        if prov_old is not None:
            logger.warn("Overwriting previously set transitions {}->{}".format(from_state, to_state))
        this_trans[to_state] = rates_provider
        return self

    def _build_matrix(self,
                      transitions: dict[int, dict[int, BaseRatesProvider]]) -> list[list[Optional[BaseRatesProvider]]]:
        # generate a matrix of state transition rates providers
        transition_provider_matrix = []
        for i in range(self._dim):
            new_row: list[Optional[BaseRatesProvider]] = []
            transition_provider_matrix.append(new_row)
            from_dict = transitions.get(i)
            for j in range(self._dim):
                if from_dict is None:
                    new_row.append(None)
                else:
                    new_row.append(from_dict.get(j))

        return transition_provider_matrix
        # return Model(self.states_model, transition_provider_matrix)

    def build_rates_provides_matrix(self, at: AssumptionType) -> list[list[Optional[BaseRatesProvider]]]:

        if at == AssumptionType.BE:
            return self._build_matrix(self.be_transitions)
        elif at == AssumptionType.RES:
            return self._build_matrix(self.res_transitions)
        else:
            raise Exception(f"Unknown assumption type: {at}")

    def build_assumption_set(self, at: AssumptionType) -> actuarial.AssumptionSet:

        if at == AssumptionType.BE:
            transitions = self.be_transitions
        elif at == AssumptionType.RES:
            transitions = self.res_transitions
        else:
            raise Exception(f"Unknown assumption type: {at}")

        acs = actuarial.AssumptionSet(self._dim)

        for from_state, prvdrs_dict in transitions.items():
            if prvdrs_dict is not None:
                for to_state, provider in prvdrs_dict.items():
                    if isinstance(provider, actuarial.ConstantRateProvider):
                        acs.add_provider_const(from_state, to_state, provider)
                    elif isinstance(provider, actuarial.StandardRateProvider):
                        acs.add_provider_std(from_state, to_state, provider)
        return acs

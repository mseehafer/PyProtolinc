
import logging
from abc import ABC, abstractmethod
from typing import Optional, Iterable

from pyprotolinc.assumptions.providers import AssumptionType, BaseRatesProvider
from pyprotolinc.assumptions.providers import AssumptionSetWrapper
from pyprotolinc.models.state_models import AbstractStateModel
from pyprotolinc.portfolio import Portfolio
import pyprotolinc._actuarial as actuarial  # type: ignore

logger = logging.getLogger(__name__)


# _STATE_MODELS = {}


# def register_state_model(cls):

#     check_states(cls)

#     if _STATE_MODELS.get(cls.__name__) is None:
#         _STATE_MODELS[cls.__name__] = cls
#         logger.debug("Registered state model %s", cls.__name__)


# def list_state_models() -> list[type]:
#     """ Returns a list of the currently known state models. """
#     return dict(_STATE_MODELS)

class ModelState:
    """ This class describes the attributes of a Model while running. """
    pass


class Model(ABC):
    """ The model class describes the static parts of a model. """

    MODEL_NAME: str = "META"
    # STATES_MODEL: Optional[type[AbstractStateModel]] = None

    def __init__(self, states_model: type[AbstractStateModel], assumptions_wrapper: AssumptionSetWrapper) -> None:  # states_model, rates_provider_matrix_be, rates_provider_matrix_res):
        self.states_model = states_model
        self._assumptions_wrapper = assumptions_wrapper

        self.known_states = {int(k) for k in self.states_model}

        # # self.states_dim = len(states_model)
        # self.rates_provider_matrix_be = rates_provider_matrix_be
        # self.rates_provider_matrix_res = rates_provider_matrix_res

    @property
    def rates_provider_matrix_be(self) -> list[list[Optional[BaseRatesProvider]]]:
        return self._assumptions_wrapper.build_rates_provides_matrix(AssumptionType.BE)

    @property
    def rates_provider_matrix_res(self) -> list[list[Optional[BaseRatesProvider]]]:
        return self._assumptions_wrapper.build_rates_provides_matrix(AssumptionType.RES)

    @property
    def assumption_set_be(self) -> actuarial.AssumptionSet:
        return self._assumptions_wrapper.build_assumption_set(AssumptionType.BE)

    @property
    def assumption_set_res(self) -> actuarial.AssumptionSet:
        return self._assumptions_wrapper.build_assumption_set(AssumptionType.RES)

    @abstractmethod
    def new_state_instance(self, num_timesteps: int, portfolio: Portfolio, rows_for_state_recorder: Optional[Iterable] = None, *args, **kwargs) -> ModelState:
        # def new_state_instance(self, num_timesteps: int, portfolio, *args, **kwargs) -> ModelState:
        """ Return a new instance of the run-state."""
        raise Exception("Method must be implemented in subclass")

    # is this still needed?
    def get_non_trivial_state_transitions(self, be_or_res: AssumptionType) -> list[tuple[int, int]]:
        """ Returns a list of the non-trivial state transitions. """
        if be_or_res == AssumptionType.BE:
            return self._get_nontrivial_transitions(self.rates_provider_matrix_be)
        elif be_or_res == AssumptionType.RES:
            return self._get_nontrivial_transitions(self.rates_provider_matrix_res)
        else:
            raise Exception(f"Unknown Assumption type: {be_or_res}!")

    def _get_nontrivial_transitions(self, rates_provider_matrix) -> list[tuple[int, int]]:
        # an optimization: we determine which state transitions are non-trivial
        non_trivial_state_transitions = []
        for from_state in self.states_model:
            for to_state in self.states_model:
                if rates_provider_matrix[from_state][to_state] is not None:
                    non_trivial_state_transitions.append((int(from_state), int(to_state)))
        return non_trivial_state_transitions
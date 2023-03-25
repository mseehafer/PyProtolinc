
from enum import IntEnum
import numpy as np
import numpy.typing as npt
from typing import Optional, Iterable, Any
from pyprotolinc.models import Model, ModelState
from pyprotolinc.results import ProbabilityVolumeResults
from pyprotolinc.portfolio import Portfolio

from pyprotolinc.models.state_models import AbstractStateModel
from pyprotolinc.assumptions.providers import AssumptionSetWrapper


class ProjectionState(ModelState):
    """ Hold the current state information of a projection run. """

    def __init__(self, model: Model, num_timesteps: int, portfolio: Portfolio, rows_for_state_recorder: Optional[Iterable[int]] = None) -> None:
        """ Keep references to the original input data and extract the relevant state information. """

        self.model = model
        self.std_output_map = self.model.states_model.to_std_outputs()
        self._portfolio = portfolio

        self.num_records = len(self._portfolio)
        self.num_states = len(model.states_model)
        self.num_timesteps = num_timesteps

        # ages in months
        self.current_ages = self._portfolio.initial_ages.copy()

        # note that this field is only filled when disabled at start, otherwise it's NaN
        self.months_disabled_current_if_at_start = self._portfolio.months_disabled_at_start.copy()

        # the current time or timestep
        self.step = 0

        # The probability states are encoded such that for each state we maintain two
        # columns: The first one (index 0 in the second slot) contains the "in-month-incurred/changes"
        # (or "pre-accept") volume and the second one
        # contains the begin of month volume. At the end of the month
        # the "in-month" changes need to be moved over to the second column
        #
        # -> might need to make that time dependent
        self.probability_states = np.zeros((self.num_states, 2, self.num_records))

        # initialize
        for state in self.model.states_model:
            self.probability_states[state, 1, :] = self._portfolio.initial_states == state

        # monthly movements
        self.probability_movements = np.zeros((self.num_states, self.num_states, self.num_records))

        # The state recorder variable keeps the full state history for some selected policies
        self.rows_for_state_recorder = list() if rows_for_state_recorder is None else list(rows_for_state_recorder)
        self.state_recorder_indexes = None
        self.state_recorder = None

        if self.rows_for_state_recorder:
            self.state_recorder_indexes = np.array(self.rows_for_state_recorder, dtype=np.int32)
            self.state_recorder = np.zeros((1 + self.num_timesteps, self.num_states, len(self.state_recorder_indexes)))

            # check if that assignment works
            self.state_recorder[self.step, :, :] = self.probability_states[:, 1, self.state_recorder_indexes]

    def get_state_probs_bom(self, state: int) -> npt.NDArray[np.float64]:
        return self.probability_states[state, 1, :]

    def get_assumption_cofactors(self) -> tuple[npt.NDArray[np.int32],
                                                npt.NDArray[np.int32],
                                                npt.NDArray[np.int32],
                                                npt.NDArray[np.int32]]:
        """ Return the current values of the risk factors on which
            the assumptions depend. """
        return (self.current_ages, self._portfolio.gender, self._portfolio.smokerstatus, self.months_disabled_current_if_at_start)

    def update_state_matrix(self, transition_ass_timestep: npt.NDArray[np.float64]) -> None:

        # obtain current volumes (sum of in-month and begin-of-month)
        prob_states = self.probability_states.sum(axis=1)      # prob_states is now 2D with dimensions states x records

        # In some sense we want "prob_movements = transition_ass_timestep * prob_states"
        prob_movements = np.einsum('rft,fr->ftr', transition_ass_timestep, prob_states)
        # Here the meaning is as follows:
        #   r - records
        #   f - "from" state
        #   t - "to" state

        # update "in-month-movement totals"
        self.probability_movements += prob_movements

        # update the pre-accept columns adding the timestep-movements
        for state in self.model.states_model:
            self.probability_states[state, 0, :] += prob_movements[:, state, :].sum(axis=0) - prob_movements[state, :, :].sum(axis=0)

        self.step += 1
        if self.rows_for_state_recorder and self.state_recorder is not None and self.state_recorder_indexes is not None:
            self.state_recorder[self.step, :, :] = self.probability_states[:, : self.state_recorder_indexes].sum(axis=1)

    def get_monthly_probability_vol_info(self) -> npt.NDArray[np.float64]:
        """ Return a vector with the portfolio level volumes/movements:
            VOL_ACTIVE, VOL_DIS1, VOL_DIS2, VOL_DEATH, VOL_LAPSED
            MV_ACTIVE_DEATH, MV_ACTIVE_DIS1, MVM_ACT_DIS2, MVM_ACT_LAPSED
            MV_DIS1_DEATH, MV_DIS1_DIS2, MV_DIS1_ACT
            MV_DIS2_DEATH, MV_DIS2_DIS1, MV_DIS2_ACT

            Here the three volume columns are "EOM", the movements are "in-month"
        """
        res = np.zeros(len(ProbabilityVolumeResults))

        for output in ProbabilityVolumeResults:
            mapped_from = self.std_output_map.get(output)
            if mapped_from is None:
                continue
            elif isinstance(mapped_from, IntEnum):
                res[output] = self.probability_states[mapped_from, :].sum()
            else:
                res[output] = self.probability_movements[mapped_from[0], mapped_from[1]].sum()

        return res

    def advance_month(self) -> None:
        """ Required state updates after a month has passed. """

        # adjust the volumes moving the in-month to the end-of-month (=begin of next month) part
        self.probability_states[:, 1] = self.probability_states.sum(axis=1)
        self.probability_states[:, 0] = 0

        # reset the monthly movements
        self.probability_movements[:, :, :] = 0

        self.current_ages += 1
        self.months_disabled_current_if_at_start += 1


class GenericMultiStateModel(Model):
    """ Generic Model that encapsulates the state model and the assumptions."""

    MODEL_NAME = "GenericMultiState"

    def __init__(self, states_model: type[AbstractStateModel], assumptions_wrapper: AssumptionSetWrapper) -> None:
        super().__init__(states_model, assumptions_wrapper)

    def new_state_instance(self, num_timesteps: int, portfolio: Portfolio, rows_for_state_recorder: Optional[Iterable[int]] = None, *args: Any, **kwargs: Any) -> ProjectionState:
        return ProjectionState(self, num_timesteps, portfolio, rows_for_state_recorder)

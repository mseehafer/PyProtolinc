
from enum import IntEnum
import numpy as np
from pyprotolinc.models import Model, ModelState
from pyprotolinc.results import ProbabilityVolumeResults

# from pyprotolinc.models.model_disability_multistate import MultiStateDisabilityStates
from pyprotolinc.models import _STATE_MODELS


class GenericMultiStateModel(Model):

    MODEL_NAME = "GenericMultiState"
    STATES_MODEL = None

    def __init__(self, rates_provider_matrix_be, rates_provider_matrix_res):
        super().__init__(self.STATES_MODEL, rates_provider_matrix_be, rates_provider_matrix_res)

    def new_state_instance(self, num_timesteps, portfolio, rows_for_state_recorder=None):
        return ProjectionState(self, num_timesteps, portfolio, rows_for_state_recorder)


def adjust_state_for_generic_model(model, state_model_name):
    """ For the Generic model the StateModel must be injected. """
    if isinstance(model, GenericMultiStateModel):
        for stateclass_name, state_class in _STATE_MODELS.items():
            if stateclass_name.upper() == state_model_name.upper():
                model.states_model = state_class
                model.known_states = {int(k) for k in model.states_model}
                break


class ProjectionState(ModelState):
    """ Hold the current state information of a projection run. """

    def __init__(self, model, num_timesteps, portfolio, rows_for_state_recorder=None):
        """ Keep references to the original input data and extract the relevant state information. """

        self.model = model
        self.std_output_map = self.model.states_model.to_std_outputs()
        self._portfolio = portfolio

        self.num_records = len(self._portfolio)
        self.num_states = len(model.states_model)
        self.num_timesteps = num_timesteps

        # ages in months
        self.current_ages = self._portfolio.initial_ages.copy()

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
        self.rows_for_state_recorder = list(rows_for_state_recorder)
        self.state_recorder_indexes = None
        self.state_recorder = None

        if self.rows_for_state_recorder:
            self.state_recorder_indexes = np.array(self.rows_for_state_recorder, dtype=np.int32)
            self.state_recorder = np.zeros((1 + self.num_timesteps, self.num_states, len(self.state_recorder_indexes)))

            # check if that assignment works
            self.state_recorder[self.step, :, :] = self.probability_states[:, 1, self.state_recorder_indexes]

    def get_state_probs_bom(self, state):
        return self.probability_states[state, 1, :]

    def get_assumption_cofactors(self):
        """ Return the current values of the risk factors on which
            the assumptions depend. """
        return (self.current_ages, self._portfolio.gender)

    def update_state_matrix(self, transition_ass_timestep):

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
        if self.rows_for_state_recorder:
            self.state_recorder[self.step, :, :] = self.probability_states[:, : self.state_recorder_indexes].sum(axis=1)

    def get_monthly_probability_vol_info(self):
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

    def advance_month(self):
        """ Required state updates after a month has passed. """

        # adjust the volumes moving the in-month to the end-of-month (=begin of next month) part
        self.probability_states[:, 1] = self.probability_states.sum(axis=1)
        self.probability_states[:, 0] = 0

        # reset the monthly movements
        self.probability_movements[:, :, :] = 0

        self.current_ages += 1

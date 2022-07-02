
from enum import IntEnum, unique
import numpy as np

from protolinc.models import Model, ModelState
from protolinc.results import ProbabilityVolumeResults


@unique
class AnnuityRunoffStates(IntEnum):
    """ A state model consisting of two states:
        - DIS (=0) representing the annuity phase
        - DEATH (=1)
    """
    DIS1 = 0    # the "annuitant state"
    DEATH = 1   # the death state

    @classmethod
    def to_std_outputs(cls):
        return {
            # ProbabilityVolumeResults.VOL_ACTIVE: None,
            ProbabilityVolumeResults.VOL_DIS1: cls.DIS1,
            # ProbabilityVolumeResults.VOL_DIS2: None,
            ProbabilityVolumeResults.VOL_DEATH: cls.DEATH,
            # ProbabilityVolumeResults.VOL_LAPSED: None,

            # ProbabilityVolumeResults.MV_ACTIVE_DEATH: (None, None),
            # ProbabilityVolumeResults.MV_ACTIVE_DIS1: (None, None),
            # ProbabilityVolumeResults.MV_ACT_DIS2: (None, None),
            # ProbabilityVolumeResults.MV_ACT_LAPSED: (None, None),

            ProbabilityVolumeResults.MV_DIS1_DEATH: (cls.DIS1, cls.DEATH),
            # ProbabilityVolumeResults.MV_DIS1_DIS2: (None, None),
            # ProbabilityVolumeResults.MV_DIS1_ACT: (None, None),

            # ProbabilityVolumeResults.MV_DIS2_DEATH: (None, None),
            # ProbabilityVolumeResults.MV_DIS2_DIS1: (None, None),
            # ProbabilityVolumeResults.MV_DIS2_ACT: (None, None),
        }


class AnnuityRunoffModel(Model):

    MODEL_NAME = "AnnuityRunoff"
    STATES_MODEL = AnnuityRunoffStates

    def __init__(self, rates_provider_matrix_be, rates_provider_matrix_res):
        super().__init__(self.STATES_MODEL, rates_provider_matrix_be, rates_provider_matrix_res)

    def new_state_instance(self, num_timesteps, portfolio, rows_for_state_recorder=None):
        return AnnuityProjectionState(self, num_timesteps, portfolio, rows_for_state_recorder)


class AnnuityProjectionState(ModelState):
    """ Hold the current state information of a projection run. """

    def __init__(self, model, num_timesteps, portfolio, rows_for_state_recorder=None):
        """ Keep references to the original input data and extract the relevant state information. """

        self.model = model
        self._portfolio = portfolio

        self.num_records = len(self._portfolio)
        self.num_states = len(model.states_model)
        self.num_timesteps = num_timesteps

        # ages in months
        self.current_ages = self._portfolio.initial_ages.copy()

        # the current time or timestep
        self.step = 0

        # for each time and each record we store the probability that it is in a certain state
        # the state matrix is indexed by time where time=0 is when the projection starts
        self.state_matrix = np.zeros((self.num_records, self.num_states))

        # everything above seems generic and could be part of a superclass
        self.state_matrix[np.arange(self.num_records), self._portfolio.initial_states] = 1

        # New and more flexible (and more verbose) state concept: Each
        # state is encoded by a matrix with (for now) two columns. The first
        # one contains the "in-month-incurred/changes" (or "pre-accept") volume and the second one
        # contains the begin of month volume. At the end of the month
        # the "in-month" changes need to be moved over to the second column
        # It is possible to have further columns to encode things like waiting periods
        self.prob_state_active = np.zeros((self.num_records, 2))     # just a dummy, remains constant
        self.prob_state_dis1 = np.zeros((self.num_records, 2))
        self.prob_state_dis2 = np.zeros((self.num_records, 2))       # just a dummy, remains constant
        self.prob_state_death = np.zeros((self.num_records, 2))
#        self.prob_state_lapsed = np.zeros((self.num_records, 2))

        # TODO: in the next group we have a hard dependency on the state model

        # initialize
#        self.prob_state_active[:, 1] = self._portfolio.initial_MultiStateDisabilityStates == MultiStateDisabilityStates.ACTIVE
        self.prob_state_dis1[:, 1] = self._portfolio.initial_states == AnnuityRunoffStates.DIS1
#        self.prob_state_dis2[:, 1] = self._portfolio.initial_MultiStateDisabilityStates == MultiStateDisabilityStates.DIS2
        self.prob_state_death[:, 1] = self._portfolio.initial_states == AnnuityRunoffStates.DEATH
#        self.prob_state_lapsed[:, 1] = self._portfolio.initial_MultiStateDisabilityStates == MultiStateDisabilityStates.LAPSED

        # monthly movements
        # active -> *
#        self.monthly_prob_mvm_active_death = np.zeros(self.num_records)
#        self.monthly_prob_mvm_active_lapsed = np.zeros(self.num_records)
#        self.monthly_prob_mvm_active_dis1 = np.zeros(self.num_records)
#        self.monthly_prob_mvm_active_dis2 = np.zeros(self.num_records)
        #  dis1 -> *
        self.monthly_prob_mvm_dis1_death = np.zeros(self.num_records)
#        self.monthly_prob_mvm_dis1_active = np.zeros(self.num_records)
#        self.monthly_prob_mvm_dis1_dis2 = np.zeros(self.num_records)
        # dis2 -> *
#        self.monthly_prob_mvm_dis2_death = np.zeros(self.num_records)
#        self.monthly_prob_mvm_dis2_active = np.zeros(self.num_records)
#        self.monthly_prob_mvm_dis2_dis1 = np.zeros(self.num_records)

        # The state recorder variable keeps the full state history for some selected policies
        self.rows_for_state_recorder = list(rows_for_state_recorder)
        self.state_recorder_indexes = None
        self.state_recorder = None

        # TODO another hard dependency incl. a remapping that was needed

        if self.rows_for_state_recorder:
            self.state_recorder_indexes = np.array(self.rows_for_state_recorder, dtype=np.int32)
            self.state_recorder = np.zeros((1 + self.num_timesteps, len(self.state_recorder_indexes), self.num_states))
#           self.state_recorder[self.step, :, 0] = self.prob_state_active[self.state_recorder_indexes, 1]
            self.state_recorder[self.step, :, 0] = self.prob_state_dis1[self.state_recorder_indexes, 1]
#            self.state_recorder[self.step, :, 2] = self.prob_state_dis2[self.state_recorder_indexes, 1]
            self.state_recorder[self.step, :, 1] = self.prob_state_death[self.state_recorder_indexes, 1]
#            self.state_recorder[self.step, :, 4] = self.prob_state_lapsed[self.state_recorder_indexes, 1]

    def get_payment_state_probs(self):
        return (
            self.prob_state_active.transpose(),
            self.prob_state_dis1.transpose(),
            self.prob_state_dis2.transpose(),
        )

    def get_assumption_cofactors(self):
        """ Return the current values of the risk factors on which
            the assumptions depend. """
        return (self.current_ages, self._portfolio.gender)

    def update_state_matrix(self, transition_ass_timestep):

        # obtain current volumes (sum of in-month and begin-of-month)
#        prob_state_active = self.prob_state_active.sum(axis=1)
        prob_state_dis1 = self.prob_state_dis1.sum(axis=1)
#        prob_state_dis2 = self.prob_state_dis2.sum(axis=1)
        # prob_state_death = self.prob_state_death.sum(axis=1)
        # prob_state_lapsed = self.prob_state_lapsed.sum(axis=1)

        # state migration probabilities of the calculation step
        # active -> *
#        prob_mvm_active_death = transition_ass_timestep[:, MultiStateDisabilityStates.ACTIVE, MultiStateDisabilityStates.DEATH] * prob_state_active
#        prob_mvm_active_lapsed = transition_ass_timestep[:, MultiStateDisabilityStates.ACTIVE, MultiStateDisabilityStates.LAPSED] * prob_state_active
#        prob_mvm_active_dis1 = transition_ass_timestep[:, MultiStateDisabilityStates.ACTIVE, MultiStateDisabilityStates.DIS1] * prob_state_active
#        prob_mvm_active_dis2 = transition_ass_timestep[:, MultiStateDisabilityStates.ACTIVE, MultiStateDisabilityStates.DIS2] * prob_state_active

        # print(transition_ass_timestep[:, MultiStateDisabilityStates.ACTIVE, MultiStateDisabilityStates.DEATH],
        #       transition_ass_timestep[:, MultiStateDisabilityStates.ACTIVE, MultiStateDisabilityStates.LAPSED],
        #       prob_mvm_active_lapsed)

        # dis1 -> *
        prob_mvm_dis1_death = transition_ass_timestep[:, self.model.states_model.DIS1, self.model.states_model.DEATH] * prob_state_dis1
#        prob_mvm_dis1_active = transition_ass_timestep[:, MultiStateDisabilityStates.DIS1, MultiStateDisabilityStates.ACTIVE] * prob_state_dis1
#        prob_mvm_dis1_dis2 = transition_ass_timestep[:, MultiStateDisabilityStates.DIS1, MultiStateDisabilityStates.DIS2] * prob_state_dis1
        # dis2 -> *
#        prob_mvm_dis2_death = transition_ass_timestep[:, MultiStateDisabilityStates.DIS2, MultiStateDisabilityStates.DEATH] * prob_state_dis2
#        prob_mvm_dis2_active = transition_ass_timestep[:, MultiStateDisabilityStates.DIS2, MultiStateDisabilityStates.ACTIVE] * prob_state_dis2
#        prob_mvm_dis2_dis1 = transition_ass_timestep[:, MultiStateDisabilityStates.DIS2, MultiStateDisabilityStates.DIS1] * prob_state_dis2

        # update "in-month-movement totals"
#        self.monthly_prob_mvm_active_death += prob_mvm_active_death
#        self.monthly_prob_mvm_active_lapsed += prob_mvm_active_lapsed
#        self.monthly_prob_mvm_active_dis1 += prob_mvm_active_dis1
#        self.monthly_prob_mvm_active_dis2 += prob_mvm_active_dis2
        #  dis1 -> *
        self.monthly_prob_mvm_dis1_death += prob_mvm_dis1_death
#        self.monthly_prob_mvm_dis1_active += prob_mvm_dis1_active
#        self.monthly_prob_mvm_dis1_dis2 += prob_mvm_dis1_dis2
        # dis2 -> *
#        self.monthly_prob_mvm_dis2_death += prob_mvm_dis2_death
#        self.monthly_prob_mvm_dis2_active += prob_mvm_dis2_active
#        self.monthly_prob_mvm_dis2_dis1 += prob_mvm_dis2_dis1

        # update the pre-accept columns adding the timestep-movements
#        self.prob_state_active[:, 0] += prob_mvm_dis1_active + prob_mvm_dis2_active - prob_mvm_active_death \
#            - prob_mvm_active_lapsed - prob_mvm_active_dis1 - prob_mvm_active_dis2

        self.prob_state_dis1[:, 0] += -prob_mvm_dis1_death

#        self.prob_state_dis2[:, 0] += prob_mvm_active_dis2 + prob_mvm_dis1_dis2 \
#            - prob_mvm_dis2_death - prob_mvm_dis2_active - prob_mvm_dis2_dis1

        self.prob_state_death[:, 0] += prob_mvm_dis1_death

#        self.prob_state_lapsed[:, 0] += prob_mvm_active_lapsed

        # # the unified way
        # self.state_matrix = np.einsum('ij,ijk->ik', self.state_matrix, transition_ass_timestep)

        self.step += 1
        if self.rows_for_state_recorder:
            # self.state_recorder[self.step, :, 0] = self.prob_state_active[self.state_recorder_indexes, :].sum(axis=1)
            self.state_recorder[self.step, :, 0] = self.prob_state_dis1[self.state_recorder_indexes, :].sum(axis=1)
            # self.state_recorder[self.step, :, 2] = self.prob_state_dis2[self.state_recorder_indexes, :].sum(axis=1)
            self.state_recorder[self.step, :, 1] = self.prob_state_death[self.state_recorder_indexes, :].sum(axis=1)
            # self.state_recorder[self.step, :, 4] = self.prob_state_lapsed[self.state_recorder_indexes, :].sum(axis=1)

    def get_monthly_probability_vol_info(self):
        """ Return a vector with the portfolio level volumes/movements:
            VOL_ACTIVE, VOL_DIS1, VOL_DIS2, VOL_DEATH, VOL_LAPSED
            MV_ACTIVE_DEATH, MV_ACTIVE_DIS1, MVM_ACT_DIS2, MVM_ACT_LAPSED
            MV_DIS1_DEATH, MV_DIS1_DIS2, MV_DIS1_ACT
            MV_DIS2_DEATH, MV_DIS2_DIS1, MV_DIS2_ACT

            Here the three volume columns are "EOM", the movements are "in-month"
        """
        res = np.zeros(15)

#        res[ProbabilityVolumeResults.VOL_ACTIVE] = self.prob_state_active.sum()
        res[ProbabilityVolumeResults.VOL_DIS1] = self.prob_state_dis1.sum()
#        res[ProbabilityVolumeResults.VOL_DIS2] = self.prob_state_dis2.sum()
        res[ProbabilityVolumeResults.VOL_DEATH] = self.prob_state_death.sum()
#        res[ProbabilityVolumeResults.VOL_LAPSED] = self.prob_state_lapsed.sum()

#        res[ProbabilityVolumeResults.MV_ACTIVE_DEATH] = self.monthly_prob_mvm_active_death.sum()
#        res[ProbabilityVolumeResults.MV_ACTIVE_DIS1] = self.monthly_prob_mvm_active_dis1.sum()
#        res[ProbabilityVolumeResults.MV_ACT_DIS2] = self.monthly_prob_mvm_active_dis2.sum()
#        res[ProbabilityVolumeResults.MV_ACT_LAPSED] = self.monthly_prob_mvm_active_lapsed.sum()

        res[ProbabilityVolumeResults.MV_DIS1_DEATH] = self.monthly_prob_mvm_dis1_death.sum()
#        res[ProbabilityVolumeResults.MV_DIS1_DIS2] = self.monthly_prob_mvm_dis1_dis2.sum()
#        res[ProbabilityVolumeResults.MV_DIS1_ACT] = self.monthly_prob_mvm_dis1_active.sum()

#        res[ProbabilityVolumeResults.MV_DIS2_DEATH] = self.monthly_prob_mvm_dis2_death.sum()
#        res[ProbabilityVolumeResults.MV_DIS2_DIS1] = self.monthly_prob_mvm_dis2_dis1.sum()
#        res[ProbabilityVolumeResults.MV_DIS2_ACT] = self.monthly_prob_mvm_dis2_active.sum()

        return res

    def advance_month(self):
        """ Required state updates after a month has passed. """

        # adjust the volumes moving the in-month to theend-of-month (=begin of next month) part
#        self.prob_state_active[:, 1] = self.prob_state_active.sum(axis=1)
        self.prob_state_dis1[:, 1] = self.prob_state_dis1.sum(axis=1)
#        self.prob_state_dis2[:, 1] = self.prob_state_dis2.sum(axis=1)
        self.prob_state_death[:, 1] = self.prob_state_death.sum(axis=1)
#        self.prob_state_lapsed[:, 1] = self.prob_state_lapsed.sum(axis=1)

#        self.prob_state_active[:, 0] = 0
        self.prob_state_dis1[:, 0] = 0
#        self.prob_state_dis2[:, 0] = 0
        self.prob_state_death[:, 0] = 0
#        self.prob_state_lapsed[:, 0] = 0

        # reset the monthly movements
        #  active -> *
#        self.monthly_prob_mvm_active_death[:] = 0
#        self.monthly_prob_mvm_active_lapsed[:] = 0
#        self.monthly_prob_mvm_active_dis1[:] = 0
#        self.monthly_prob_mvm_active_dis2[:] = 0
        #  dis1 -> *
        self.monthly_prob_mvm_dis1_death[:] = 0
#        self.monthly_prob_mvm_dis1_active[:] = 0
#        self.monthly_prob_mvm_dis1_dis2[:] = 0
        # dis2 -> *
#        self.monthly_prob_mvm_dis2_death[:] = 0
#        self.monthly_prob_mvm_dis2_active[:] = 0
#        self.monthly_prob_mvm_dis2_dis1[:] = 0

        self.current_ages += 1

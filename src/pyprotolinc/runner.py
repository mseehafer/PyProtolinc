import logging
import numpy as np
from pyprotolinc.assumptions.providers import AssumptionTimestepAdjustment
from pyprotolinc import MAX_AGE
from pyprotolinc.results import ProbabilityVolumeResults, CfNames
from pyprotolinc.assumptions.providers import AssumptionType

logger = logging.getLogger(__name__)


class TimeAxis:

    def __init__(self, portfolio_date, total_num_months):
        portfolio_year, portfolio_month = portfolio_date.year, portfolio_date.month

        # generate a time axis starting at the beginning of the month of the portfolio date
        _zero_based_months_tmp = (portfolio_month - 1) + np.arange(total_num_months + 1)
        self.months = _zero_based_months_tmp % 12 + 1
        self.years = portfolio_year + _zero_based_months_tmp // 12
        self.quarters = (self.months - 1) // 3 + 1

    def __len__(self):
        return len(self.months)


class Projector:
    """ The projection engine. """

    def __init__(self, run_config, portfolio, model, proj_state, product,
                 rows_for_state_recorder=None, chunk_index=1, num_chunks=1):

        self.run_config = run_config

        self.chunk_index = chunk_index
        self.num_chunks = num_chunks

        logger.debug("Creating a <Projector> object for chunk %s of %s",
                     self.chunk_index, self.num_chunks)

        # Shouldn't the projection state come from the model?
        self.proj_state = proj_state
        self.model = model

        self.product = product

        assert self.model.states_model == product.STATES_MODEL

        self.sum_insured = portfolio.sum_insured

        self.total_num_months = 12 * self.run_config.years_to_simulate
        self.month_count = 0

        self.time_axis = TimeAxis(portfolio.portfolio_date, self.total_num_months)

        # criterion for early termination: if all results are zero for some number of months
        # the run can be terminated
        self.number_all_zero_results = 0
        self.TERMINATE_AFTER_X_ZERO_MONTHS = 13

        # A three dimensional tensor that contains the applicable assumptions
        # on a yearly grid
        #    Indexes:
        #       * row in the portfolio
        #       * 'from' state
        #       * 'to' state
        self.applicable_yearly_assumptions_be = np.zeros((self.proj_state.num_records, self.proj_state.num_states, self.proj_state.num_states))
        self.applicable_yearly_assumptions_res = np.zeros((self.proj_state.num_records, self.proj_state.num_states, self.proj_state.num_states))

        # an optimization: we determine which state transitions are non-trivial
        self.non_trivial_state_transitions_be = self.model.get_non_trivial_state_transitions(AssumptionType.BE)
        self.non_trivial_state_transitions_res = self.model.get_non_trivial_state_transitions(AssumptionType.RES)

        # a timestep adjustment that converts yearly assumptions to smaller steps
        self.timestep_adjuster = AssumptionTimestepAdjustment(self.run_config.timestep_duration,
                                                              self.proj_state.num_states,
                                                              self.proj_state.num_records)

        # the timestep adjuster for the reservers will always operate monthly
        self.timestep_adjuster_monthly = AssumptionTimestepAdjustment(1.0 / 12.0,
                                                                      self.proj_state.num_states,
                                                                      self.proj_state.num_records)

        # container for the monthly payments
        self.monthly_payment_matrix = np.zeros((self.proj_state.num_records, len(CfNames)))

        # container for the monthly reserving transition assumptions which are saved in the first
        # pass so that in a second backwards pass the reserves can be obatined recursively
        # TODO: Here and elsewhere we should put the records(=insured) dimension to the end
        self.transition_ass_monthly_res_with_time = np.zeros((len(self.time_axis),
                                                             self.proj_state.num_records,
                                                             self.proj_state.num_states,
                                                             self.proj_state.num_states))

        # container for the monthly accumulated BE state probabilities
        self.probability_states_with_time = np.zeros((len(self.time_axis),
                                                      self.proj_state.num_states,
                                                      self.proj_state.num_records))

        # store ncf-results for selected policies
        self.rows_for_payments_recorder = list(rows_for_state_recorder)
        if self.rows_for_payments_recorder:
            self.payments_recorder_indexes = np.array(self.rows_for_payments_recorder, dtype=np.int32)
            self.payments_recorder = np.zeros((1 + self.total_num_months, len(self.payments_recorder_indexes), self.proj_state.num_states))

        # container for the cash flow result
        self.ncf_portfolio = np.zeros((self.total_num_months + 1, len(CfNames)))

        # Container for the probability movements
        self.probability_movements = np.zeros((self.total_num_months + 1, len(ProbabilityVolumeResults)))

        # here we obtain the whole conditional payment stream upfront
        self.cond_bom_payment_dict = self.product.get_bom_payments(self.time_axis)
        self.cond_eom_payment_dict = self.product.get_state_transition_payments(self.time_axis)

        # contractual state transitions originating from the product and the insured state
        # rather than actuarial assumptions
        self.contractual_state_transitions = self.product.contractual_state_transitions(self.time_axis)

        # tensor that is supposed to hold transitions from contractual state changes in the current period
        # of the time-loop
        self.contractual_transition_ts_period = np.zeros((self.proj_state.num_records,
                                                         self.proj_state.num_states,
                                                         self.proj_state.num_states))

        # this container of structure (time x state x insured) will hold reserves
        # as at the begin of period
        self.reserves_bom = None

    def update_state(self, transition_ass_timestep):
        self.proj_state.update_state_matrix(transition_ass_timestep)

    def select_applicable_base_assumptions(self, ages, genders, calendaryear):
        """ Construct a three dimensional tensor that contains the base assumptions.
            Indexes:
              * row in the portfolio
              * 'from' state
              * 'to' state
        """

        # get BE assumptions
        for (from_state, to_state) in self.non_trivial_state_transitions_be:
            provider = self.model.rates_provider_matrix_be[from_state][to_state]
            sel_ass = provider.get_rates(length=len(ages),
                                         age=ages,
                                         gender=genders,
                                         calendaryear=calendaryear)
            self.applicable_yearly_assumptions_be[:, from_state, to_state] = sel_ass

        # get RES assumptions
        for (from_state, to_state) in self.non_trivial_state_transitions_res:
            provider = self.model.rates_provider_matrix_res[from_state][to_state]
            sel_ass = provider.get_rates(length=len(ages),
                                         age=ages,
                                         gender=genders,
                                         calendaryear=calendaryear)
            self.applicable_yearly_assumptions_res[:, from_state, to_state] = sel_ass

    def calc_payments_bom(self):
        """ Calculate the payments based on the state information which should be
            as at the begin of the month. """

        self.monthly_payment_matrix[:] = 0
        for st in self.model.states_model:
            state_payments = self.cond_bom_payment_dict.get(st)
            if state_payments is None:
                continue
            for cfname, payment in state_payments:
                self.monthly_payment_matrix[:, cfname] += payment[:, self.month_count] * self.proj_state.get_state_probs_bom(st)

        if self.rows_for_payments_recorder:
            self.payments_recorder[self.month_count, :, :] = self.monthly_payment_matrix[self.payments_recorder_indexes, :]

        # self.ncf_portfolio[self.month_count, :] = self.monthly_payment_matrix.sum(axis=0)

    def calc_payments_eom(self):
        """ Calculate the payments based on the state information which should be
            as at the end of the month (LS claims, potentially end of period reserves). """

        # calculate the payments due at end of month like LS benefits
        if self.cond_eom_payment_dict:
            for from_state in self.model.states_model:
                for to_state in self.model.states_model:
                    state_transition_payments = self.cond_eom_payment_dict.get((from_state, to_state))
                    if state_transition_payments is None:
                        continue
                    for cfname, payment in state_transition_payments:
                        self.monthly_payment_matrix[:, cfname] += payment[:, self.month_count] * self.proj_state.probability_movements[from_state, to_state, :]

        # sum up the payments
        self.ncf_portfolio[self.month_count, :] = self.monthly_payment_matrix.sum(axis=0)

        # extract volumes and movements at EOM
        self.probability_movements[self.month_count, :] = self.proj_state.get_monthly_probability_vol_info()

        # termination criterion: check "all is zero" with a little bit of tolerance
        if np.absolute(self.ncf_portfolio[self.month_count, :]).sum() < 0.001:
            self.number_all_zero_results += 1
        else:
            self.number_all_zero_results = 0

    def calculate_reserves(self):
        """ Reserve loop: Calculated the reserves using reserving assumptions weighted by BE assumptions. """

        # obtain the discount factor
        reserving_interest = 0.0  # 0.04   # Placeholder for now!
        monthly_discount_factor = (1.0 + reserving_interest)**(-1.0 / 12.0)

        reserves_bom_by_insured = np.zeros((len(self.time_axis),
                                            self.proj_state.num_states,
                                            self.proj_state.num_records))

        # the vector of reserves conditional on being in the respective state
        reserves_last_month_conditional = np.zeros((self.proj_state.num_states, self.proj_state.num_records))

        # NCF@BOM/EOM per each state/state-change for the current period
        cfs_bom_per_state = np.zeros((self.proj_state.num_states, self.proj_state.num_records))
        cf_eom_per_state_change = np.zeros((self.proj_state.num_states, self.proj_state.num_states, self.proj_state.num_records))

        while self.month_count > 0:

            # get the CF@BOM
            cfs_bom_per_state[:] = 0
            for st in self.model.states_model:
                state_payments = self.cond_bom_payment_dict.get(st)
                if state_payments is None:
                    continue
                for _, payment in state_payments:   # assume for now that all cash flows are `reserve relevant`
                    cfs_bom_per_state[st, :] -= payment[:, self.month_count]   # inversion of sign for reserve calculation intended

            # get the CF@EOM
            # TODO: NOT YET TESTED
            cf_eom_per_state_change[:] = 0
            if self.cond_eom_payment_dict:
                for from_state in self.model.states_model:
                    for to_state in self.model.states_model:
                        state_transition_payments = self.cond_eom_payment_dict.get((from_state, to_state))
                        if state_transition_payments is None:
                            continue
                        for cfname, payment in state_transition_payments:
                            cf_eom_per_state_change[from_state, to_state, :] -= payment[:, self.month_count]

            # Explanation of IDEA first: recursive calculation equation along the line of
            # reserves_bom[self.month_count, :] = CF@BOM|state=j + D * ( \sum_{states k}) p^{res, insured=i}_{j->k} (CF@EOM|state=j) + Res_bom(t+1)|state=k)

            # first we determine the amounts needed bases on the transitions
            # the structure of transition_amounts is (from_state, to_state, insured), the broadcasting adds the reserve needed in the "to_state" to the payments
            transition_amounts = (cf_eom_per_state_change) + reserves_last_month_conditional   # here we reflect that reserves are not in P/L sign logic

            # the transition amounts ar emultiplied with the transition probabilities
            # the probabilities with time fixed have the strcuture(insured(r), from_state(f), to_state(t))
            cond_res_eom = np.einsum('rft,ftr->fr', self.transition_ass_monthly_res_with_time[self.month_count, :], transition_amounts)

            reserves_last_month_conditional[:] = cfs_bom_per_state + monthly_discount_factor * cond_res_eom

            # store the "probability weighted" reserve
            reserves_bom_by_insured[self.month_count, :] = reserves_last_month_conditional[:] * self.probability_states_with_time[self.month_count, :]

            self.month_count -= 1

        return reserves_bom_by_insured

    def get_results_dict(self):
        data = {
            "YEAR": self.time_axis.years,
            "QUARTER": self.time_axis.quarters,
            "MONTH": self.time_axis.months
        }

        for cfn in CfNames:
            data[cfn.name] = self.ncf_portfolio[:, cfn]

        # add the reserves
        for st in self.model.states_model:
            data["RESERVE_BOM({})".format(st.name)] = self.reserves_bom[:, st]

        # add the probability movements
        for vol_prob_res in ProbabilityVolumeResults:
            data[vol_prob_res.name] = self.probability_movements[:, vol_prob_res]

        # # maybe do this rather at the end of the calculation
        # # extend the state probabilities until the result vector length
        # for vol_prob_res in ProbabilityVolumeResults:
        #     if vol_prob_res.name.startswith("VOL_"):
        #         data[vol_prob_res.name] = fill_with_last_nonzero_value(data[vol_prob_res.name])

        return data

    def calculate_contractual_transition_tensor(self, state_transitions_current_month):
        """ Expand the contractual transition data structure into a full transition tensor.
        """

        # reset values
        self.contractual_transition_ts_period[:] = 0

        num_states = self.contractual_transition_ts_period.shape[1]

        #  set diagonal elements so that we now have ad "id" state transition tensor for each record
        for k in range(num_states):
            self.contractual_transition_ts_period[:, k, k] = 1

        # adjust for the state transitions
        for from_state, to_state, insured_selector in state_transitions_current_month:
            # convert selector to bool
            insured_selector = insured_selector.astype(bool, copy=False)

            for st in range(num_states):
                self.contractual_transition_ts_period[insured_selector, from_state, st] = st == to_state

    def run(self):
        # projection loop over time
        _terminate = False
        _ages_last_month = -np.ones(self.proj_state.num_records)  # iniate with negative values
        _calendaryear_last_month = -np.ones(self.proj_state.num_records)

        # get initial volumes
        self.probability_movements[0, :] = self.proj_state.get_monthly_probability_vol_info()

        logger.debug("Starting the simulation for chunk %s of %s", self.chunk_index, self.num_chunks)
        for yr in range(1, 1 + self.run_config.years_to_simulate):

            if _terminate:
                break

            # logger.debug("Calculating projection year %s.", yr)

            for month in range(1, 13):
                if _terminate:
                    break

                self.month_count += 1

                # logger.debug("Calculating timestep {}/{}".format(yr, month))

                # save the accumulated state probabilities at BOM according to the BE assumptions
                self.probability_states_with_time[self.month_count, :] = self.proj_state.probability_states[:, 1, :]

                # calculate the NCF due at the beginning of the current month
                self.calc_payments_bom()

                # update the yearly assumptions

                # get risk factors
                ages_months, genders = self.proj_state.get_assumption_cofactors()
                ages = np.minimum(ages_months // 12, MAX_AGE)  # age selection depends on completed years
                calendaryear = np.ones(len(ages), dtype=np.int32) * self.time_axis.years[self.month_count]

                # check if the risk factors have changed and refresh the assumptions in this case
                assumption_update_required = not (np.array_equal(ages, _ages_last_month) and np.array_equal(calendaryear, _calendaryear_last_month))

                if assumption_update_required:
                    self.select_applicable_base_assumptions(ages, genders, calendaryear)

                    # TODO: apply assumption modifiers on policy level as found in the portfolio data

                    # adjust assumptions for the length of the timestep
                    transition_ass_timestep_be = self.timestep_adjuster.adjust_simple(self.applicable_yearly_assumptions_be)
                    transition_ass_timestep_res_ts = self.timestep_adjuster_monthly.adjust_simple(self.applicable_yearly_assumptions_res)
                    # Note: for this optimization to work these variables must not be changed elsewhere

                    assert self.run_config.steps_per_month == 1, "For reserves the update works only for monthly steps"
                else:
                    # nothing to do:
                    # transition_ass_timestep_be and transition_ass_timestep_res_ts
                    # are still valid
                    pass

                # could maybe be moved to "if"-branch above
                _ages_last_month[:] = ages
                _calendaryear_last_month[:] = calendaryear

                # perform the state update for the month
                for step in range(1, 1 + self.run_config.steps_per_month):
                    # logger.debug("Calculating timestep {}/{}/{}".format(yr, month, step))
                    # state transition
                    self.update_state(transition_ass_timestep_be)
                    # for reserves we might need to calculate powers of the transition tensor in this loop
                    # to make this work

                # apply contractual state transitions after the regular state transitions (BE and RES)
                state_transitions_current_month = [(from_state, to_state, state_transitions[:, self.month_count])
                                                   for from_state, to_state, state_transitions in
                                                   self.contractual_state_transitions]

                # Check if state transitions are applicable this month
                if np.array([m[2].sum() for m in state_transitions_current_month]).sum() > 0:

                    # this call will update the instance variable self.contractual_transition_ts_period
                    self.calculate_contractual_transition_tensor(state_transitions_current_month)

                    # for BE:
                    self.update_state(self.contractual_transition_ts_period)

                    # for reserves we build an updated transition matrix which we store
                    self.transition_ass_monthly_res_with_time[self.month_count, :] = np.einsum('rij,rjk->rik', transition_ass_timestep_res_ts, self.contractual_transition_ts_period)
                else:

                    # save unadjusted reserving assumptions in any case
                    self.transition_ass_monthly_res_with_time[self.month_count, :] = transition_ass_timestep_res_ts

                # at end of the month:
                # the next call also counts the number_all_zero_cashflows which are used to decide about the termination
                self.calc_payments_eom()

                self.proj_state.advance_month()

                # check early termination
                if self.number_all_zero_results >= self.TERMINATE_AFTER_X_ZERO_MONTHS:
                    # TODO: termination flag should only be set if no future new business is still expected
                    _terminate = True
                    logging.info("Runner for chunk %s: Early termination in %s/%s",
                                 self.chunk_index,
                                 self.time_axis.months[self.month_count],
                                 self.time_axis.years[self.month_count])
                    break

        # calculate the reserves
        logger.debug("Starting backwards loop to calculate the reserves for chunk %s of %s", self.chunk_index, self.num_chunks)
        reserves_bom_by_insured = self.calculate_reserves()
        # this will be of the structure time x state
        self.reserves_bom = reserves_bom_by_insured.sum(axis=2)

        # in case of early termination extend the state probabilities until the result vector length
        if _terminate:
            for vol_prob_res in ProbabilityVolumeResults:
                if vol_prob_res.name.startswith("VOL_"):
                    self.probability_movements[:, vol_prob_res] = fill_with_last_nonzero_value(self.probability_movements[:, vol_prob_res])


def fill_with_last_nonzero_value(x: np.ndarray):
    """ Return a vector which consists of a copy of x but with all trailing zeros
        overwritten by with the last non-zero element in the vector."""
    y = x.copy()
    nz = np.nonzero(y)[0]
    if len(nz) > 0:
        y[nz.max()+1:] = y[nz.max()]
    return y

import logging
from typing import Any, Optional


import numpy as np
import numpy.typing as npt

from pyprotolinc.assumptions.providers import AssumptionTimestepAdjustment
from pyprotolinc import MAX_AGE, RunConfig
from pyprotolinc.results import ProbabilityVolumeResults, CfNames
from pyprotolinc.assumptions.providers import AssumptionType
import pyprotolinc._actuarial as actuarial  # type: ignore
from pyprotolinc.models import Model
from pyprotolinc.portfolio import Portfolio
from pyprotolinc.models.state_models import AbstractStateModel

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


class TimeAxis2:
    """ Wrapper object for the CTimeAxis that is compatible with the Python-TimeAxis"""

    def __init__(self, c_time_axis_wrapper, years, months, days, quarters):
        self.c_time_axis_wrapper = c_time_axis_wrapper
        self.years = years
        self.months = months
        self.days = days
        self.quarters = quarters

    def __len__(self):
        return len(self.c_time_axis_wrapper)


class CProjector:
    """ Encapsulate the C-kernel calls. """

    def __init__(self, run_config: RunConfig,
                 portfolio: Portfolio,
                 model: Model,
                 proj_state: Any,
                 product,
                 rows_for_state_recorder: Optional[tuple[int]] = None,
                 chunk_index=1,
                 num_chunks=1) -> None:

        self.c_portfolio = actuarial.build_c_portfolio(portfolio)
        self.time_step = actuarial.TimeStep.MONTHLY  # actuarial.TimeStep.MONTHLY  # QUARTERLY   # TODO: test if we get back a result set with this timestep
        self.max_age = run_config.max_age

        self.model = model
        self.state_dimension: int = len(self.model.known_states)
        self.product = product

        # placeholder for the results
        self._output_columns: list[str] = []
        self._result: Optional[npt.NDArray[np.float64]] = None

        # for logging
        self.chunk_index = chunk_index
        self.num_chunks = num_chunks

        # construct assumption set
        acs_be: actuarial.AssumptionSet = model.assumption_set_be  # self.build_assumption_set()

        self.runner = actuarial.RunnerInterfaceWrapper(acs_be, self.c_portfolio, self.time_step, self.max_age, run_config.use_multicore, run_config.years_to_simulate)
        self.time_axis = TimeAxis2(*self.runner.get_time_axis())

        # product information, here we obtain the whole conditional payment stream upfront
        self.cond_bom_payment_dict = self.product.get_bom_payments(self.time_axis)
        self.cond_eom_payment_dict = self.product.get_state_transition_payments(self.time_axis)

        # contractual state transitions originating from the product and the insured state
        # rather than actuarial assumptions
        self.contractual_state_transitions = self.product.contractual_state_transitions(self.time_axis)

        # pass BOP information to C++
        for state, payment_list in self.cond_bom_payment_dict.items():
            for payment_type_index, payment_matrix in payment_list:
                self.runner.add_cond_state_payment(state, payment_type_index, payment_matrix)

        # print("EOM-payment", self.cond_eom_payment_dict)
        # print("BOM-payment", self.cond_bom_payment_dict)

    # def build_assumption_set(self):
    #     """ Construct the actuarial assumption set for the C-Kernel. """

    #     non_trivial_state_transitions_be = self.model.get_non_trivial_state_transitions(AssumptionType.BE)

    #     acs = actuarial.AssumptionSet(self.state_dimension)

    #     # get BE assumptions
    #     for (from_state, to_state) in non_trivial_state_transitions_be:
    #         provider = self.model.rates_provider_matrix_be[from_state][to_state]

    #         if isinstance(provider, actuarial.ConstantRateProvider):
    #             acs.add_provider_const(from_state, to_state, provider)
    #         elif isinstance(provider, actuarial.StandardRateProvider):
    #             acs.add_provider_std(from_state, to_state, provider)

    #     # # DUMMYS:
    #     # # provider05 = actuarial.ConstantRateProvider(0.5)
    #     # provider02 = actuarial.ConstantRateProvider(0.0015)
    #     # acs = actuarial.AssumptionSet(2)
    #     # acs.add_provider_const(0, 1, provider02)
    #     # # acs.add_provider_const(1, 0, provider05)

    #     return acs

    def run(self):
        self._output_columns, self._result = self.runner.run()

    def get_results_dict(self) -> dict[str, npt.NDArray[np.float64]]:
        if self._result is None:
            raise Exception("Logic Error: results must be calculated before getting them.")

        # non-cash flows
        c_output_map = {col_name: index for index, col_name in enumerate(self._output_columns) if not col_name.startswith("STATE_PAYMENT_TYPE_")}

        num_rows = self._result.shape[0]

        data = {
            "YEAR": self._result[:, c_output_map["PERIOD_END_Y"]],
            "QUARTER": (self._result[:, c_output_map["PERIOD_END_M"]] - 1) // 3 + 1,
            "MONTH": self._result[:, c_output_map["PERIOD_END_M"]]
        }

        cf_map = {CfNames(int(col_name[19:])): index
                  for index, col_name in enumerate(self._output_columns)
                  if col_name.startswith("STATE_PAYMENT_TYPE_")}

        output_model_map = self.model.states_model.to_std_outputs()

        # cashflows
        for cfn in CfNames:
            mapped_col_no = cf_map.get(cfn)  # c_output_map.get(cfn.name)
            if mapped_col_no is None:
                data[cfn.name] = np.zeros(num_rows)
            else:
                data[cfn.name] = self._result[:, mapped_col_no]

        # reserves -- TODO: the reserve mapping uses the names from the statet model rather than the generic output model
        for st in self.model.states_model:
            c_col_name = "RESERVE_BOM_{}".format(st.value)
            output_col_name = "RESERVE_BOM({})".format(st.name)
            mapped_col_no = c_output_map.get(c_col_name)
            if mapped_col_no is None:
                data[output_col_name] = np.zeros(num_rows)
            else:
                data[output_col_name] = self._result[:, mapped_col_no]

        # add the probability movements
        for vol_prob_res in ProbabilityVolumeResults:

            # get mapping
            mapped = output_model_map.get(vol_prob_res)

            if mapped is None:
                # add zero vector for not mapped output
                data[vol_prob_res.name] = np.zeros(num_rows)
            else:
                if vol_prob_res.name.startswith("VOL_"):

                    if isinstance(mapped, AbstractStateModel):
                        state_no = mapped.value

                        # TODO: decide if VOL output should be PROB_STATE or VOL_STATE
                        c_state_name = "PROB_STATE_{}".format(state_no)
                        data[vol_prob_res.name] = self._result[:, c_output_map[c_state_name]]
                    else:
                        raise Exception("VOL columns are not state transitions!")

                elif vol_prob_res.name.startswith("MV_"):

                    if isinstance(mapped, tuple):
                        from_state_no = mapped[0].value
                        to_state_no = mapped[1].value

                        # TODO: decide if VOL output should be PROB_STATE or VOL_STATE
                        c_state_name = "PROB_MVM_{}_{}".format(from_state_no, to_state_no)
                        data[vol_prob_res.name] = self._result[:, c_output_map[c_state_name]]
                    else:
                        raise Exception("MVM output must be a tuple!")

        return data


# TODO: rename internal methods so that they start with "_"
class Projector:
    """ The PYTHON projection engine. """

    def __init__(self,
                 run_config: RunConfig,
                 portfolio: Portfolio,
                 model: Model,
                 proj_state,
                 product,
                 rows_for_state_recorder=None,
                 chunk_index: int = 1,
                 num_chunks: int = 1) -> None:

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
        self.reserving_rate = portfolio.reserving_rate
        self.years_of_birth = portfolio.years_of_birth
        self.gender = portfolio.gender

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

    def select_applicable_base_assumptions(self, ages, genders, calendaryear, smokerstatus, yearsdisabledifdisabledatstart):
        """ Construct a three dimensional tensor that contains the base assumptions.
            Indexes:
              * row in the portfolio
              * 'from' state
              * 'to' state
        """

        # print("ages, genders, calendaryear, smokerstatus, yearsdisabledifdisabledatstart")
        # print(ages.dtype, genders.dtype, calendaryear.dtype, smokerstatus.dtype, yearsdisabledifdisabledatstart.dtype)

        # get BE assumptions
        for (from_state, to_state) in self.non_trivial_state_transitions_be:
            provider = self.model.rates_provider_matrix_be[from_state][to_state]
            # print(from_state, to_state, provider.get_offsets())
            sel_ass = provider.get_rates(len(ages),
                                         age=ages,
                                         gender=genders,
                                         calendaryear=calendaryear,
                                         smokerstatus=smokerstatus,
                                         yearsdisabledifdisabledatstart=yearsdisabledifdisabledatstart)
            self.applicable_yearly_assumptions_be[:, from_state, to_state] = sel_ass

        # get RES assumptions
        for (from_state, to_state) in self.non_trivial_state_transitions_res:
            provider = self.model.rates_provider_matrix_res[from_state][to_state]
            sel_ass = provider.get_rates(len(ages),
                                         age=ages,
                                         gender=genders,
                                         calendaryear=calendaryear,
                                         smokerstatus=smokerstatus,
                                         yearsdisabledifdisabledatstart=yearsdisabledifdisabledatstart)
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

        # obtain the discount factor and force into column shape
        # reserving_interest = self.reserving_rate.reshape((self.proj_state.num_records, 1))  # 0.0  # 0.04   # Placeholder for now!
        # reserving_interest = 0.04  # Placeholder for now!
        reserving_interest = self.reserving_rate.reshape((1, self.proj_state.num_records))
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

            # first we determine the amounts needed based on the transitions
            # the structure of transition_amounts is (from_state, to_state, insured), the broadcasting adds the reserve needed in the "to_state" to the payments
            transition_amounts = (cf_eom_per_state_change) + reserves_last_month_conditional   # here we reflect that reserves are not in P/L sign logic

            # the transition amounts are multiplied with the transition probabilities
            # the probabilities with time fixed have the strcuture(insured(r), from_state(f), to_state(t))
            cond_res_eom = np.einsum('rft,ftr->fr', self.transition_ass_monthly_res_with_time[self.month_count, :], transition_amounts)

            reserves_last_month_conditional[:] = cfs_bom_per_state + monthly_discount_factor * cond_res_eom

            # store the "probability weighted" reserve
            reserves_bom_by_insured[self.month_count, :] = reserves_last_month_conditional[:] * self.probability_states_with_time[self.month_count, :]

            self.month_count -= 1

        return reserves_bom_by_insured

    def get_results_dict(self) -> dict[str, npt.NDArray[np.float64]]:
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

    def initialize_assumption_providers(self):
        """ Call into the init hook of the assumption providers. """
        # get BE assumptions
        for (from_state, to_state) in self.non_trivial_state_transitions_be:
            provider = self.model.rates_provider_matrix_be[from_state][to_state]
            provider.initialize(years_of_birth=self.years_of_birth, gender=self.gender)

        # get RES assumptions
        for (from_state, to_state) in self.non_trivial_state_transitions_res:
            provider = self.model.rates_provider_matrix_res[from_state][to_state]
            provider.initialize(years_of_birth=self.years_of_birth, gender=self.gender)

    def run(self) -> None:
        # projection loop over time
        _terminate = False
        _ages_last_month = -np.ones(self.proj_state.num_records)  # iniate with negative values
        _calendaryear_last_month = -np.ones(self.proj_state.num_records)
        _years_disabled_if_at_start_last_month = np.ones(self.proj_state.num_records) * np.NaN

        # initialize the assumption providers
        self.initialize_assumption_providers()

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
                # print("Timestep {}/{}".format(yr, month))

                # save the accumulated state probabilities at BOM according to the BE assumptions
                self.probability_states_with_time[self.month_count, :] = self.proj_state.probability_states[:, 1, :]

                # calculate the NCF due at the beginning of the current month
                self.calc_payments_bom()

                # update the yearly assumptions

                # get risk factors
                ages_months, genders, smokerstatus, months_disabled_if_at_start = self.proj_state.get_assumption_cofactors()
                ages = np.minimum(ages_months // 12, MAX_AGE)  # age selection depends on completed years
                years_disabled_if_at_start = months_disabled_if_at_start // 12

                calendaryear = np.ones(len(ages), dtype=np.int32) * self.time_axis.years[self.month_count]

                # check if the risk factors have changed and refresh the assumptions in this case
                assumption_update_required = not (np.array_equal(ages, _ages_last_month) and np.array_equal(calendaryear, _calendaryear_last_month)
                                                  and np.array_equal(years_disabled_if_at_start, _years_disabled_if_at_start_last_month))

                if assumption_update_required:
                    self.select_applicable_base_assumptions(ages, genders, calendaryear, smokerstatus, years_disabled_if_at_start)

                    # TODO: apply assumption modifiers on policy level as found in the portfolio data if any

                    # adjust assumptions for the length of the timestep
                    # TODO: The adjuster could be injected here or into the model (via a Mixin?)
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
                _years_disabled_if_at_start_last_month[:] = years_disabled_if_at_start

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
                    self.transition_ass_monthly_res_with_time[self.month_count, :] = np.einsum('rij,rjk->rik',
                                                                                               transition_ass_timestep_res_ts,
                                                                                               self.contractual_transition_ts_period)
                else:

                    # save unadjusted reserving assumptions in any case
                    self.transition_ass_monthly_res_with_time[self.month_count, :] = transition_ass_timestep_res_ts

                # at end of the month:
                # the next call also counts the number_all_zero_cashflows which are used to decide about the termination
                self.calc_payments_eom()

                self.proj_state.advance_month()

                # check for early termination
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

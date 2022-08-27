/**
 * @file record_projector.h
 * @author M. Seehafer
 * @brief Projection engine for one record.
 * @version 0.1
 * @date 2022-08-27
 * 
 * @copyright Copyright (c) 2022
 * 
 */


#ifndef C_RECORD_PROJECTOR_H
#define C_RECORD_PROJECTOR_H

#include <vector>
#include <string>
#include <iostream>
#include <memory>
#include <algorithm>
#include "assumption_sets.h"
#include "providers.h"
#include "portfolio.h"
#include "run_config.h"
#include "time_axis.h"
#include "run_result.h"
#include "risk_factors.h"

using namespace std;

/**
 * @brief Functionality to project cash flows for a single record at a time.
 * 
 */
class RecordProjector
{

private:
    const CRunConfig &_run_config;
    const TimeAxis &_ta;

    const unsigned int _dimension;

    // time loop relevant fixed vectors
    const vector<PeriodDate> &_start_dates = _ta.get_start_dates();
    const vector<PeriodDate> &_end_dates = _ta.get_end_dates();
    const vector<int> &_period_lengths = _ta.get_period_length_in_days();

    // valuation assumption sets
    CAssumptionSet _record_be_assumptions;
    vector<shared_ptr<CAssumptionSet>> _record_other_assumptions;

    ///////////////////////////////////////
    // run specific values
    ///////////////////////////////////////

    unique_ptr<double[]> be_a_yearly; // current independent be assumptions on the yearly grid
    // TODO: something similar for other assumptions needed

    unique_ptr<double[]> be_a_time_step_dependent; // current dependent assumptions on the time-step-grid
    // TODO: something similar for other assumptions needed

    // the risk factors
    vector<int> risk_factors_current = vector<int>(NUMBER_OF_RISK_FACTORS);
    vector<int> risk_factors_last_used = vector<int>(NUMBER_OF_RISK_FACTORS, -1);

    ///////////////////////////////////////
    // private metods
    ///////////////////////////////////////

    void adjust_assumptions_simple(int days);

    void set_relevant_risk_factors(vector<bool> &relevant_risk_factors)
    {
        relevant_risk_factors.assign(NUMBER_OF_RISK_FACTORS, false);
        
        _record_be_assumptions.get_relevant_risk_factor_indexes(relevant_risk_factors);
        for (auto oas : _record_other_assumptions)
        {
            oas->get_relevant_risk_factor_indexes(relevant_risk_factors);
        }
    }

    ///< Check if a risk factor relevant for the projection was updated
    bool relevant_factor_changed(const vector<bool> &relevant_risk_factors)
    {
        for (size_t s = 0; s < NUMBER_OF_RISK_FACTORS; s++)
        {
            if (relevant_risk_factors[s] && (risk_factors_current[s] != risk_factors_last_used[s]))
            {
                return true;
            }
        }
        return false;
    }

    ///< Clear temporary values stored in the projector object.
    void clear()
    {
        cout << "RecordProjector::clear()" << endl;
    }


    void slice_assumptions(const CPolicy &policy)
    {
        cout << "RecordProjector::slice_assumptions() -- TODO!" << endl;
        vector<int> slice_indexes(NUMBER_OF_RISK_FACTORS, -1);

        // specialize for Gender and SmokerStatus
        slice_indexes[(int)CRiskFactors::Gender] = policy.get_gender();
        slice_indexes[(int)CRiskFactors::SmokerStatus] = policy.get_smoker_status();

        _run_config.get_be_assumptions().slice_into(slice_indexes, _record_be_assumptions);
        for(int n=0; n < _run_config.get_other_assumptions().size(); n++) {
             _run_config.get_other_assumptions()[n]->slice_into(slice_indexes, *_record_other_assumptions[n]);
        }
    }    

public:
    RecordProjector(const CRunConfig &run_config, const TimeAxis &ta) : _run_config(run_config),
                                                                        _ta(ta),
                                                                        _dimension(run_config.get_dimension()),
                                                                        _start_dates(_ta.get_start_dates()),
                                                                        _end_dates(_ta.get_end_dates()),
                                                                        _period_lengths(_ta.get_period_length_in_days()),
                                                                        _record_be_assumptions(_run_config.get_be_assumptions().get_dimension())
    {
        // array containers for the current assumptions
        be_a_yearly = unique_ptr<double[]>(new double[_dimension * _dimension], std::default_delete<double[]>());
        be_a_time_step_dependent = unique_ptr<double[]>(new double[_dimension * _dimension], std::default_delete<double[]>());

        // deep copy of the portfolio assumption set into the record assumption set
        // which is later on sliced as needed
        _run_config.get_be_assumptions().clone_into(_record_be_assumptions);
        const vector<shared_ptr<CAssumptionSet>> &other_assumptions = _run_config.get_other_assumptions();
        for (const shared_ptr<CAssumptionSet> &oa : other_assumptions)
        {
            auto rec_oas = make_shared<CAssumptionSet>(oa->get_dimension());
            oa->clone_into(*rec_oas);
            _record_other_assumptions.push_back(rec_oas);
        }
    }




    /**
     * @brief Create the projection result for one policy.
     * 
     * @param runner_no Number of the runner instance.
     * @param record_count Number of record in batch for this runner.
     * @param policy The record to project
     * @param result Container for the result
     * @param portfolio_date portfolio date
     */
    void run(int runner_no, int record_count, const CPolicy &policy, RunResult &result, const PeriodDate &portfolio_date);
};

void RecordProjector::run(int runner_no, int record_count, const CPolicy &policy, RunResult &result, const PeriodDate &portfolio_date)
{

    cout << "RecordProjector::run() - with " << policy.to_string() << endl;

    if (record_count % 1000 == 0)
    {
        cout << "Projector for runner #" << runner_no << ", record_count=" << record_count << ", ID=" << policy.get_cession_id() << endl;
    }

    // clean up before
    this->clear();

    // specialize the assumption providers for the current record
    this->slice_assumptions(policy);

    // determine which risk factors are relevant
    vector<bool> relevant_risk_factors(NUMBER_OF_RISK_FACTORS, false);
    set_relevant_risk_factors(relevant_risk_factors);
    // control output
    print_vec<bool>(relevant_risk_factors, "relevant_risk_factors");

    // initialize the risk factors - could have taken the start date from the time axis instead
    int age_month_completed = get_age_at_date(policy.get_dob_year(), policy.get_dob_month(), policy.get_dob_day(), portfolio_date.get_year(), portfolio_date.get_month(), portfolio_date.get_day());

    // cout << "RecordProjector::run() - number of time steps is " << _end_dates.size() << endl;
    // cout << "RecordProjector::run(): dimension=" << _record_be_assumptions.get_dimension() << endl;
    // for (unsigned r = 0; r < _dimension; r++)
    // {
    //     for (unsigned c = 0; c < _dimension; c++)
    //     {
    //         cout << "RecordProjector::run(): (" << r << ", " << c << "): " << _record_be_assumptions.get_provider_info(r, c) << endl;
    //     }
    // }

    int max_time_step_index = (int)_end_dates.size() - 1;

    bool early_stop = false;
    int time_index = 0;

    // special treatment of first time step as needed


    // main loop over time
    bool first_iteration = true;
    while (++time_index <= max_time_step_index)
    {

        cout << "Simulation step until " << _end_dates[time_index] << endl;

        int days_previous_step = _period_lengths[time_index - 1];
        int days_current_step = _period_lengths[time_index];

        cout <<   "duration_prev=" << days_previous_step << ", duration_curr=" << days_current_step << endl;

        ///////////////////////////////////////////////////////////////////////////////////////
        // Step 1: identify the assumptions to be used for this step
        ///////////////////////////////////////////////////////////////////////////////////////

        // update the risk factors
        risk_factors_current[0] = age_month_completed / 12;            // 0 Age
        risk_factors_current[1] = policy.get_gender();                 // 1 Gender
        risk_factors_current[2] = _start_dates[time_index].get_year(); // 2 CalendarYear
        risk_factors_current[3] = policy.get_smoker_status();          // 3 SmokerStatus
        risk_factors_current[4] = 0;                                   // 4 YearsDisabledIfDisabledAtStart  -- TODO!

        // check if we need to update the yearly assumptions
        bool yearly_assumptions_updated = false;
        if (relevant_factor_changed(relevant_risk_factors) || first_iteration)
        {
            cout << "updating yearly assumptions" << endl;
            _record_be_assumptions.get_single_rateset(risk_factors_current, be_a_yearly.get());
            yearly_assumptions_updated = true;

            // print out the yearly assumptions
            cout << "  unscaled" << endl;
            for (unsigned r = 0; r < _dimension; r++)
            {
                cout << "    ";
                for (unsigned c = 0; c < _dimension; c++)
                {
                    cout << be_a_yearly.get()[r * _dimension + c] << ", ";
                }
                cout << endl;
            }

            // copy new relevant risk factors to last used
            risk_factors_last_used.assign(risk_factors_current.begin(), risk_factors_current.end());
        }

        // convert the assumptions to the length of the timestep and make them dependent
        if (yearly_assumptions_updated || (days_current_step != days_previous_step))
        {
            cout << "updating period assumptions" << endl;
            adjust_assumptions_simple(days_current_step);
        }

        // print out the adjusted assumptions
        cout << "  scaled" << endl;
        for (unsigned r = 0; r < _dimension; r++)
        {
            cout << "    ";
            for (unsigned c = 0; c < _dimension; c++)
            {
                cout << be_a_time_step_dependent.get()[r * _dimension + c] << ", ";
            }
            cout << endl;
        }


        ///////////////////////////////////////////////////////////////////////////////////////
        // Step 2: Update the state
        ///////////////////////////////////////////////////////////////////////////////////////













        first_iteration = false;

        if (early_stop)
        {
            cout << "Early stop detected." << endl;
            break;
        }
    }

    // clean-up after early stop as necessary
    if (early_stop)
    {
    }
}

void RecordProjector::adjust_assumptions_simple(int days)
{
    double duration_factor = days / 360.0;
    double sum_row_nondiag;

    // simple scaling method
    for (unsigned r = 0; r < _dimension; r++)
    {
        sum_row_nondiag = 0;
        for (unsigned c = 0; c < _dimension; c++)
        {
            if (c == r)
            {
                continue;
            }
            double this_scaled_val = duration_factor * be_a_yearly.get()[r * _dimension + c];
            sum_row_nondiag += this_scaled_val;
            be_a_time_step_dependent.get()[r * _dimension + c] = this_scaled_val;
        }
        be_a_time_step_dependent.get()[r * _dimension + r] = 1 - sum_row_nondiag;
    }
}

#endif
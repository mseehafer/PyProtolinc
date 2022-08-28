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
 * @brief Methods to calculate the policy state probabilities, data storage is managed externally.
 * 
 */
class ProjectionStateMatrix
{
private:
    double *_state_probs = nullptr;
    int _num_timesteps;
    int _num_states;
    int _size;


public:
    /**
     * @brief Construct a new Projection State Matrix object
     * 
     * @param num_timesteps Number of timesteps
     * @param num_states Number of possible states
     */
    ProjectionStateMatrix(int num_timesteps, int num_states): _num_timesteps(num_timesteps), _num_states(num_states), _size(num_timesteps*num_states) {
    }

    // no copying intended
    ProjectionStateMatrix() = delete;
    ProjectionStateMatrix(const ProjectionStateMatrix &) = delete;
    ProjectionStateMatrix(ProjectionStateMatrix &&) = delete;

    
    /**
     * @brief Set the data pointer in that method and reset the state matrix (fill with zero) and set the initial state in the first row
     * 
     * @param state_probs Pointer to the data array
     * @param start_state Initial state the record is in
     */
    void initialize_states(double *state_probs, int start_state) {
        _state_probs = state_probs;

        if (start_state < 0 || start_state >= _num_states) {
            throw domain_error("Invalid state index: " + start_state);
        }
        // for(int j = 0; j<_size; j++) {
        //     _state_probs[j] = 0;
        // }
        
        _state_probs[0 * _num_states +  start_state] = 1;
    }

    /**
     * @brief Calculate the probabilities of the next state.
     * 
     * @param index_last Index (row) of the last valid assumption set
     * @param be_a_ts (Dependent) assumptions to be applied for the current timestep
     */
    void update_state(int index_last, double* be_a_ts)
    {
        // SHOULD IT BE AS SIMPLE AS THAT?
        
        // use some pointer arithmetics
        double *current_states = _state_probs + index_last * _num_states;
        double *updated_states = _state_probs + (1 + index_last) * _num_states;

        for (int r = 0; r < _num_states; r++)
        {
            for (int  c = 0; c < _num_states; c++)
            {
                updated_states[c] += be_a_ts[r * _num_states + c] * current_states[r];
            }
        }        
    }


    void print_state_probs(int time_index)
    {
        double *states = _state_probs + time_index * _num_states;

        cout << "STATES (t=" << time_index << ") = [";
        for (int i = 0; i < _num_states; i++)
        {
            if (i > 0) {
                cout << ", ";
            }
            cout << states[i];
        }

        cout << "]" << endl;
    }
    
};


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

    /// the best estimate states
    unique_ptr<ProjectionStateMatrix> _be_states;

    ///////////////////////////////////////
    // private metods
    ///////////////////////////////////////

    void adjust_assumptions_simple(int days);

    /// Mark the relevant risk factors as true
    void set_relevant_risk_factors(vector<bool> &relevant_risk_factors)
    {
        relevant_risk_factors.assign(NUMBER_OF_RISK_FACTORS, false);
        
        _record_be_assumptions.get_relevant_risk_factor_indexes(relevant_risk_factors);
        for (auto oas : _record_other_assumptions)
        {
            oas->get_relevant_risk_factor_indexes(relevant_risk_factors);
        }
    }

    /// Check if a risk factor relevant for the projection was updated
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
//        cout << "RecordProjector::clear()" << endl;
    }


    void slice_assumptions(const CPolicy &policy)
    {
//        cout << "RecordProjector::slice_assumptions()" << endl;
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
        _be_states = unique_ptr<ProjectionStateMatrix>(new ProjectionStateMatrix((int)_ta.get_length(), (int)_run_config.get_dimension()));
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

//    cout << "RecordProjector::run() - with " << policy.to_string() << endl;

    // if (record_count % 1000 == 0)
    // {
    //     cout << "Projector for runner #" << runner_no << ", record_count=" << record_count << ", ID=" << policy.get_cession_id() << endl;
    // }

    // clean up before
    this->clear();

    /////////////////////////////////
    // set relevant storage pointers
    ////////////////////////////////
    
    // in this case also: initialize the state matrix
    _be_states->initialize_states(result.get_be_state_probs_ptr(), policy.get_initial_state());    

    // specialize the assumption providers for the current record
    this->slice_assumptions(policy);

    // determine which risk factors are relevant
    vector<bool> relevant_risk_factors(NUMBER_OF_RISK_FACTORS, false);
    set_relevant_risk_factors(relevant_risk_factors);
    // control output
//    print_vec<bool>(relevant_risk_factors, "relevant_risk_factors");

    // initialize the risk factors - could have taken the start date from the time axis instead


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
    // assert portfolio_date == _end_dates[0] = _start_dates[0]
//    cout << "Projection start at " << _end_dates[0] <<endl;
    int age_month_completed = get_age_at_date(policy.get_dob(), portfolio_date);
//    cout << "Age of policyholder: " << age_month_completed << "  (" << age_month_completed / 12.0 << ")" << endl;




    // main loop over time
    bool first_iteration = true;
    bool yearly_assumptions_updated = false;    
    while (++time_index <= max_time_step_index)
    {

        int days_previous_step = _period_lengths[time_index - 1];
        int days_current_step = _period_lengths[time_index];

//        cout << "Simulation step until " << _end_dates[time_index] << ", duration_prev=" << days_previous_step << ", duration_curr=" << days_current_step << endl;

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
        yearly_assumptions_updated = false;
        if (relevant_factor_changed(relevant_risk_factors) || first_iteration)
        {
//            cout << "updating yearly assumptions" << endl;
            _record_be_assumptions.get_single_rateset(risk_factors_current, be_a_yearly.get());
            yearly_assumptions_updated = true;

            // // print out the yearly assumptions
            // cout << "  unscaled" << endl;
            // for (unsigned r = 0; r < _dimension; r++)
            // {
            //     cout << "    ";
            //     for (unsigned c = 0; c < _dimension; c++)
            //     {
            //         cout << be_a_yearly.get()[r * _dimension + c] << ", ";
            //     }
            //     cout << endl;
            // }

            // copy new relevant risk factors to last used
            risk_factors_last_used.assign(risk_factors_current.begin(), risk_factors_current.end());
        }

        // convert the assumptions to the length of the timestep and make them dependent
        if (yearly_assumptions_updated || (days_current_step != days_previous_step))
        {
//            cout << "updating period assumptions" << endl;
            adjust_assumptions_simple(days_current_step);
        }

        // // print out the adjusted assumptions
        // cout << "  scaled" << endl;
        // for (unsigned r = 0; r < _dimension; r++)
        // {
        //     cout << "    ";
        //     for (unsigned c = 0; c < _dimension; c++)
        //     {
        //         cout << be_a_time_step_dependent.get()[r * _dimension + c] << ", ";
        //     }
        //     cout << endl;
        // }


        ///////////////////////////////////////////////////////////////////////////////////////
        // Step 2: Payments at begin of period
        ///////////////////////////////////////////////////////////////////////////////////////


        ///////////////////////////////////////////////////////////////////////////////////////
        // Step 3: Update the state
        ///////////////////////////////////////////////////////////////////////////////////////

//        _be_states->print_state_probs(time_index - 1);
        _be_states->update_state(time_index - 1, be_a_time_step_dependent.get());
//        _be_states->print_state_probs(time_index);


        ///////////////////////////////////////////////////////////////////////////////////////
        // Step 4: Payments at end of period
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
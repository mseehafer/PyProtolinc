/**
 * @file run_result.h
 * @author M. Seehafer
 * @brief Stores the result of a calculation.
 * @version 0.1
 * @date 2022-08-27
 * 
 * @copyright Copyright (c) 2022
 * 
 */

#ifndef C_RUN_RESULT_H
#define C_RUN_RESULT_H

#include <vector>
#include <string>
#include "time_axis.h"

using namespace std;

/// Column meaning of the result array when an external array is populated.
const vector<string> time_axis_names = {
    "PERIOD_START_Y", "PERIOD_START_M", "PERIOD_START_D",
    "PERIOD_END_Y", "PERIOD_END_M", "PERIOD_END_D",
    "PERIOD_DAYS"};


/// Insert a submatrix into the result matrix
void copy_state_probs(double *ext_result, double *res_cmp, int _num_states, int row_num, int col_num, int start_col)
{
    for (int t = 0; t < row_num; t++)
    {
        for (int state_index = 0; state_index < _num_states; state_index++)
        {
            ext_result[t * col_num + start_col + state_index] = res_cmp[t * _num_states + state_index];
        }
    }
}

void copy_state_probs_mvms(double *ext_result, double *res_cmp, int _num_states, int row_num, int col_num, int start_col)
{
    for (int t = 0; t < row_num; t++)
    {
        for (int from_state_index = 0; from_state_index < _num_states; from_state_index++) {
            for (int to_state_index = 0; to_state_index < _num_states; to_state_index++)
            {
                ext_result[t * col_num + start_col + from_state_index * _num_states + to_state_index] = res_cmp[t * _num_states * _num_states + from_state_index * _num_states + to_state_index];
            }
        }
    }
}




/**
 * @brief Result container that is used to store results at various granularities and provides for
 * aggregation functinality of partial results.
 * 
 */
class RunResult
{
private:
    //double *results;

    int _num_states;
    int _num_timesteps;    

    shared_ptr<TimeAxis> _ta = nullptr;

    /// projected state probabilities and probability movements
    unique_ptr<double[]> _be_state_probs = nullptr;
    unique_ptr<double[]> _be_prob_movements = nullptr;

    /// projected state volume and volume movements
    unique_ptr<double[]> _be_state_vols = nullptr;
    unique_ptr<double[]> _be_vol_movements = nullptr;



    // private methods
    void copy_time_axis(double *ext_result, int rows_num, int col_num, int start_col);
    //void copy_state_probs(double *ext_result, double *res_cmp, int rows_num, int col_num, int start_col);


public:
    /**
     * @brief Construct a new Run Result object
     * 
     * @param num_states Number of states in states model
     * @param p_time_axis Pointer to the time axis object
     */
    RunResult(int num_states, shared_ptr<TimeAxis> p_time_axis) : _num_states(num_states), _num_timesteps(p_time_axis->get_length()), _ta(p_time_axis) {

       // allocate memory for the be probability states
       _be_state_probs = unique_ptr<double[]>(new double[_num_timesteps * _num_states], std::default_delete<double[]>());
       _be_prob_movements = unique_ptr<double[]>(new double[_num_timesteps * _num_states * _num_states], std::default_delete<double[]>());
       
       _be_state_vols = unique_ptr<double[]>(new double[_num_timesteps * _num_states], std::default_delete<double[]>());
       _be_vol_movements = unique_ptr<double[]>(new double[_num_timesteps * _num_states * _num_states], std::default_delete<double[]>());
       
       // initialize with zeros
       this->reset();
    }

    /// Return a list of strings containing the headers of the external results table
    vector<string> get_result_header_names() {
        // copy the time axis names
        vector<string> hdrs = time_axis_names;

        // add be_state_probs
        for(int j=0; j < _num_states; j++) {
            hdrs.push_back("PROB_STATE_" + std::to_string(j));
        }

        // add be_state_probs movements
        for(int from=0; from < _num_states; from++) {
            for(int to=0; to < _num_states; to++) {
                hdrs.push_back("PROB_MVM_" + std::to_string(from) + "_" + std::to_string(to));
            }
        }

        // add be_state_vols
        for(int j=0; j < _num_states; j++) {
            hdrs.push_back("VOL_STATE_" + std::to_string(j));
        }

        // add be_state_probs movements
        for(int from=0; from < _num_states; from++) {
            for(int to=0; to < _num_states; to++) {
                hdrs.push_back("VOL_MVM_" + std::to_string(from) + "_" + std::to_string(to));
            }
        }

        return hdrs;
    }

    /// Return a pointer to the space where to store the projected state probabilities
    double *get_be_state_probs_ptr() {
        return _be_state_probs.get();
    }

    /// Return a pointer to the space where to store the projected volume results
    double *get_be_state_vols_ptr() {
        return _be_state_vols.get();
    }

    /// Return a pointer to the space where to store the projected state probability movements
    double *get_be_prob_mvms_ptr() {
        return _be_prob_movements.get();
    }

    /// Return a pointer to the space where to store the projected state volume movements
    double *get_be_vol_mvms_ptr() {
        return _be_vol_movements.get();
    }


    /// Reset the result, zeroises the allocated arrays
    void reset() {
        // resetting _be_state_probs
        for (auto i = 0; i <  _num_states * _num_timesteps; i++) {
            _be_state_probs[i] = 0;
            _be_state_vols[i] = 0;
        }

        for (auto i = 0; i <  _num_states * _num_states * _num_timesteps; i++) {
            _be_prob_movements[i] = 0;
            _be_vol_movements[i] = 0;
        }
    }

    /// Add another result to this one
    void add_result(const RunResult &other_res) {

        // add state probabilities and volumes
        for (auto i = 0; i <  _num_states * _num_timesteps; i++) {
            _be_state_probs[i] += other_res._be_state_probs[i];
            _be_state_vols[i] += other_res._be_state_vols[i];
        }        

        // add probability and volume movements
        for (auto i = 0; i <  _num_states * _num_states * _num_timesteps; i++) {
            _be_prob_movements[i] += other_res._be_prob_movements[i];
            _be_vol_movements[i] += other_res._be_vol_movements[i];
        }        


    }

    /// Copy results to an external array
    void copy_results(double *ext_result, int row_num, int col_num)
    {
        int next_col = 0;
        
        copy_time_axis(ext_result, row_num, col_num, next_col );
        next_col += 7;
        
        copy_state_probs(ext_result, _be_state_probs.get(), _num_states, row_num, col_num, next_col );
        next_col += _num_states;

        copy_state_probs_mvms(ext_result, _be_prob_movements.get(), _num_states, row_num, col_num, next_col );
        next_col += _num_states * _num_states;

        copy_state_probs(ext_result, _be_state_vols.get(), _num_states, row_num, col_num, next_col );
        next_col += _num_states;

        copy_state_probs_mvms(ext_result, _be_vol_movements.get(), _num_states, row_num, col_num, next_col );
        next_col += _num_states * _num_states;
    }

    /// Return the number of rows in the result set
    int size() {
        return (int) _ta->get_length();
    }
};

void RunResult::copy_time_axis(double *ext_result, int row_num, int col_num, int start_col)
{

    if (row_num != _ta->get_length()) {
        throw domain_error("Wrong length hof external array");
    }

   
    for (int t = 0; t < row_num; t++)
    {
        const PeriodDate &p_end = _ta->end_at(t);
        const PeriodDate &p_start = _ta->start_at(t);

        // perdiod start
        ext_result[t * col_num + start_col + 0] = p_start.get_year();
        ext_result[t * col_num + start_col + 1] = p_start.get_month();
        ext_result[t * col_num + start_col + 2] = p_start.get_day();

        // period end
        ext_result[t * col_num + start_col + 3] = p_end.get_year();
        ext_result[t * col_num + start_col + 4] = p_end.get_month();
        ext_result[t * col_num + start_col + 5] = p_end.get_day();

        // duration
        ext_result[t * col_num + start_col + 6] = _ta->duration_at(t);
    }
}



#endif
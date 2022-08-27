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
const vector<string> result_names = {
    "PERIOD_START_Y", "PERIOD_START_M", "PERIOD_START_D",
    "PERIOD_END_Y", "PERIOD_END_M", "PERIOD_END_D",
    "PERIOD_DAYS"};


/**
 * @brief Result container that is used to store results at various granularities and provides for
 * aggregation functinality of partial results.
 * 
 */
class RunResult
{
private:
    // todo
    double *results;

    shared_ptr<TimeAxis> _ta = nullptr;
    //shared_ptr<TimeAxis> p_time_axis;

    void copy_time_axis(double *ext_result);

public:
    RunResult() {}
    RunResult(shared_ptr<TimeAxis> p_time_axis) : _ta(p_time_axis) {}

    RunResult & set_time_axis(shared_ptr<TimeAxis> p_time_axis) {
        _ta = p_time_axis;
        return *this;
    }

    /// Reset the result
    void reset() {}

    /// Add another result to this one
    void add_result(const RunResult &other_res) {}

    /// Copy results to an external array
    void copy_results(double *ext_result)
    {
        copy_time_axis(ext_result);
    }

    /// Return the number of rows in the result set
    int size() {
        return (int) _ta->get_length();
    }
};

void RunResult::copy_time_axis(double *ext_result)
{
    size_t col_length = result_names.size();

    for (int t = 0; t < _ta->get_length(); t++)
    {
        const PeriodDate &p_end = _ta->end_at(t);
        const PeriodDate &p_start = _ta->start_at(t);

        // perdiod start
        ext_result[t * col_length + 0] = p_start.get_year();
        ext_result[t * col_length + 1] = p_start.get_month();
        ext_result[t * col_length + 2] = p_start.get_day();

        // period end
        ext_result[t * col_length + 3] = p_end.get_year();
        ext_result[t * col_length + 4] = p_end.get_month();
        ext_result[t * col_length + 5] = p_end.get_day();

        // duration
        ext_result[t * col_length + 6] = _ta->duration_at(t);
    }
}

#endif
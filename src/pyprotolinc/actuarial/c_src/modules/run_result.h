

/* Projection of one record. */

#ifndef C_RUN_RESULT_H
#define C_RUN_RESULT_H

#include <vector>
#include <string>
// #include <iostream>
// #include "assumption_sets.h"
// #include "providers.h"
// #include "portfolio.h"
// #include "run_config.h"
#include "time_axis.h"

using namespace std;

const vector<string> result_names = {
    "PERIOD_START_Y", "PERIOD_START_M", "PERIOD_START_D",
    "PERIOD_END_Y", "PERIOD_END_M", "PERIOD_END_D",
    "PERIOD_DAYS"};

/// a result container that is used at various granularities
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

    // reset the result
    void reset() {}

    // add another result to this one
    void add_result(const RunResult &other_res) {}

    void copy_results(double *ext_result)
    {
        copy_time_axis(ext_result);
    }

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
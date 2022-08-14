



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


const vector<string> result_names = {"YEAR", "QUARTER", "MONTH"};


/// a result container that is used at various granularities
class RunResult {
private:
    // todo
    double* results;

    const TimeAxis &_ta;
public:
    
    RunResult(const TimeAxis &ta): _ta(ta) {}

    // reset the result
    void reset() {}

    // add another result to this one
    void add_result(const RunResult& other_res) {}

    void copy_results(double *ext_result) {
        const int col_length = 3;

        for (int t=0; t < _ta.get_total_timesteps(); t++) {
            TimeIndex ti = _ta.at(t);

            ext_result[t* col_length + 0] = ti.year;
            ext_result[t* col_length + 1] = ti.quarter;
            ext_result[t* col_length + 2] = ti.month;
        }

    }
};


#endif


/* Projection of one record. */

#ifndef C_RECORD_PROJECTOR_H
#define C_RECORD_PROJECTOR_H

#include <vector>
#include <string>
#include <iostream>
#include "assumption_sets.h"
#include "providers.h"
#include "portfolio.h"
#include "run_config.h"
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

class RecordProjector {

private:
    const CRunConfig &_run_config;
    const TimeAxis &_ta;
public:

    RecordProjector(const CRunConfig &run_config, const TimeAxis & ta): _run_config(run_config), _ta(ta)
    {}

    // clear the temporary values
    void clear() {
    }

    void run(int runner_no, int record_count, CPolicy &policy, RunResult& result) {
        clear();

        if (record_count % 1000 == 0) {
            cout << "Projector for runner #" << runner_no << ", record_count=" << record_count << ", ID=" << policy.get_cession_id() << endl;
        }

        this->clear();

        // specialize the assumption providers for the current record

    }
};


#endif
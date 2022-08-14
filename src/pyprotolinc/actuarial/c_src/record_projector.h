

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
#include "run_result.h"


using namespace std;




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
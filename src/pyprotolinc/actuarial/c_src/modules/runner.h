
/* CPP implementation of the assumption providers. */

#ifndef C_VALUATION_RUNNER_H
#define C_VALUATION_RUNNER_H

#include <vector>
#include <string>
#include <iostream>
#include <memory>
#include "assumption_sets.h"
#include "providers.h"
#include "portfolio.h"
#include "run_config.h"
#include "record_projector.h"
#include "time_axis.h"
#include "run_result.h"


using namespace std;


// class RecordProjector {

// private:
//     const CRunConfig &_run_config;
// public:

//     RecordProjector(const CRunConfig &run_config): _run_config(run_config)
//     {}

//     void clear() {
//     }

//     void run(int runner_no, int record_count, CPolicy &policy) {
//         if (record_count % 1000 == 0)
//             cout << "Projector for runner #" << runner_no << ", record_count=" << record_count << ", ID=" << policy.get_cession_id() << endl;
//     }
// };




class Runner {
private:

    int _runner_no;

    const CRunConfig &_run_config;

    const shared_ptr<CPolicyPortfolio> _ptr_portfolio;
    
    TimeAxis _ta;

    // projection engine for single policy
    RecordProjector _record_projector;

    // the result of the single record
    RunResult record_result;

public:

    Runner(int runner_no, shared_ptr<CPolicyPortfolio> ptr_portfolio, const CRunConfig &run_config):
        _runner_no(runner_no),
        _ptr_portfolio(ptr_portfolio),
        _run_config (run_config),
        _ta(TimeAxis(run_config.get_time_step(), run_config.get_years_to_simulate(), ptr_portfolio->_ptf_year,  ptr_portfolio->_ptf_month,  ptr_portfolio->_ptf_day)),
        _record_projector(RecordProjector(run_config, _ta)),
        record_result(_ta)
    {}
    
    void run(RunResult &run_result) {
        // TODO: create time axis object from configuration
        cout << "RUNNER " << _runner_no << " run()" <<  "Portfolio size is " << _ptr_portfolio->size() << ". "<<endl;

        int record_count = 0;
        for(auto record_ptr: _ptr_portfolio->get_policies()) {
            record_count++;
            record_result.reset();
            _record_projector.run(_runner_no, record_count, *record_ptr, record_result);
            run_result.add_result(record_result);
        }
    }
};



/// The runner object.
class MetaRunner
{
protected:
    const CRunConfig &run_config;

    const shared_ptr<CPolicyPortfolio> ptr_portfolio;
    
    TimeAxis _ta;

public:
    MetaRunner(const CRunConfig &_run_config,
               const shared_ptr<CPolicyPortfolio> _ptr_portfolio) : run_config(_run_config),
                                                                    ptr_portfolio(_ptr_portfolio),
                                                                    _ta(TimeAxis(_run_config.get_time_step(),
                                                                                 _run_config.get_years_to_simulate(),
                                                                                 _ptr_portfolio->_ptf_year,
                                                                                 _ptr_portfolio->_ptf_month,
                                                                                 _ptr_portfolio->_ptf_day))
    {
        if (!_ptr_portfolio)
        {
            throw domain_error("Portfolio must not be null!");
        }
    }

    /// Calculate the number of groups the portfolio will be split into
    int get_num_groups()
    {
        if (!run_config.get_use_multicore())
        {
            return 1;
        }
        int cpu_count = run_config.get_cpu_count();
        int ptf_size = ptr_portfolio->size();

        // make sure we have at least four policies in each group
        int tmp = cpu_count < ptf_size / 4 ? cpu_count : ptf_size / 4;
        return tmp == 0 ? 1 : tmp;
    }

    // calculate the result and storein ext_result
    void run(RunResult &run_result)
    // void run(double *ext_result)
    {
        // some control output
        cout << "CRunner::run(): STARTING RUN" << endl;
        const CAssumptionSet &be_ass = run_config.get_be_assumptions();
        unsigned dimension = be_ass.get_dimension();

        cout << "CRunner::run(): dimension=" << be_ass.get_dimension() << endl;
        cout << "CRunner::run(): portfolio.size()=" << ptr_portfolio->size() << endl;

        for (unsigned r = 0; r < dimension; r++)
        {
            for (unsigned c = 0; c < dimension; c++)
            {
                cout << "CRunner::run(): (" << r << ", " << c << "): " << be_ass.get_provider_info(r, c) << endl;
            }
        }


        // split portfolio in N groups
        const int NUM_GROUPS = get_num_groups();
        cout << "NUM_GROUPS=" << NUM_GROUPS << endl;
        vector<shared_ptr<CPolicyPortfolio>> subportfolios(NUM_GROUPS);
        vector<Runner> runners = vector<Runner>();
        vector<RunResult> results = vector<RunResult>();
        for (int j = 0; j < NUM_GROUPS; j++)
        {
            subportfolios[j] = make_shared<CPolicyPortfolio>(ptr_portfolio->_ptf_year, ptr_portfolio->_ptf_month, ptr_portfolio->_ptf_day);
            runners.emplace_back(Runner(j+1, subportfolios[j], run_config));
            results.emplace_back(RunResult(_ta));
        }
        int subportfolio_index = 0;
        const vector<shared_ptr<CPolicy>> &policies = ptr_portfolio->get_policies();
        for (shared_ptr<CPolicy> record : policies)
        {
            subportfolios[subportfolio_index]->add(record);
            if (++subportfolio_index >= NUM_GROUPS)
            {
                subportfolio_index = 0;
            }
        }

        // // container for the result is a vector with entries
        // // for each local group. Each entry is an array
        // // with length 120*12*no_cols
        // // which is initialized with zero
        // vector<shared_ptr<double>> output_loc;
        // for(int j=0;j<NUM_GROUPS;j++) {
        //     std::shared_ptr<double> sp(new double[VECTOR_LENGTH_YEARS*12*no_cols], std::default_delete<double[]>());
        //     for(long k=0; k < VECTOR_LENGTH_YEARS * 12 * no_cols; k++) {
        //         sp.get()[k] = 0;
        //         //(*sp)[k] = 0;
        //     }
        //     output_loc.push_back(sp);
        // }

        // value subportfolios
#pragma omp parallel for
        for (int j = 0; j < NUM_GROUPS; j++)
        {
            runners[j].run(results[j]);
            //     // container for the local result
            //     //_valuation(output_loc[j], vecs[j], be_ass, locgaap_ass);
            //     _valuation(output_loc[j], no_cols, vecs[j], be_ass, locgaap_ass);
        }

        // combine the results of the subportfolios to combined result
        for (int j = 0; j < NUM_GROUPS; j++)
        {
            run_result.add_result(results[j]);
        }

        // copy result to external output
//        results[0].copy_results(ext_result);
        // // sum up the results just calculated
        // for (int k=0; k<NUM_GROUPS;k++) {
        //     for(int j=0; j<VECTOR_LENGTH_YEARS*12; j++) {
        //         // skip columns for year and month
        //         for (int i=2; i < no_cols; i++) {
        //             output[no_cols*j+i] += (output_loc[k]).get()[no_cols*j+i];
        //         }
        //     }
        // }

        // // set year and month
        // int pf_year = portfolio_year;
        // int pf_month = portfolio_month;
        // for(int j=0; j<VECTOR_LENGTH_YEARS*12; j++) {
        //     pf_month++;
        //     if (pf_month == 13) {
        //         pf_month = 1;
        //         pf_year++;
        //     }
        //     output[no_cols*j+0] = pf_year;
        //     output[no_cols*j+1] = pf_month;
        // }

        cout << "CRunner::run(): DONE" << endl;
    }
};




void run_c_valuation(const CRunConfig &run_config, shared_ptr<CPolicyPortfolio> ptr_portfolio, RunResult& run_result)
{
    cout << "run_c_valuation()" << endl;
    MetaRunner runner(run_config, ptr_portfolio);
    runner.run(run_result);
};

#endif
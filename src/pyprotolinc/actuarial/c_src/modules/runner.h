
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

class Runner
{
private:
    int _runner_no;

    const CRunConfig &_run_config;

    const shared_ptr<CPolicyPortfolio> _ptr_portfolio;

    const shared_ptr<TimeAxis> _ta;

    // projection engine for single policy
    RecordProjector _record_projector;

    // the result of the single record
    RunResult _record_result;

public:
    Runner(int runner_no, const shared_ptr<CPolicyPortfolio> ptr_portfolio,
           const CRunConfig &run_config, const shared_ptr<TimeAxis> ta) : _runner_no(runner_no),
                                                                          _ptr_portfolio(ptr_portfolio),
                                                                          _run_config(run_config),
                                                                          _ta(ta),
                                                                          _record_projector(RecordProjector(run_config, *_ta)),
                                                                          _record_result(_ta)
    {
    }

    void run(RunResult &run_result);
};

void Runner::run(RunResult &run_result)
{
    cout << "Runner::run(): RUNNER " << _runner_no << " run() - "
         << "Portfolio size is " << _ptr_portfolio->size() << ". " << endl;

    
    PeriodDate portfolio_date(_ptr_portfolio->_ptf_year, _ptr_portfolio->_ptf_month, _ptr_portfolio->_ptf_day);

    int record_count = 0;
    for (auto record_ptr : _ptr_portfolio->get_policies())
    {
        record_count++;
        _record_result.reset();
        //_record_projector->run(_runner_no, record_count, *record_ptr, record_result);
        _record_projector.run(_runner_no, record_count, *record_ptr, _record_result, portfolio_date);
        run_result.add_result(_record_result);
    }
}

/// The runner object.
class MetaRunner
{
protected:
    const CRunConfig &run_config;

    const shared_ptr<CPolicyPortfolio> ptr_portfolio;

    const shared_ptr<TimeAxis> _ta;

public:
    MetaRunner(const CRunConfig &_run_config,
               const shared_ptr<CPolicyPortfolio> _ptr_portfolio,
               const shared_ptr<TimeAxis> ta) : run_config(_run_config),
                                                ptr_portfolio(_ptr_portfolio),
                                                _ta(ta)
    {
        if (!_ptr_portfolio)
        {
            throw domain_error("Portfolio must not be null!");
        }
    }

    int get_num_groups();

    void run(RunResult &run_result);
};

/// Calculate the number of groups the portfolio will be split into
int MetaRunner::get_num_groups()
{
    if (!run_config.get_use_multicore())
    {
        return 1;
    }
    int cpu_count = run_config.get_cpu_count();
    int ptf_size = (int) ptr_portfolio->size();

    // make sure we have at least four policies in each group
    int tmp = cpu_count < ptf_size / 4 ? cpu_count : ptf_size / 4;
    return tmp == 0 ? 1 : tmp;
}

// calculate the result and store in ext_result
void MetaRunner::run(RunResult &run_result)
{
    cout << "MetaRunner::run(): STARTING RUN" << endl;
    const CAssumptionSet &be_ass = run_config.get_be_assumptions();
    unsigned dimension = be_ass.get_dimension();

    cout << "MetaRunner::run(): dimension=" << be_ass.get_dimension() << endl;
    cout << "MetaRunner::run(): portfolio.size()=" << ptr_portfolio->size() << endl;

    for (unsigned r = 0; r < dimension; r++)
    {
        for (unsigned c = 0; c < dimension; c++)
        {
            cout << "MetaRunner::run(): (" << r << ", " << c << "): " << be_ass.get_provider_info(r, c) << endl;
        }
    }

    // create N runners, run_results and sub-portfolios
    const int NUM_GROUPS = get_num_groups();
    cout << "MetaRunner::run(): NUM_GROUPS=" << NUM_GROUPS << endl;
    vector<shared_ptr<CPolicyPortfolio>> subportfolios(NUM_GROUPS);
    vector<Runner> runners = vector<Runner>();
    vector<RunResult> results = vector<RunResult>();
    for (int j = 0; j < NUM_GROUPS; j++)
    {
        subportfolios[j] = make_shared<CPolicyPortfolio>(ptr_portfolio->_ptf_year, ptr_portfolio->_ptf_month, ptr_portfolio->_ptf_day);
        runners.emplace_back(Runner(j + 1, subportfolios[j], run_config, _ta));
        results.emplace_back(RunResult(_ta));
    }

    // split portfolio into N groups
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

    // value subportfolios
#pragma omp parallel for
    for (int j = 0; j < NUM_GROUPS; j++)
    {
        runners[j].run(results[j]);
    }

    // combine the results of the subportfolios to combined result
    for (int j = 0; j < NUM_GROUPS; j++)
    {
        run_result.add_result(results[j]);
    }

    cout << "MetaRunner::run(): DONE" << endl;
}


// Interface-Function to the Python-Code
void run_c_valuation(const CRunConfig &run_config, shared_ptr<CPolicyPortfolio> ptr_portfolio, RunResult &run_result)
{
    cout << "run_c_valuation()" << endl;

    shared_ptr<TimeAxis> p_time_axis = make_shared<TimeAxis>(run_config.get_time_step(),
                                                             run_config.get_years_to_simulate(),
                                                             ptr_portfolio->_ptf_year,
                                                             ptr_portfolio->_ptf_month,
                                                             ptr_portfolio->_ptf_day);
    
    run_result.set_time_axis(p_time_axis);

    MetaRunner runner(run_config, ptr_portfolio, p_time_axis);
    runner.run(run_result);
};

#endif
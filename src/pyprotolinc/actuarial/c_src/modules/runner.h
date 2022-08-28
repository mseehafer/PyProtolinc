/**
 * @file runner.h
 * @author M. Seehafer
 * @brief Runner objects that encapsulate the projection engine and provide an interface to the calculation functionality.
 * @version 0.1
 * @date 2022-08-27
 * 
 * @copyright Copyright (c) 2022
 * 
 */


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

/**
 * @brief Provides an interface to the calculation functionality for a portfolio that will be made in one sequential batch.
 * 
 */
class Runner
{
private:
    ///< Number of this runner.
    int _runner_no;

    ///< Run configuration object.
    const CRunConfig &_run_config;

    ///< The (sub-)portfolio that shall be valued.
    const shared_ptr<CPolicyPortfolio> _ptr_portfolio;

    ///< Time axis to be used for the simulation.
    const shared_ptr<TimeAxis> _ta;

    ///< projection engine for single policy
    RecordProjector _record_projector;

    ///< the result of the single record
    RunResult _record_result;

public:
    /**
     * @brief Construct a new Runner object
     * 
     * @param runner_no Number of this runner.
     * @param ptr_portfolio The (sub-)portfolio of type CPolicyPortfolio that shall be valued.
     * @param run_config  CRunConfig configuration object.
     * @param ta Time axis to be used for the simulation.
     */
    Runner(int runner_no, const shared_ptr<CPolicyPortfolio> ptr_portfolio,
           const CRunConfig &run_config, const shared_ptr<TimeAxis> ta) : _runner_no(runner_no),
                                                                          _ptr_portfolio(ptr_portfolio),
                                                                          _run_config(run_config),
                                                                          _ta(ta),
                                                                          _record_projector(RecordProjector(run_config, *_ta)),
                                                                          _record_result(run_config.get_dimension(), _ta)
    {
    }

    /// Starts the main loop over the policies in the portfolio and combines the results.
    void run(RunResult &run_result);
};

void Runner::run(RunResult &run_result)
{
    // cout << "Runner::run(): RUNNER " << _runner_no << " run() - "
    //      << "Portfolio size is " << _ptr_portfolio->size() << ". " << endl;

    PeriodDate portfolio_date(_ptr_portfolio->get_portfolio_date());

    int record_count = 0;
    for (auto record_ptr : _ptr_portfolio->get_policies())
    {
        record_count++;
        _record_result.reset();
        _record_projector.run(_runner_no, record_count, *record_ptr, _record_result, portfolio_date);
        run_result.add_result(_record_result);
    }
}

/**
 * @brief The MetaRunner object. Splits the portfolio and triggers a (possibly) parallelized run
 * by instantiating several runner objects, starting them and combining their results.
 * 
 */
class MetaRunner
{
protected:
    const CRunConfig &_run_config;

    const shared_ptr<CPolicyPortfolio> _ptr_portfolio;

    const shared_ptr<TimeAxis> _ta;

public:
    /**
     * @brief Construct a new Meta Runner object
     * 
     * @param run_config Run configutaion object
     * @param ptr_portfolio Pointer to portfolio of policies.
     * @param ta TimeAxis object to be used for the calculation.
     */
    MetaRunner(const CRunConfig &run_config,
               const shared_ptr<CPolicyPortfolio> ptr_portfolio,
               const shared_ptr<TimeAxis> ta) : _run_config(run_config),
                                                _ptr_portfolio(ptr_portfolio),
                                                _ta(ta)
    {
        if (!_ptr_portfolio)
        {
            throw domain_error("Portfolio must not be null!");
        }
    }

    ///> Calculates into how many sub-portfolios the portfolio will be split into
    ///> depending on the cpu_count/use_multicore settings in the config and the portfolio size.
    int get_num_groups();

    ///> Calculate the result and store it in the reference passed in.
    ///>
    void run(RunResult &run_result);
};

int MetaRunner::get_num_groups()
{
    if (!_run_config.get_use_multicore())
    {
        return 1;
    }
    int cpu_count = _run_config.get_cpu_count();
    int ptf_size = (int) _ptr_portfolio->size();

    // make sure we have at least four policies in each group
    int tmp = cpu_count < ptf_size / 4 ? cpu_count : ptf_size / 4;
    return tmp == 0 ? 1 : tmp;
}


void MetaRunner::run(RunResult &run_result)
{
    cout << "MetaRunner::run(): STARTING RUN" << endl;
    const CAssumptionSet &be_ass = _run_config.get_be_assumptions();
    unsigned dimension = be_ass.get_dimension();

    cout << "MetaRunner::run(): dimension=" << be_ass.get_dimension() << endl;
    cout << "MetaRunner::run(): portfolio.size()=" << _ptr_portfolio->size() << endl;

    // for (unsigned r = 0; r < dimension; r++)
    // {
    //     for (unsigned c = 0; c < dimension; c++)
    //     {
    //         cout << "MetaRunner::run(): (" << r << ", " << c << "): " << be_ass.get_provider_info(r, c) << endl;
    //     }
    // }

    // create N runners, run_results and sub-portfolios
    const int NUM_GROUPS = get_num_groups();
    cout << "MetaRunner::run(): NUM_GROUPS=" << NUM_GROUPS << endl;
    vector<shared_ptr<CPolicyPortfolio>> subportfolios(NUM_GROUPS);
    vector<Runner> runners = vector<Runner>();
    vector<RunResult> results = vector<RunResult>();
    for (int j = 0; j < NUM_GROUPS; j++)
    {
        //subportfolios[j] = make_shared<CPolicyPortfolio>(_ptr_portfolio->_ptf_year, _ptr_portfolio->_ptf_month, _ptr_portfolio->_ptf_day);
        subportfolios[j] = make_shared<CPolicyPortfolio>(_ptr_portfolio->get_portfolio_date());
        runners.emplace_back(Runner(j + 1, subportfolios[j], _run_config, _ta));
        results.emplace_back(RunResult(_run_config.get_dimension(), _ta));
    }

    // split portfolio into N groups
    int subportfolio_index = 0;
    const vector<shared_ptr<CPolicy>> &policies = _ptr_portfolio->get_policies();
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


/**
 * @brief External interface function to the calculation engine
 * 
 * @param run_config Config object used for the run.
 * @param ptr_portfolio Pointer to a portfolio object.
 * @param run_result Container to store the results in.
 */
unique_ptr<RunResult> run_c_valuation(const CRunConfig &run_config, shared_ptr<CPolicyPortfolio> ptr_portfolio) //, RunResult &run_result)
{
    cout << "run_c_valuation()" << endl;

    shared_ptr<TimeAxis> p_time_axis = make_shared<TimeAxis>(run_config.get_time_step(),
                                                             run_config.get_years_to_simulate(),
                                                             ptr_portfolio->get_portfolio_date().get_year(),
                                                             ptr_portfolio->get_portfolio_date().get_month(),
                                                             ptr_portfolio->get_portfolio_date().get_day());
    
    //run_result.set_time_axis(p_time_axis);

    unique_ptr<RunResult> run_res_ptr = unique_ptr<RunResult>(new RunResult(run_config.get_dimension(), p_time_axis));

    MetaRunner runner(run_config, ptr_portfolio, p_time_axis);
    runner.run(*run_res_ptr);

    return run_res_ptr;
};

#endif
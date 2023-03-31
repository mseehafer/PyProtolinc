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
#include "payments.h"

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

    const int _num_state_payment_cols;

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
           const CRunConfig &run_config, const shared_ptr<TimeAxis> ta, int num_state_payment_cols) : _runner_no(runner_no),
                                                                          _ptr_portfolio(ptr_portfolio),
                                                                          _run_config(run_config),
                                                                          _ta(ta),
                                                                          _record_projector(RecordProjector(run_config, *_ta)),
                                                                          _record_result(run_config.get_dimension(), _ta, num_state_payment_cols),
                                                                          _num_state_payment_cols(num_state_payment_cols)
    {
    }

    /// Starts the main loop over the policies in the portfolio and combines the results.
    void run(RunResult &run_result, const AggregatePayments &payments);
};

void Runner::run(RunResult &run_result, const AggregatePayments &payments)
{
    // cout << "Runner::run(): RUNNER " << _runner_no << " run() - "
    //      << "Portfolio size is " << _ptr_portfolio->size() << ". " << endl;

    PeriodDate portfolio_date(_ptr_portfolio->get_portfolio_date());

    int record_count = 0;
    for (auto record_ptr : _ptr_portfolio->get_policies())
    {
        shared_ptr<unordered_map<int, StateConditionalRecordPayout>> record_payments = payments.get_single_record_payments(record_count);
        // shared_ptr<unordered_map<int, StateConditionalRecordPayout>> &record_payments = payments.get_single_record_payments(record_count);

        record_count++;
        _record_result.reset();
        _record_projector.run(_runner_no, record_count, *record_ptr, _record_result, portfolio_date, record_payments);
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

    const int _num_state_payment_cols;

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
               const shared_ptr<TimeAxis> ta,
               const int num_state_payment_cols) : _run_config(run_config),
                                                   _ptr_portfolio(ptr_portfolio),
                                                   _ta(ta),
                                                   _num_state_payment_cols(num_state_payment_cols)
    {
        if (!_ptr_portfolio)
        {
            throw domain_error("Portfolio must not be null!");
        }
    }

    ///> Calculates into how many sub-portfolios the portfolio will be split into
    ///> depending on the cpu_count/use_multicore settings in the config and the portfolio size.
    int get_num_groups() const;

    ///> Calculate the result and store it in the reference passed in.
    ///>
    void run(RunResult &run_result, const AggregatePayments &agg_payments) const;  // check if const?
};

int MetaRunner::get_num_groups() const
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


void MetaRunner::run(RunResult &run_result, const AggregatePayments &agg_payments) const
{
    cout << "MetaRunner::run(): STARTING RUN, portfolio.size()=" << _ptr_portfolio->size() << endl;
    const CAssumptionSet &be_ass = _run_config.get_be_assumptions();
    unsigned dimension = be_ass.get_dimension();

    //cout << "MetaRunner::run(): dimension=" << be_ass.get_dimension() << endl;
    //cout << "MetaRunner::run(): portfolio.size()=" << _ptr_portfolio->size() << endl;

    // for (unsigned r = 0; r < dimension; r++)
    // {
    //     for (unsigned c = 0; c < dimension; c++)
    //     {
    //         cout << "MetaRunner::run(): (" << r << ", " << c << "): " << be_ass.get_provider_info(r, c) << endl;
    //     }
    // }

    // create N runners, run_results and sub-portfolios
    const int NUM_GROUPS = get_num_groups();
    // cout << "MetaRunner::run(): NUM_GROUPS=" << NUM_GROUPS << endl;
    vector<shared_ptr<CPolicyPortfolio>> subportfolios(NUM_GROUPS);
    vector<Runner> runners = vector<Runner>();
    vector<RunResult> results = vector<RunResult>();
    vector<AggregatePayments> sub_ptf_payments = vector<AggregatePayments>();

    // when splitting the portfolios the size may vary by one depedning on the size and
    // the number of groups
    int base_size = _ptr_portfolio->size() / NUM_GROUPS;
    int num_of_groups_with_one_record_more = _ptr_portfolio->size() - NUM_GROUPS * base_size;
    for (int j = 0; j < NUM_GROUPS; j++)
    {
        //subportfolios[j] = make_shared<CPolicyPortfolio>(_ptr_portfolio->_ptf_year, _ptr_portfolio->_ptf_month, _ptr_portfolio->_ptf_day);
        subportfolios[j] = make_shared<CPolicyPortfolio>(_ptr_portfolio->get_portfolio_date());
        runners.emplace_back(Runner(j + 1, subportfolios[j], _run_config, _ta, _num_state_payment_cols));
        results.emplace_back(RunResult(_run_config.get_dimension(), _ta, _num_state_payment_cols));
        
        sub_ptf_payments.emplace_back(AggregatePayments(base_size +  (j < num_of_groups_with_one_record_more ? 1 : 0), agg_payments.get_payment_types_used()));
    }

    // split portfolio into N groups
    int subportfolio_index = 0;
    size_t overall_index = 0;
    const vector<shared_ptr<CPolicy>> &policies = _ptr_portfolio->get_policies();
    size_t index_in_group = 0;
    for (shared_ptr<CPolicy> record : policies)
    {
        subportfolios[subportfolio_index]->add(record);
        AggregatePayments &this_sub_ptf_payments = sub_ptf_payments[subportfolio_index];
        this_sub_ptf_payments.add_single_record_payments(agg_payments.get_single_record_payments(overall_index), index_in_group);
        if (++subportfolio_index >= NUM_GROUPS)
        {
            subportfolio_index = 0;
            index_in_group++;
        }
        overall_index++;
    }

    // value subportfolios
#pragma omp parallel for
    for (int j = 0; j < NUM_GROUPS; j++)
    {
        runners[j].run(results[j], sub_ptf_payments[j]);
    }

    // combine the results of the subportfolios to combined result
    for (int j = 0; j < NUM_GROUPS; j++)
    {
        run_result.add_result(results[j]);
    }

    cout << "MetaRunner::run(): DONE" << endl;
}


/**
 * @brief RunnerInterface is the external run interface
 * 
 */
class RunnerInterface
{
private:
    const CRunConfig &_run_config;
    const shared_ptr<CPolicyPortfolio> _ptr_portfolio;
    const shared_ptr<TimeAxis> _p_time_axis;
    AggregatePayments agg_payments;

public:
    RunnerInterface(const CRunConfig &run_config, shared_ptr<CPolicyPortfolio> ptr_portfolio):
         _run_config(run_config),
         _ptr_portfolio(ptr_portfolio),
         _p_time_axis(make_shared<TimeAxis>(run_config.get_time_step(),
                                            run_config.get_years_to_simulate(),
                                            ptr_portfolio->get_portfolio_date().get_year(),
                                            ptr_portfolio->get_portfolio_date().get_month(),
                                            ptr_portfolio->get_portfolio_date().get_day())),
        agg_payments(ptr_portfolio->size())         
        {}
            
    shared_ptr<TimeAxis> get_time_axis() const { return _p_time_axis;}

    void add_cond_state_payment(int state_index, int payment_type_index, double *payment_matrix)
    {
        agg_payments.add_cond_state_payment(state_index, payment_type_index, payment_matrix, _ptr_portfolio->size(), _p_time_axis->get_length());
    }

    /// @brief Start the calculation run
    /// @return Pointer to result
    unique_ptr<RunResult> run() const
    {
        int num_state_payment_cols = 1 + agg_payments.get_max_payment_index_used();
        // cout << "num_state_payment_cols=" << num_state_payment_cols << std::endl;

        MetaRunner _runner(_run_config, _ptr_portfolio, _p_time_axis, num_state_payment_cols);
        unique_ptr<RunResult> run_res_ptr = unique_ptr<RunResult>(new RunResult(_run_config.get_dimension(), _p_time_axis, num_state_payment_cols));
        _runner.run(*run_res_ptr, agg_payments);
        return run_res_ptr;        
    }
};



/**
 * @brief External interface function to the calculation engine
 * 
 * @param run_config Config object used for the run.
 * @param ptr_portfolio Pointer to a portfolio object.
 * @param run_result Container to store the results in.
 */
unique_ptr<RunResult> run_c_valuation(const CRunConfig &run_config, shared_ptr<CPolicyPortfolio> ptr_portfolio)
{
    RunnerInterface ri(run_config, ptr_portfolio);
    return ri.run();
};



#endif
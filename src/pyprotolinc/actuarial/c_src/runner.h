
/* CPP implementation of the assumption providers. */

#ifndef C_VALUATION_RUNNER_H
#define C_VALUATION_RUNNER_H

#include <vector>
#include <string>
#include <iostream>
#include "assumption_sets.h"
#include "providers.h"
#include "portfolio.h"

using namespace std;

class CRunConfig
{

protected:
    // dimension of the state model
    unsigned int dimension;

    int num_cpus;
    bool use_multicore;

    // valuation assumptions
    shared_ptr<CAssumptionSet> be_assumptions;
    shared_ptr<vector<shared_ptr<CAssumptionSet>>> other_assumptions = make_shared<vector<shared_ptr<CAssumptionSet>>>();
    // nullptr;

public:
    CRunConfig(unsigned _dim, int _num_cpus, bool _use_multicore, shared_ptr<CAssumptionSet> _be_assumptions) : dimension(_dim), num_cpus(_num_cpus),
                                                                                                                use_multicore(_use_multicore), be_assumptions(_be_assumptions)
    {
        // other_assumptions = make_shared<vector<shared_ptr<CAssumptionSet>>>(new vector<shared_ptr<CAssumptionSet>>());
        if (!_be_assumptions)
        {
            throw domain_error("Assumption set pointer must not be null!");
        }
        if (_be_assumptions->get_dimension() != _dim)
        {
            throw domain_error("Dimension of assumptions set and the one passed in must match");
        }
    }

    int get_cpu_count() const { return num_cpus; }
    bool get_use_multicore() const { return use_multicore; }

    void add_assumption_set(shared_ptr<CAssumptionSet> as)
    {

        // if (!other_assumptions) {
        //     other_assumptions = make_shared<vector<shared_ptr<CAssumptionSet>>>();
        // }
        other_assumptions->push_back(as);
    }

    const CAssumptionSet &get_be_assumptions() const
    {
        return *be_assumptions;
    }

    const vector<shared_ptr<CAssumptionSet>> &get_other_assumptions() const
    {
        return *other_assumptions;
    }
};


/// The runner object.
class MetaRunner
{
protected:
    const CRunConfig &run_config;

    const shared_ptr<CPolicyPortfolio> ptr_portfolio;

public:
    MetaRunner(const CRunConfig &_run_config,
               const shared_ptr<CPolicyPortfolio> _ptr_portfolio) : run_config(_run_config), ptr_portfolio(_ptr_portfolio)
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

    void run()
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
        for (int j = 0; j < NUM_GROUPS; j++)
        {
            subportfolios[j] = make_shared<CPolicyPortfolio>(ptr_portfolio->_ptf_year, ptr_portfolio->_ptf_month, ptr_portfolio->_ptf_day);
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
            //     // container for the local result
            //     //_valuation(output_loc[j], vecs[j], be_ass, locgaap_ass);
            //     _valuation(output_loc[j], no_cols, vecs[j], be_ass, locgaap_ass);
        }

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

void run_c_valuation(const CRunConfig &run_config, shared_ptr<CPolicyPortfolio> ptr_portfolio)
{
    cout << "run_c_valuation()" << endl;
    MetaRunner runner(run_config, ptr_portfolio);
    runner.run();
};

#endif
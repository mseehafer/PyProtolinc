
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


class CRunConfig {

protected:

    // dimension of the state model
    unsigned int dimension;

    
    
    // valuation assumptions
    shared_ptr<CAssumptionSet> be_assumptions;
    shared_ptr<vector<shared_ptr<CAssumptionSet>>> other_assumptions = make_shared<vector<shared_ptr<CAssumptionSet>>>();
    // nullptr;

public:
    CRunConfig(unsigned _dim, shared_ptr<CAssumptionSet> _be_assumptions): dimension(_dim),
                                                                           be_assumptions(_be_assumptions)
    {
        //other_assumptions = make_shared<vector<shared_ptr<CAssumptionSet>>>(new vector<shared_ptr<CAssumptionSet>>());
        if (!_be_assumptions) {
            throw domain_error("Assumption set pointer must not be null!");
        }
        if (_be_assumptions->get_dimension() != _dim) {
            throw domain_error("Dimension of assumptions set and the one passed in must match");
        }
    }

    void add_assumption_set(shared_ptr<CAssumptionSet> as) {
        
        // if (!other_assumptions) {
        //     other_assumptions = make_shared<vector<shared_ptr<CAssumptionSet>>>();
        // }
        other_assumptions->push_back(as);
    }

    const CAssumptionSet & get_be_assumptions() const {
        return *be_assumptions;
    }

    const vector<shared_ptr<CAssumptionSet>>& get_other_assumptions() const {
        return *other_assumptions;
    }

};



/// The runner object.
class CRunner
{
protected:
    const CRunConfig &run_config;

    const shared_ptr<CPolicyPortfolio> ptr_portfolio;

public:
    CRunner (const CRunConfig &_run_config,
             const shared_ptr<CPolicyPortfolio> _ptr_portfolio): run_config(_run_config), ptr_portfolio(_ptr_portfolio) {
        if (!_ptr_portfolio) {
            throw domain_error("Portfolio must not be null!");
        }
    }

    void run() {
        cout << "CRunner::run(): STARTING RUN" << endl;
        const CAssumptionSet & be_ass = run_config.get_be_assumptions();
        unsigned dimension = be_ass.get_dimension();
        
        cout << "CRunner::run(): dimension=" << be_ass.get_dimension() << endl;
        cout << "CRunner::run(): portfolio.size()=" << ptr_portfolio->size() << endl;

        for (unsigned r = 0; r < dimension; r++) {
            for (unsigned c = 0; c < dimension; c++) {
                cout << "CRunner::run(): (" << r << ", " << c << "): " << be_ass.get_provider_info(r, c) << endl;
            }
        }
        

        cout << "CRunner::run(): DONE" << endl;
    }
};       


void run_c_valuation(const CRunConfig &run_config, shared_ptr<CPolicyPortfolio> ptr_portfolio) {
    cout << "run_c_valuation()" << endl;
    CRunner runner(run_config, ptr_portfolio);
    runner.run();
};

#endif
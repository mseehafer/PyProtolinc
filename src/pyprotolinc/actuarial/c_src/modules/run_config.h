/* Configuration object for a run. */

#ifndef C_RUNCONFIG_H
#define C_RUNCONFIG_H

#include <vector>
#include <string>
#include <iostream>
#include <memory>
#include "time_axis.h"
#include "assumption_sets.h"
// #include "providers.h"
// #include "portfolio.h"

using namespace std;

class CRunConfig
{

protected:
    // dimension of the state model
    unsigned int dimension;

    TimeStep _time_step;
    int _years_to_simulate;

    int _num_cpus;
    bool _use_multicore;

    // valuation assumptions
    shared_ptr<CAssumptionSet> be_assumptions;
    shared_ptr<vector<shared_ptr<CAssumptionSet>>> other_assumptions = make_shared<vector<shared_ptr<CAssumptionSet>>>();
    // nullptr;

public:
    CRunConfig(unsigned _dim, TimeStep time_step, int years_to_simulate, int num_cpus, bool use_multicore, shared_ptr<CAssumptionSet> _be_assumptions):
        dimension(_dim),
        _time_step(time_step),
        _years_to_simulate(years_to_simulate),
        _num_cpus(num_cpus),
        _use_multicore(use_multicore),
        be_assumptions(_be_assumptions)
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

    int get_cpu_count() const { return _num_cpus; }
    bool get_use_multicore() const { return _use_multicore; }
    TimeStep get_time_step() const { return _time_step; }
    int get_years_to_simulate() const { return _years_to_simulate;}

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

    // int get_total_timesteps() const {
    //     return  get_total_steps(_time_step, _years_to_simulate);
    // }
};


shared_ptr<TimeAxis> make_time_axis(const CRunConfig &run_config, short _ptf_year, short _ptf_month, short _ptf_day) {
    return make_shared<TimeAxis>(run_config.get_time_step(), run_config.get_years_to_simulate(), _ptf_year,  _ptf_month,  _ptf_day);
};



#endif
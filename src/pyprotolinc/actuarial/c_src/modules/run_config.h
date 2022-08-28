/**
 * @file run_config.h
 * @author M. Seehafer
 * @brief Configuration object for a run. The settings stored here control the flow of the calculation and the parameters used.
 * @version 0.1
 * @date 2022-08-27
 * 
 * @copyright Copyright (c) 2022
 * 
 * 
 */

#ifndef C_RUNCONFIG_H
#define C_RUNCONFIG_H

#include <vector>
#include <string>
#include <iostream>
#include <memory>
#include "time_axis.h"
#include "assumption_sets.h"

using namespace std;

/**
 * @brief Container with configuration parameters.
 * 
 */
class CRunConfig
{

private:
    ///< dimension of the state model
    unsigned int dimension;

    ///< Time scale on which to calculate
    TimeStep _time_step;

    ///< Time scale on which to calculate
    int _years_to_simulate;

    ///< Number of cpus to use
    int _num_cpus;

    ///< Use multicore flag
    bool _use_multicore;

    // valuation assumptions
    shared_ptr<CAssumptionSet> be_assumptions;
    shared_ptr<vector<shared_ptr<CAssumptionSet>>> other_assumptions = make_shared<vector<shared_ptr<CAssumptionSet>>>();

public:
    /**
     * @brief Construct a new CRunConfig object
     * 
     * @param _dim Dimension of the state model
     * @param time_step Time scale on which to calculate
     * @param years_to_simulate Number of years to project into the future
     * @param num_cpus Number of cpus to use if `use_multicore=true`
     * @param use_multicore Use multicore flag
     * @param _be_assumptions Best estimate assumptions
     */
    CRunConfig(unsigned _dim, TimeStep time_step, int years_to_simulate, int num_cpus, bool use_multicore, shared_ptr<CAssumptionSet> _be_assumptions):
        dimension(_dim),
        _time_step(time_step),
        _years_to_simulate(years_to_simulate),
        _num_cpus(num_cpus),
        _use_multicore(use_multicore),
        be_assumptions(_be_assumptions)
    {
        if (!_be_assumptions)
        {
            throw domain_error("Assumption set pointer must not be null!");
        }
        if (_be_assumptions->get_dimension() != _dim)
        {
            throw domain_error("Dimension of assumptions set and the one passed in must match");
        }
    }

    int get_cpu_count() const { return _num_cpus; }                     ///< Returns the number of cpus to use if `use_multicore=true`
    bool get_use_multicore() const { return _use_multicore; }           ///< Returns if multiple core should be used
    TimeStep get_time_step() const { return _time_step; }               ///< Returns the time scale on which to calculate
    int get_years_to_simulate() const { return _years_to_simulate;}     ///< Returns the umber of years to project into the future
    unsigned int get_dimension() const { return dimension; }            ///< Returns the dimension of the state model

    /// Add an auxiliary assumption set.
    void add_assumption_set(shared_ptr<CAssumptionSet> as)
    {
        other_assumptions->push_back(as);
    }

    /// Get the main assumption set
    const CAssumptionSet &get_be_assumptions() const
    {
        return *be_assumptions;
    }

    /// Get the other auxilary assumption sets
    const vector<shared_ptr<CAssumptionSet>> &get_other_assumptions() const
    {
        return *other_assumptions;
    }

};



#endif
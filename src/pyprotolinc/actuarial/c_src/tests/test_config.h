#ifndef TEST_CONFIG_H
#define TEST_CONFIG_H


#include <gtest/gtest.h>

// #include "../modules/portfolio.h"
#include "../modules/run_config.h"
#include "../modules/assumption_sets.h"



//////////////////////////////////////////////////////////////////////
//
// Config creation
//
//////////////////////////////////////////////////////////////////////

TEST(test_config, create)
{
    unsigned state_dimension = 2;
    TimeStep time_step = TimeStep::MONTHLY;
    int years_to_simulate = 10;
    int num_cpus = 1;
    bool use_multicore = false;
    int max_age = 120;

    // test that assumptions set must not be null
    shared_ptr<CAssumptionSet> _be_assumptions = nullptr;
    ASSERT_ANY_THROW(CRunConfig(state_dimension, time_step, years_to_simulate, num_cpus, use_multicore, _be_assumptions, max_age));

    // create assumptions sets
    _be_assumptions = make_shared<CAssumptionSet>(state_dimension);
    shared_ptr<CBaseRateProvider> rp = make_shared<CConstantRateProvider>(0.5);
    _be_assumptions->set_provider(0, 1, rp);

    // create config
    auto run_config = CRunConfig(state_dimension, time_step, years_to_simulate, num_cpus, use_multicore, _be_assumptions, max_age);
    EXPECT_EQ(run_config.get_time_step(), time_step);
}


#endif
#ifndef TEST_ASSUMPTIONS_H
#define TEST_ASSUMPTIONS_H

/* Testing of the time_axis class. */

#include <gtest/gtest.h>

// #include "../modules/portfolio.h"
//#include "../modules/time_axis.h"
//#include "../modules/run_config.h"
#include "../modules/assumption_sets.h"

//////////////////////////////////////////////////////////////////////
//
// Assupmtions
//
//////////////////////////////////////////////////////////////////////

TEST(assumptions, const_provider_create)
{
    shared_ptr<CBaseRateProvider> rp = make_shared<CConstantRateProvider>(0.5);
    EXPECT_EQ(rp->to_string(), "<CConstantRateProvider with constant 0.500000>");

    // dummy index vectors needed in this case
    const std::vector<int> index;
    const std::vector<int *> indexes;
    EXPECT_EQ(rp->get_rate(index), 0.5);

    size_t num_results = 4;
    auto results = std::unique_ptr<double[]>(new double[num_results], std::default_delete<double[]>());

    // get rates vector
    rp->get_rates(results.get(), num_results, indexes);
    for (int i = 0; i < num_results; ++i)
    {
        EXPECT_EQ(results[i], 0.5) << "Vectors x and y differ at index " << i;
    }
}


TEST(assumptions, standard_provider_create)
{
    // create provider with two risk factors and set some values
    shared_ptr<CStandardRateProvider> srp = make_shared<CStandardRateProvider>();
    srp->add_risk_factor(CRiskFactors::Age);
    srp->add_risk_factor(CRiskFactors::Gender);
    vector<int> shape_vec = {2, 3};
    vector<int> offsets = {0, 0};
    double ext_vals[] = {0.1, 0.2, 0.3,
                         0.4, 0.5, 0.6};

    srp->set_values(shape_vec, offsets, ext_vals);


    EXPECT_EQ(srp->to_string(), "<CStandardRateProvider with RF (Age, Gender)>");

    // check values
    vector<int> query_indexes = {0, 0};
    for (int r = 0; r < shape_vec[0]; r++) {
        for (int c = 0; c < shape_vec[1]; c++) {
            query_indexes[0] = r;
            query_indexes[1] = c;
            EXPECT_EQ(srp->get_rate(query_indexes), ext_vals[r*shape_vec[1] + c]);
        }
    }
            
}


TEST(assumptions, standard_provider_slicing)
{
    // create provider as above
    shared_ptr<CStandardRateProvider> srp = make_shared<CStandardRateProvider>();
    srp->add_risk_factor(CRiskFactors::Age);
    srp->add_risk_factor(CRiskFactors::Gender);
    vector<int> shape_vec = {2, 3};
    vector<int> offsets = {0, 0};
    double ext_vals[] = {0.1, 0.2, 0.3,
                         0.4, 0.5, 0.6};
    srp->set_values(shape_vec, offsets, ext_vals);

    // clone provider
    auto srp_cloned = srp->clone();

    // now slice the cloned object
    vector<int> slice_indexes = {-1, 0};  // grab first column
    srp->slice_into(slice_indexes, srp_cloned.get());

    EXPECT_EQ(srp_cloned->to_string(), "<CStandardRateProvider with RF (Age)>");
    vector<int> query_indexes1d = {0};
    for (int r = 0; r < shape_vec[0]; r++) {
            query_indexes1d[0] = r;
            EXPECT_EQ(srp_cloned->get_rate(query_indexes1d), ext_vals[r*shape_vec[1] + 0]);
    }    

    // another slice
    vector<int> slice_indexes2 = {-1, 1};  // grab middle column
    srp->slice_into(slice_indexes2, srp_cloned.get() );
    EXPECT_EQ(srp_cloned->to_string(), "<CStandardRateProvider with RF (Age)>");
    for (int r = 0; r < shape_vec[0]; r++) {
            query_indexes1d[0] = r;
            EXPECT_EQ(srp_cloned->get_rate(query_indexes1d), ext_vals[r*shape_vec[1] + 1]);
    }    


    // another slice
    vector<int> slice_indexes3 = {-1, 2};  // third column
    srp->slice_into(slice_indexes3, srp_cloned.get());
    EXPECT_EQ(srp_cloned->to_string(), "<CStandardRateProvider with RF (Age)>");
    for (int r = 0; r < shape_vec[0]; r++) {
            query_indexes1d[0] = r;
            EXPECT_EQ(srp_cloned->get_rate(query_indexes1d), ext_vals[r*shape_vec[1] + 2]);
    }    

    // grab first column
    vector<int> slice_indexes4 = {0, -1};  // first row
    srp->slice_into(slice_indexes4, srp_cloned.get());
    EXPECT_EQ(srp_cloned->to_string(), "<CStandardRateProvider with RF (Gender)>");
    for (int c = 0; c < shape_vec[1]; c++) {
            query_indexes1d[0] = c;
            EXPECT_EQ(srp_cloned->get_rate(query_indexes1d), ext_vals[0*shape_vec[1] + c]);
    }    

    // grab second column
    vector<int> slice_indexes5 = {1, -1};  // first row
    srp->slice_into(slice_indexes5, srp_cloned.get());
    EXPECT_EQ(srp_cloned->to_string(), "<CStandardRateProvider with RF (Gender)>");
     for (int c = 0; c < shape_vec[1]; c++) {
            query_indexes1d[0] = c;
            EXPECT_EQ(srp_cloned->get_rate(query_indexes1d), ext_vals[1*shape_vec[1] + c]);
    }    

}


TEST(assumptions, set_create)
{

    unsigned state_dimension = 2;
    auto assumption_set = make_shared<CAssumptionSet>(state_dimension);

    // add a provider
    shared_ptr<CBaseRateProvider> rp = make_shared<CConstantRateProvider>(0.5);
    assumption_set->set_provider(0, 1, rp);
}

#endif
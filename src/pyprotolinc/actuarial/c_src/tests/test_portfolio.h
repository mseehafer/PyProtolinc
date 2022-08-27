#ifndef TEST_PORTFOLIO_H
#define TEST_PORTFOLIO_H

#include <gtest/gtest.h>

#include "../modules/portfolio.h"



TEST(test_policy, rate)
{
    CPolicy policy = CPolicy(1,            // cession_id,
                   19850407,     // dob_long,
                   20200801,     // issue_date_long,
                   0,            // disablement_date_long,
                   0,            // gender,
                   0,            // smoker_status,
                   100000,       //sum_insured,
                   0.02,         // reserving_rate,
                   "TERM",       // product
                   0             // initial state index
                   );

    double rate = policy.get_reserving_rate();
    EXPECT_DOUBLE_EQ(rate, 0.02);
}


TEST(test_policy, dob)
{
    CPolicy policy = CPolicy(1,            // cession_id,
                   19850407,     // dob_long,
                   20200801,     // issue_date_long,
                   0,            // disablement_date_long,
                   0,            // gender,
                   0,            // smoker_status,
                   100000,       //sum_insured,
                   0.02,         // reserving_rate,
                   "TERM",       // product
                   0             // initial state index
                   );

    int y = policy.get_dob().year;
    int m = policy.get_dob().month;
    int d = policy.get_dob().day;

    EXPECT_EQ(y, 1985);
    EXPECT_EQ(m, 4);
    EXPECT_EQ(d, 7);
}



TEST(test_portfolio, create)
{
    // create a policy
    shared_ptr<CPolicy> policy = make_shared<CPolicy>(
                   1,            // cession_id,
                   19850407,     // dob_long,
                   20200801,     // issue_date_long,
                   0,            // disablement_date_long,
                   0,            // gender,
                   0,            // smoker_status,
                   100000,       //sum_insured,
                   0.02,         // reserving_rate,
                   "TERM",       // product
                   0             // initial state index
                   );
    // create a portfolio with that policy
    short ptf_year = 2021;
    short ptf_month = 12;
    short ptf_day = 20;
    auto portfolio = make_shared<CPolicyPortfolio> (ptf_year, ptf_month, ptf_day);
    portfolio->add(policy);

    EXPECT_EQ(portfolio->size(), 1);

    // get the policy back from the portfolio
    const CPolicy &pol = portfolio->at(0);

    EXPECT_EQ(pol.get_cession_id(), policy->get_cession_id());

}


#endif
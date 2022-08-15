
#include <gtest/gtest.h>

#include "../modules/portfolio.h"



TEST(test_calculations, rate)
{
    CPolicy policy = CPolicy(1,            // cession_id,
                   19850407,     // dob_long,
                   20200801,     // issue_date_long,
                   0,            // disablement_date_long,
                   0,            // gender,
                   0,            // smoker_status,
                   100000,       //sum_insured,
                   0.02,         // reserving_rate,
                   "TERM"         // product
                   );

    double rate = policy.get_reserving_rate();
    EXPECT_DOUBLE_EQ(rate, 0.02);
}


TEST(test_calculations, dob)
{
    CPolicy policy = CPolicy(1,            // cession_id,
                   19850407,     // dob_long,
                   20200801,     // issue_date_long,
                   0,            // disablement_date_long,
                   0,            // gender,
                   0,            // smoker_status,
                   100000,       //sum_insured,
                   0.02,         // reserving_rate,
                   "TERM"         // product
                   );

    int y = policy.get_dob_year();
    int m = policy.get_dob_month();
    int d = policy.get_dob_day();

    EXPECT_EQ(y, 1985);
    EXPECT_EQ(m, 4);
    EXPECT_EQ(d, 7);
}

#ifndef TEST_TIMEAXIS_H
#define TEST_TIMEAXIS_H

#include <gtest/gtest.h>

// #include "../modules/portfolio.h"
#include "../modules/time_axis.h"


TEST(time_axis, monthly_dec)
{
    // set up time axis object
    TimeStep time_step = TimeStep::MONTHLY;
    int years_to_simulate = 4;
    short ptf_year = 2021;
    short ptf_month = 12;
    short ptf_day = 20;

    TimeAxis ta(time_step, years_to_simulate, ptf_year, ptf_month, ptf_day);

    const vector<PeriodDate> &start_dates = ta.get_start_dates();
    const vector<PeriodDate> &end_dates = ta.get_end_dates();
    const vector<int> &period_lengths = ta.get_period_length_in_days();

    // check starting/ending dates
    EXPECT_EQ(start_dates[0].day, ptf_day);
    EXPECT_EQ(start_dates[0].month, ptf_month);
    EXPECT_EQ(start_dates[0].year, ptf_year);

    // end date
    EXPECT_EQ(end_dates[end_dates.size() - 1].day, 31);
    EXPECT_EQ(end_dates[end_dates.size() - 1].month, 12);
    EXPECT_EQ(end_dates[end_dates.size() - 1].year, ptf_year + years_to_simulate);

    EXPECT_EQ(end_dates[0].day, ptf_day);
    EXPECT_EQ(end_dates[0].month, ptf_month);
    EXPECT_EQ(end_dates[0].year, ptf_year);
    EXPECT_EQ(period_lengths[0], 0);

    EXPECT_EQ(end_dates[1].day, 31);
    EXPECT_EQ(end_dates[1].month, 12);
    EXPECT_EQ(end_dates[1].year, 2021);
    EXPECT_EQ(period_lengths[1], 10); // this is waht we get with the 30/360 convention

    EXPECT_EQ(end_dates[2].day, 31);
    EXPECT_EQ(end_dates[2].month, 1);
    EXPECT_EQ(end_dates[2].year, 2022);
    EXPECT_EQ(period_lengths[2], 30);

    EXPECT_EQ(end_dates[3].day, 28);
    EXPECT_EQ(end_dates[3].month, 2);
    EXPECT_EQ(end_dates[3].year, 2022);
    EXPECT_EQ(period_lengths[3], 30);

    // output results:
    // for (size_t t=0; t < end_dates1.size(); t++) {
    //     cout << start_dates[t] << " - " << end_dates[t] << " : " << period_lengths[t] << endl;
    // }
}

TEST(time_axis, monthly_nov)
{
    // set up time axis object
    TimeStep time_step = TimeStep::MONTHLY;
    int years_to_simulate = 4;
    short ptf_year = 2021;
    short ptf_month = 11; // NOVEMBER
    short ptf_day = 20;

    TimeAxis ta(time_step, years_to_simulate, ptf_year, ptf_month, ptf_day);

    const vector<PeriodDate> &start_dates = ta.get_start_dates();
    const vector<PeriodDate> &end_dates = ta.get_end_dates();
    const vector<int> &period_lengths = ta.get_period_length_in_days();

    // check starting/ending dates
    EXPECT_EQ(start_dates[0].day, ptf_day);
    EXPECT_EQ(start_dates[0].month, ptf_month);
    EXPECT_EQ(start_dates[0].year, ptf_year);

    // end date
    EXPECT_EQ(end_dates[end_dates.size() - 1].day, 31);
    EXPECT_EQ(end_dates[end_dates.size() - 1].month, 12);
    EXPECT_EQ(end_dates[end_dates.size() - 1].year, ptf_year + years_to_simulate);

    EXPECT_EQ(end_dates[0].day, ptf_day);
    EXPECT_EQ(end_dates[0].month, ptf_month);
    EXPECT_EQ(end_dates[0].year, ptf_year);
    EXPECT_EQ(period_lengths[0], 0);

    EXPECT_EQ(end_dates[1].day, 30);
    EXPECT_EQ(end_dates[1].month, 11);
    EXPECT_EQ(end_dates[1].year, 2021);
    EXPECT_EQ(period_lengths[1], 10); // this is waht we get with the 30/360 convention

    EXPECT_EQ(end_dates[2].day, 31);
    EXPECT_EQ(end_dates[2].month, 12);
    EXPECT_EQ(end_dates[2].year, 2021);
    EXPECT_EQ(period_lengths[2], 30);

    EXPECT_EQ(end_dates[3].day, 31);
    EXPECT_EQ(end_dates[3].month, 1);
    EXPECT_EQ(end_dates[3].year, 2022);
    EXPECT_EQ(period_lengths[3], 30);
}

TEST(time_axis, quarterly)
{
    // set up time axis object
    TimeStep time_step = TimeStep::QUARTERLY;
    int years_to_simulate = 4;
    short ptf_year = 2021;
    short ptf_month = 12;
    short ptf_day = 20;

    TimeAxis ta(time_step, years_to_simulate, ptf_year, ptf_month, ptf_day);

    const vector<PeriodDate> &start_dates = ta.get_start_dates();
    const vector<PeriodDate> &end_dates = ta.get_end_dates();
    const vector<int> &period_lengths = ta.get_period_length_in_days();

    // check starting/ending dates
    EXPECT_EQ(start_dates[0].day, ptf_day);
    EXPECT_EQ(start_dates[0].month, ptf_month);
    EXPECT_EQ(start_dates[0].year, ptf_year);

    // end date
    EXPECT_EQ(end_dates[end_dates.size() - 1].day, 31);
    EXPECT_EQ(end_dates[end_dates.size() - 1].month, 12);
    EXPECT_EQ(end_dates[end_dates.size() - 1].year, ptf_year + years_to_simulate);

    // first end date is equal to start date
    EXPECT_EQ(end_dates[0].day, ptf_day);
    EXPECT_EQ(end_dates[0].month, ptf_month);
    EXPECT_EQ(end_dates[0].year, ptf_year);
    EXPECT_EQ(period_lengths[0], 0);

    EXPECT_EQ(end_dates[1].day, 31);
    EXPECT_EQ(end_dates[1].month, 12);
    EXPECT_EQ(end_dates[1].year, 2021);
    EXPECT_EQ(period_lengths[1], 10); // this is waht we get with the 30/360 convention

    EXPECT_EQ(end_dates[2].day, 31);
    EXPECT_EQ(end_dates[2].month, 3);
    EXPECT_EQ(end_dates[2].year, 2022);
    EXPECT_EQ(period_lengths[2], 90);

    EXPECT_EQ(end_dates[3].day, 30);
    EXPECT_EQ(end_dates[3].month, 6);
    EXPECT_EQ(end_dates[3].year, 2022);
    EXPECT_EQ(period_lengths[3], 90);
}

TEST(time_axis, yearly)
{
    // set up time axis object
    TimeStep time_step = TimeStep::YEARLY;
    int years_to_simulate = 4;
    short ptf_year = 2021;
    short ptf_month = 12;
    short ptf_day = 20;

    TimeAxis ta(time_step, years_to_simulate, ptf_year, ptf_month, ptf_day);
    const vector<PeriodDate> &start_dates = ta.get_start_dates();
    const vector<PeriodDate> &end_dates = ta.get_end_dates();
    const vector<int> &period_lengths = ta.get_period_length_in_days();

    // check starting/ending dates
    EXPECT_EQ(start_dates[0].day, ptf_day);
    EXPECT_EQ(start_dates[0].month, ptf_month);
    EXPECT_EQ(start_dates[0].year, ptf_year);

    // end date
    EXPECT_EQ(end_dates[end_dates.size() - 1].day, 31);
    EXPECT_EQ(end_dates[end_dates.size() - 1].month, 12);
    EXPECT_EQ(end_dates[end_dates.size() - 1].year, ptf_year + years_to_simulate);

    EXPECT_EQ(end_dates[0].day, ptf_day);
    EXPECT_EQ(end_dates[0].month, ptf_month);
    EXPECT_EQ(end_dates[0].year, ptf_year);
    EXPECT_EQ(period_lengths[0], 0);

    EXPECT_EQ(end_dates[1].day, 31);
    EXPECT_EQ(end_dates[1].month, 12);
    EXPECT_EQ(end_dates[1].year, 2021);
    EXPECT_EQ(period_lengths[1], 10); // this is waht we get with the 30/360 convention

    EXPECT_EQ(end_dates[2].day, 31);
    EXPECT_EQ(end_dates[2].month, 12);
    EXPECT_EQ(end_dates[2].year, 2022);
    EXPECT_EQ(period_lengths[2], 360);

    EXPECT_EQ(end_dates[3].day, 31);
    EXPECT_EQ(end_dates[3].month, 12);
    EXPECT_EQ(end_dates[3].year, 2023);
    EXPECT_EQ(period_lengths[3], 360);
}



#endif
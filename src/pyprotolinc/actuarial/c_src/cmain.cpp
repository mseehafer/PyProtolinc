

#include <iostream>
#include "modules/time_axis.h"
#include "modules/providers.h"

using namespace std;

int main(void) {

    cout << "TEST1 - Starting 2021-12-31" << endl;

    TimeStep time_step = TimeStep::MONTHLY;
    int years_to_simulate = 4;
    short ptf_year = 2021;
    short ptf_month = 12;
    short ptf_day = 31;

    TimeAxis ta(time_step, years_to_simulate,ptf_year, ptf_month, ptf_day );
    const vector<PeriodEndDate>& the_dates1 = ta.get_the_dates();
    const vector<int>& period_lengths1 = ta.get_period_length_in_days();
    print_vec<PeriodEndDate>(the_dates1, "THE_DATES");
    print_vec<int>(period_lengths1, "PERIOD_LENGTH");

    vector<int> recalc1;
    recalc1.reserve(period_lengths1.size());
    recalc1.push_back(0);
    for (size_t i = 1; i < period_lengths1.size(); i++) {
        recalc1.push_back(getdays_30U_360(the_dates1[i-1], the_dates1[i]));
    }
    print_vec<int>(recalc1, "PERIOD_LENGTH_RECALC");
   

    
    cout << "TEST2 - Starting 2021-12-20" << endl;
    time_step = TimeStep::MONTHLY;
    years_to_simulate = 4;
    ptf_year = 2021;
    ptf_month = 12;
    ptf_day = 20;

    ta = TimeAxis(time_step, years_to_simulate,ptf_year, ptf_month, ptf_day );
    const vector<PeriodEndDate>& the_dates2 = ta.get_the_dates();
    const vector<int>& period_lengths2 = ta.get_period_length_in_days();
    print_vec<PeriodEndDate>(the_dates2, "THE_DATES");
    print_vec<int>(period_lengths2, "PERIOD_LENGTH");    

    vector<int> recalc2;
    recalc2.reserve(period_lengths1.size());
    recalc2.push_back(0);
    for (size_t i = 1; i < period_lengths1.size(); i++) {
        recalc2.push_back(getdays_30U_360(the_dates2[i-1], the_dates2[i]));
    }
    print_vec<int>(recalc2, "PERIOD_LENGTH_RECALC");


}


#include <iostream>
#include "modules/time_axis.h"
#include "modules/providers.h"

using namespace std;

int main(void) {

    cout << "TEST1 - Starting 2021-12-31 | MONTHLY" << endl;

    TimeStep time_step = TimeStep::MONTHLY;
    int years_to_simulate = 4;
    short ptf_year = 2021;
    short ptf_month = 12;
    short ptf_day = 20;

    TimeAxis ta(time_step, years_to_simulate,ptf_year, ptf_month, ptf_day );

    const vector<PeriodDate>& start_dates1 = ta.get_start_dates();
    const vector<PeriodDate>& end_dates1 = ta.get_end_dates();
    const vector<int>& period_lengths1 = ta.get_period_length_in_days();  
    for (size_t t=0; t < end_dates1.size(); t++) {
        cout << start_dates1[t] << " - " << end_dates1[t] << " : " << period_lengths1[t] << endl;
    }

    cout << endl;
    cout << "TEST2 - Starting 2021-12-20 | QUARTERLY" << endl;
    time_step = TimeStep::QUARTERLY;
    years_to_simulate = 4;
    ptf_year = 2021;
    ptf_month = 12;
    ptf_day = 20;

    ta = TimeAxis(time_step, years_to_simulate,ptf_year, ptf_month, ptf_day );
    const vector<PeriodDate>& start_dates2 = ta.get_start_dates();
    const vector<PeriodDate>& end_dates2 = ta.get_end_dates();
    const vector<int>& period_lengths2 = ta.get_period_length_in_days();  
    for (size_t t=0; t < end_dates2.size(); t++) {
        cout << start_dates2[t] << " - " << end_dates2[t] << " : " << period_lengths2[t] << endl;
    }

    cout << endl;
    cout << "TEST3 - Starting 2021-12-20 | YEARLY" << endl;
    time_step = TimeStep::YEARLY;
    years_to_simulate = 4;
    ptf_year = 2021;
    ptf_month = 12;
    ptf_day = 20;

    ta = TimeAxis(time_step, years_to_simulate,ptf_year, ptf_month, ptf_day );
    const vector<PeriodDate>& start_dates3 = ta.get_start_dates();
    const vector<PeriodDate>& end_dates3 = ta.get_end_dates();
    const vector<int>& period_lengths3 = ta.get_period_length_in_days();  
    for (size_t t=0; t < end_dates3.size(); t++) {
        cout << start_dates3[t] << " - " << end_dates3[t] << " : " << period_lengths3[t] << endl;
    }


}
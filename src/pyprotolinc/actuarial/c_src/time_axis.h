

/* CPP implementation of the assumption providers. */

#ifndef C_TIME_AXIS_H
#define C_TIME_AXIS_H

#include <iostream>

using namespace std;


enum class TimeStep: int {
    MONTHLY,                               // 0
    QUARTERLY,                             // 1
    YEARLY                                 // 2
};


struct TimeIndex {
    int year;
    int quarter;
    int month;
};


int get_total_steps(TimeStep time_step, int years_to_simulate)
{
    switch(time_step) {
        case TimeStep::MONTHLY: return 12 * years_to_simulate + 1;
        case TimeStep::QUARTERLY: return 4 * years_to_simulate + 1;
        case TimeStep::YEARLY: return years_to_simulate + 1;
    }    
};


class TimeAxis {

    TimeStep _time_step;
    int _years_to_simulate;
    
    // portfolio_date
    short _ptf_year, _ptf_month, _ptf_day;

    //short _start_year, _start_month, _start_day;

public:
    TimeAxis(TimeStep time_step, int years_to_simulate,
    short ptf_year, short ptf_month, short ptf_day): _time_step(time_step),
                                                     _years_to_simulate(years_to_simulate),
                                                     _ptf_year(ptf_year), _ptf_month(ptf_month), _ptf_day(ptf_day)
    {
        cout << "Creating time axis with time_step=" << (int) _time_step << endl;

        //_start_year, _start_month, _start_day
    }

    int get_portfolio_year() const {return _ptf_year;}
    int get_portfolio_month() const {return _ptf_month;}
    int get_portfolio_day() const {return _ptf_day;}

    TimeIndex at(int k) const {
        // TODO: add the calculation
        TimeIndex ti;
        ti.year = _ptf_year;
        ti.quarter = (_ptf_month-1) / 3 + 1;
        ti.month = _ptf_month;
        return ti;
    }

    int get_total_timesteps() const {
        return  get_total_steps(_time_step, _years_to_simulate);
    }

};


#endif
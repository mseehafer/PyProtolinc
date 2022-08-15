/* CPP implementation of the assumption providers. */

#ifndef C_TIME_AXIS_H
#define C_TIME_AXIS_H

#include <iostream>

using namespace std;

enum class TimeStep : int
{
    MONTHLY,   // 0
    QUARTERLY, // 1
    YEARLY     // 2
};

const int _days_in_month[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};

struct PeriodEndDate
{
    short year;
    short month;
    short day;

    PeriodEndDate(short y, short m, short d) : year(y), month(m), day(d) {}

    void set(short y, short m, short d)
    {
        year = y;
        month = m;
        day = d;
    }

    inline bool is_schaltjahr()
    {
        if (year % 400 == 0)
            return true;
        else if (year % 100 == 0)
            return false;
        else if (year % 4 == 0)
            return true;
        else
            return false;
    }

    inline bool before(short y, short m, short d)
    {
        if (year < y || (year == y && month < m) || (year == y && month == m && day < d))
            return true;
        else
            return false;
    }

    void set_next_end_of_month()
    {
        int duration{30};
        switch (month)
        {
        case 1:
        case 3:
        case 5:
        case 7:
        case 8:
        case 10:
        case 12:
            if (day < 31)
            {
                day = 31;
            }
            else
            {
                month++;
                if (month > 12)
                {
                    month = 1;
                    year++;
                }
                day = _days_in_month[month - 1];
            }
            break;
        default:
            if (day < _days_in_month[month - 1])
            {
                day = _days_in_month[month - 1];
            }
            else
            {
                day = 31; // small error if day = 28 in schaltjahr
                month++;
            }
        }
        // Schaltjahr Check
        if (month == 2 && is_schaltjahr())
            day = 29;
    }

    void set_next_end_of_quarter()
    {
        if (before(year, 3, 31))
        {
            month = 3;
            day = 31;
        }
        else if (before(year, 6, 30))
        {
            month = 6;
            day = 30;
        }
        else if (before(year, 9, 30))
        {
            month = 9;
            day = 30;
        }
        else if (before(year, 12, 31))
        {
            month = 12;
            day = 31;
        }
        else
        {
            year++;
            month = 3;
            day = 31;
        }
    }

    void set_next_end_of_year()
    {
        if (before(year, 12, 31))
        {
            month = 12;
            day = 31;
        }
        else
        {
            year++;
            month = 12;
            day = 31;
        }
    }
};

// int get_total_steps(TimeStep time_step, int years_to_simulate)
// {
//     switch(time_step) {
//         case TimeStep::MONTHLY: return 12 * years_to_simulate + 1;
//         case TimeStep::QUARTERLY: return 4 * years_to_simulate + 1;
//         case TimeStep::YEARLY: return years_to_simulate + 1;
//     }
//     return -1; // shouldn't be reached
// }

class TimeAxis
{

    TimeStep _time_step;
    int _years_to_simulate;

    // portfolio_date
    short _ptf_year, _ptf_month, _ptf_day;

    // short _start_year, _start_month, _start_day;
    vector<PeriodEndDate> the_dates;

public:
    TimeAxis(TimeStep time_step, int years_to_simulate,
             short ptf_year, short ptf_month, short ptf_day) : _time_step(time_step),
                                                               _years_to_simulate(years_to_simulate),
                                                               _ptf_year(ptf_year), _ptf_month(ptf_month), _ptf_day(ptf_day)
    {
        cout << "Creating time axis with time_step=" << (int)_time_step << endl;
        the_dates.reserve(2 + 12 * _years_to_simulate);

        PeriodEndDate d(_ptf_year, _ptf_month, _ptf_day);
        PeriodEndDate end_date(_ptf_year + _years_to_simulate, _ptf_month, _ptf_day);
        if (end_date.month != 12 || (end_date.month == 12 && end_date.day != 31))
            end_date.set_next_end_of_year();

        the_dates.push_back(d);
        while (d.before(end_date.year, end_date.month, end_date.day))
        {
            if (time_step == TimeStep::YEARLY)
            {
                d.set_next_end_of_year();
            }
            else if (time_step == TimeStep::QUARTERLY)
            {
                d.set_next_end_of_quarter();
            }
            else
            {
                d.set_next_end_of_month();
            }

            the_dates.push_back(d);
        }
    }

    int get_portfolio_year() const { return _ptf_year; }
    int get_portfolio_month() const { return _ptf_month; }
    int get_portfolio_day() const { return _ptf_day; }

    const PeriodEndDate &at(int k) const
    {
        return the_dates[k];
    }

    int get_length() const
    {
        return the_dates.size();
    }
};

#endif
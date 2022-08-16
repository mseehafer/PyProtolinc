/* CPP implementation of the time axis and related objects.

Some read on 30/360 time count convention: https://sqlsunday.com/2014/08/17/30-360-day-count-convention/
 */

#ifndef C_TIME_AXIS_H
#define C_TIME_AXIS_H

#include <iostream>
#include <vector>
#include <string>

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

    string to_string() const {
        return std::to_string((int)year) + "/" + std::to_string((int)month) + "/" +  std::to_string((int)day);
    }

    void set(short y, short m, short d)
    {
        year = y;
        month = m;
        day = d;
    }

    bool is_schaltjahr() const
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

    bool before(short y, short m, short d) const
    {
        if (year < y || (year == y && month < m) || (year == y && month == m && day < d))
            return true;
        else
            return false;
    }

    int set_next_end_of_month()
    {
        int duration;
        
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
                duration = (day <=30 ? 30 - day: 0);
                day = 31;
            }
            else
            {
                duration = 30;
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
                duration = (day <=30 ? 30 - day: 0);
                day = _days_in_month[month - 1];
            }
            else
            {
                duration = 30;
                day = 31; // small error if day = 28 in schaltjahr
                month++;
            }
        }
        // Schaltjahr Check
        if (month == 2 && is_schaltjahr())
            day = 29;
        
        return duration;
    }

    int set_next_end_of_quarter()
    {
        int duration;  // full quarter by default
        if (before(year, 3, 31))
        {
            duration = (day <=30 ? 30 - day: 0) + 30 * (3 - month);
            month = 3;
            day = 31;
        }
        else if (before(year, 6, 30))
        {
            duration = (day <=30 ? 30 - day: 0) + 30 * (6 - month);
            month = 6;
            day = 30;
        }
        else if (before(year, 9, 30))
        {
            duration = (day <=30 ? 30 - day: 0) + 30 * (9 - month);
            month = 9;
            day = 30;
        }
        else if (before(year, 12, 31))
        {
            duration = (day <=30 ? 30 - day: 0) + 30 * (12 - month);
            month = 12;
            day = 31;
        }
        else
        {
            int duration = 90;
            year++;
            month = 3;
            day = 31;
        }
        return duration;
    }

    int set_next_end_of_year()
    {
        int duration = 360; // full year by default
        if (before(year, 12, 31))
        {
            // calculate the duration by assuming 30/360
            duration = (day <=30 ? 30 - day: 0) + 30 * (12 - month);

            month = 12;
            day = 31;
        }
        else
        {
            year++;
            month = 12;
            day = 31;
        }
        return duration;
    }
};

/// US 30/360 convention accoriding to https://sqlsunday.com/2014/08/17/30-360-day-count-convention/
inline int getdays_30U_360(const PeriodEndDate &date1, const PeriodEndDate &date2) {

    // ASSERT date1 <= date2

    short d1 = date1.day;
    short d2 = date2.day;

    bool d1_is_last_of_feb = date1.month == 2 && ((date1.is_schaltjahr() && d1 == 29) || (!date1.is_schaltjahr() && d1 == 28));
    bool d2_is_last_of_feb = date2.month == 2 && ((date2.is_schaltjahr() && d2 == 29) || (!date2.is_schaltjahr() && d2 == 28));

    // from: https://en.wikipedia.org/wiki/360-day_calendar
    // If both date A and B fall on the last day of February, then date B will be changed to the 30th.
    if (d1_is_last_of_feb && d2_is_last_of_feb) {
        d2 = 30;
    }
    
    // If date A falls on the 31st of a month or last day of February, then date A will be changed to the 30th.
    if (d1_is_last_of_feb || d1 == 31) {
        d1 = 30;
    }

    // If date A falls on the 30th of a month after applying (2) above and date B falls on the 31st of a month, then date B will be changed to the 30th.
    if (d1 == 30 && date2.day == 31) {
        d2 = 30;
    }

    // // 4. If @d1 is 31, set @d1 to 30.
    // if (date1.day == 31) {
    //     d1 = 30;
    // }
    
    return 360*(date2.year-date1.year) + 30*(date2.month-date1.month) + (d2-d1);
}

/// European 30/360 convention accoriding to https://sqlsunday.com/2014/08/17/30-360-day-count-convention/
int getdays_30E_360(const PeriodEndDate &date1, const PeriodEndDate &date2) {

   // ASSERT date1 <= date2

    short d1 = date1.day;
    short d2 = date2.day;

    // 1. If @d1 is 31, set @d1 to 30.
    if (d1 == 31) {
        d1 = 30;
    }
    
    // 2. If @d2 is 31, set @d2 to 30.
    if (d2 == 31) {
        d2 = 30;
    }

    return 360*(date2.year-date1.year) + 30*(date2.month-date1.month) + (d2 - d1);
}




// to make the above struct printable with cout
std::ostream & operator << (std::ostream & outs, const PeriodEndDate & ped) {
    return outs << ped.to_string();
}



class TimeAxis
{
private:
    TimeStep _time_step;
    int _years_to_simulate;

    // portfolio_date
    short _ptf_year, _ptf_month, _ptf_day;

    // short _start_year, _start_month, _start_day;
    vector<PeriodEndDate> the_dates;
    vector<int> period_length_in_days;

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
        period_length_in_days.push_back(0);
        while (d.before(end_date.year, end_date.month, end_date.day))
        {
            int duration;
            if (time_step == TimeStep::YEARLY)
            {
                duration = d.set_next_end_of_year();
            }
            else if (time_step == TimeStep::QUARTERLY)
            {
                duration = d.set_next_end_of_quarter();
            }
            else
            {
                duration = d.set_next_end_of_month();
            }

            the_dates.push_back(d);
            period_length_in_days.push_back(getdays_30U_360(the_dates[the_dates.size() - 2], d));
            //period_length_in_days.push_back(duration);
        }
    }

    int get_portfolio_year() const { return _ptf_year; }
    int get_portfolio_month() const { return _ptf_month; }
    int get_portfolio_day() const { return _ptf_day; }

    const PeriodEndDate &at(int k) const
    {
        return the_dates[k];
    }

    size_t get_length() const
    {
        return the_dates.size();
    }

    const vector<PeriodEndDate>& get_the_dates() const {return the_dates;}
    const vector<int>& get_period_length_in_days() const {return period_length_in_days;}
};

#endif
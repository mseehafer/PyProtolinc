/**
 * @file portfolio.h
 * @author M. Seehafer
 * @brief
 * @version 0.2.0
 * @date 2022-08-27
 *
 * @copyright Copyright (c) 2022
 *
 */
#ifndef C_PORTFOLIO_H
#define C_PORTFOLIO_H

#include <memory>
#include <vector>
#include <iostream>
#include <string>
#include <cstdint>

#include "time_axis.h"

using namespace std;

/**
 * @brief Represents a seriatim record.
 *
 */
class CPolicy
{
protected:
    int64_t cession_id;

    PeriodDate issue_date = PeriodDate(0, 0, 0);
    PeriodDate dob = PeriodDate(0, 0, 0);

    // disablement_date
    bool _has_disablement_date;
    PeriodDate date_dis = PeriodDate(0, 0, 0);

    int gender;
    int smoker_status;

    double sum_insured;
    double reserving_rate;

    string product;

    int initial_state;

public:
    /// return the technical policy ID
    int64_t get_cession_id() const { return cession_id; }

    /// Return the issue date.
    const PeriodDate &get_issue_date() const {return issue_date;}
    // short get_issue_year() const { return issue_date.year; }
    // short get_issue_month() const { return issue_date.month; }
    // short get_issue_day() const { return issue_date.day; }
    
    /// Get date of birth.
    const PeriodDate &get_dob() const {return dob;}
    // short get_dob_year() const { return dob.year; }
    // short get_dob_month() const { return dob.month; }
    // short get_dob_day() const { return dob.day; }

    /// Return if the policy had a disabled date.
    bool has_disablement_date() const { return _has_disablement_date; }

    const PeriodDate &get_date_dis() const {return date_dis;}               ///< Return the *Date of Disablement*.
    // short get_date_dis_year() const { return date_dis.year; }
    // short get_date_dis_month() const { return date_dis.month; }
    // short get_date_dis_day() const { return date_dis.day; }

    int get_gender() const { return gender; }                               ///< Return the Gender code.
    int get_smoker_status() const { return smoker_status; }                 ///< Return the SmokerStatus code.

    double get_sum_insured() const { return sum_insured; }                  ///< Return the insured amount.
    double get_reserving_rate() const { return reserving_rate; }            ///< Return the reserving rate.

    const string &get_product() const { return product; }                   ///< Return the product code of the policy.

    
    int get_initial_state() const { return initial_state; }                 ///< Return the initial state

    /**
     * @brief Construct a new CPolicy object
     *
     * @param cession_id Technical ID of the record.
     * @param dob_long Date of birth in the format YYYYMMDD
     * @param issue_date_long Date of policy issue in the format YYYYMMDD
     * @param disablement_date_long Date of disablement of the policy in format YYYYMMDD
     * @param gender Value for the selector of the risk factor Gender.
     * @param smoker_status Value for the selector of the risk factor SmokerStatus.
     * @param sum_insured Insured amount.
     * @param reserving_rate (Constant) reserving rate that shall be used for this policy.
     * @param product Product code.
     * @param initial_state State number (zero based) the policy is in at the start.
     */
    CPolicy(int64_t cession_id,
            int64_t dob_long,
            int64_t issue_date_long,
            int64_t disablement_date_long,
            int32_t gender,
            int32_t smoker_status,
            double sum_insured,
            double reserving_rate,
            string product,
            int initial_state)
    {
        this->cession_id = cession_id;

        this->issue_date.set_from_long(issue_date_long);

        this->dob.set_from_long(dob_long);

        // disablement_date
        this->_has_disablement_date = disablement_date_long >= 0;
        if (this->_has_disablement_date)
        {
            this->date_dis.set_from_long(disablement_date_long);
        }

        this->gender = gender;
        this->smoker_status = smoker_status;
        this->sum_insured = sum_insured;
        this->reserving_rate = reserving_rate;

        this->product = product;
        this->initial_state = initial_state;
    }

    string to_string() const
    {
        string s = "<CPolicy [";
        return s + // to_string(issue_age) +
                   // std::to_string(", ") +        // get_product() + ", " + get_gender() +
               "PRODUCT=" + get_product() +
               ", GENDER=" + std::to_string(get_gender()) +
               ", INITIAL_STATE=" + std::to_string(initial_state) +
               ", SMOKER_STATUS=" + std::to_string(get_smoker_status()) +
               ", SUM_INSURED=" + std::to_string(get_sum_insured()) +
               ", RESERVING_RATE=" + std::to_string(get_reserving_rate()) +
               ", BIRTH=" + std::to_string(dob.year) + "-" + std::to_string(dob.month) + "-" + std::to_string(dob.day) +
               ", ISSUE=" + std::to_string(issue_date.year) + "-" + std::to_string(issue_date.month) + "-" + std::to_string(issue_date.day) +
               ", DISABLED=" + std::to_string(date_dis.year) + "-" + std::to_string(date_dis.month) + "-" + std::to_string(date_dis.day) +
               "]>";
    }
};

/**
 * @brief A portfolio of policies.
 *
 */
class CPolicyPortfolio
{
protected:
    vector<shared_ptr<CPolicy>> _policies;

    size_t _num_policies = 0;

    PeriodDate _portfolio_date;

    void reserve(size_t capa)
    {
        _policies.reserve(capa);
    }

public:
    // // portfolio date
    // short _ptf_year, _ptf_month, _ptf_day;

    /**
     * @brief Construct a new CPolicyPortfolio object
     *
     * @param ptf_year Year of the portfolio date
     * @param ptf_month Month of the portfolio date
     * @param ptf_day Day of the portfolio date
     */
    CPolicyPortfolio(short ptf_year, short ptf_month, short ptf_day) : _portfolio_date(ptf_year, ptf_month, ptf_day)
    {
    }

    /**
     * @brief Construct a new CPolicyPortfolio object
     *
     * @param pd The portfolio date
     */
    CPolicyPortfolio(PeriodDate pd) : _portfolio_date(pd)
    {
    }

    /// Return the portfolio date
    const PeriodDate &get_portfolio_date() { return _portfolio_date; }

    /// Return the vector of policies
    const vector<shared_ptr<CPolicy>> &get_policies()
    {
        return _policies;
    }

    /// Return the size of the portfolio
    size_t size() const
    {
        return _num_policies;
    }

    /// Add a policy to the portfolio.
    void add(shared_ptr<CPolicy> record_ptr)
    {
        _policies.push_back(record_ptr);
        _num_policies++;
    }

    /// Get the policy at the given index.
    const CPolicy &at(size_t j) const
    {
        return *_policies[j];
    }

    // to allow access the reserve method
    friend class CPortfolioBuilder;
};

/**
 * @brief Builder class that allows to create portfolios from a number of
 * appropriately typed vectors.
 *
 */
class CPortfolioBuilder
{

private:
    size_t num_policies = 0;

    bool has_portfolio_date = false;
    short ptf_year, ptf_month, ptf_day;

    // one product for all policies
    string product;

    bool has_cession_ids = false;
    int64_t *ptr_cession_id;

    bool has_dob = false;
    int64_t *ptr_dob;

    bool has_issue_dates = false;
    int64_t *ptr_issue_date;

    bool has_dis_dates = false;
    int64_t *ptr_disablement_date;

    bool has_gender = false;
    int32_t *ptr_gender;

    bool has_smoker_status = false;
    int32_t *ptr_smoker_status;

    bool has_sum_insured = false;
    double *ptr_sum_insured;

    bool has_reserving_rate = false;
    double *ptr_reserving_rate;

    bool has_initial_state = false;
    int16_t *ptr_initial_state;


public:
    /**
     * @brief Construct a new CPortfolioBuilder object
     *
     * @param s The required size (number of records) in the portfolio
     * @param _product The product code applicable throughout the portfolio.
     */
    CPortfolioBuilder(size_t s, string _product) : num_policies(s), product(_product) {}

    CPortfolioBuilder &set_portfolio_date(short ptf_year, short ptf_month, short ptf_day)
    {
        this->ptf_year = ptf_year;
        this->ptf_month = ptf_month;
        this->ptf_day = ptf_day;
        has_portfolio_date = true;
        return *this;
    }

    CPortfolioBuilder &set_cession_id(int64_t *ptr_cession_id)
    {
        this->ptr_cession_id = ptr_cession_id;
        has_cession_ids = true;
        return *this;
    }

    CPortfolioBuilder &set_date_of_birth(int64_t *ptr_dob)
    {
        this->ptr_dob = ptr_dob;
        has_dob = true;
        return *this;
    }

    CPortfolioBuilder &set_issue_date(int64_t *ptr_issue_date)
    {
        this->ptr_issue_date = ptr_issue_date;
        has_issue_dates = true;
        return *this;
    }

    CPortfolioBuilder &set_date_disablement(int64_t *ptr_disablement_date)
    {
        this->ptr_disablement_date = ptr_disablement_date;
        has_dis_dates = true;
        return *this;
    }

    CPortfolioBuilder &set_gender(int32_t *ptr_gender)
    {
        this->ptr_gender = ptr_gender;
        has_gender = true;
        return *this;
    }

    CPortfolioBuilder &set_smoker_status(int32_t *ptr_smoker_status)
    {
        this->ptr_smoker_status = ptr_smoker_status;
        has_smoker_status = true;
        return *this;
    }

    CPortfolioBuilder &set_sum_insured(double *ptr_sum_insured)
    {
        this->ptr_sum_insured = ptr_sum_insured;
        has_sum_insured = true;
        return *this;
    }

    CPortfolioBuilder &set_reserving_rate(double *ptr_reserving_rate)
    {
        this->ptr_reserving_rate = ptr_reserving_rate;
        has_reserving_rate = true;
        return *this;
    }

    CPortfolioBuilder &set_initial_state(int16_t *ptr_initial_state)
    {
        this->ptr_initial_state = ptr_initial_state;
        has_initial_state = true;
        return *this;
    }


    /// Create a new portfolio object from the given input vectors.
    shared_ptr<CPolicyPortfolio> build();
};

shared_ptr<CPolicyPortfolio> CPortfolioBuilder::build()
{

    if (!has_portfolio_date)
    {
        throw domain_error("Portfolio date not set.");
    }

    if (!has_dis_dates)
    {
        throw domain_error("Disablement dates not set.");
    }

    if (!has_issue_dates)
    {
        throw domain_error("Issue dates dates not set.");
    }

    if (!has_dob)
    {
        throw domain_error("Dates of birth not set.");
    }

    if (!has_cession_ids)
    {
        throw domain_error("Cession IDs not set.");
    }

    if (!has_gender)
    {
        throw domain_error("Gender is not set.");
    }

    if (!has_smoker_status)
    {
        throw domain_error("SmokerStatus is not set.");
    }

    if (!has_sum_insured)
    {
        throw domain_error("SumInsured is not set.");
    }

    if (!has_reserving_rate)
    {
        throw domain_error("ReservingRate is not set.");
    }

    if (!has_initial_state)
    {
        throw domain_error("Initial state not set.");
    }

    // two name for the same object
    shared_ptr<CPolicyPortfolio> ptr_portfolio = make_shared<CPolicyPortfolio>(ptf_year, ptf_month, ptf_day);
    CPolicyPortfolio &portfolio = *ptr_portfolio;

    portfolio.reserve(num_policies);

    for (size_t k = 0; k < num_policies; k++)
    {
        shared_ptr<CPolicy> record = make_shared<CPolicy>(ptr_cession_id[k],
                                                          ptr_dob[k],
                                                          ptr_issue_date[k],
                                                          ptr_disablement_date[k],
                                                          ptr_gender[k],
                                                          ptr_smoker_status[k],
                                                          ptr_sum_insured[k],
                                                          ptr_reserving_rate[k],
                                                          product,
                                                          ptr_initial_state[k]);

        portfolio.add(record);
    }

    return ptr_portfolio;
}

/**
 * @brief Calculate the age in (completed) months for a given birthday and the date of interest, returns -1 if not born yet at the given date.
 *
 * @param dob_year
 * @param dob_month
 * @param dob_day
 * @param dt_year
 * @param dt_month
 * @param dt_day
 * @return int Age in (completed) months.
 */
int get_age_at_date(int dob_year, int dob_month, int dob_day, int dt_year, int dt_month, int dt_day)
{
    // check that person is born at dt already
    if (dt_year < dob_year || (dt_year == dob_year && dt_month < dob_month) ||
        (dt_year == dob_year && dt_month == dob_month && dt_day < dob_day))
    {
        return -1; // use as a error signal
    }

    // special case equality of dates
    if (dt_year == dob_year && dt_month == dob_month && dt_day == dob_day)
    {
        return 0;
    }

    int full_years = (dt_month > dob_month || dob_month == dt_month && dob_day <= dt_day) ? dt_year - dob_year : dt_year - dob_year - 1;

    // so the last birthday before dt was at dob_year + full_years/dob_month/dob_day
    int full_months = (dt_month < dob_month || (dt_month == dob_month && dt_day < dob_day)) ? 12 + dt_month - dob_month - (dt_day < dob_day ? 1 : 0)
                                                                                            : dt_month - dob_month - (dt_day < dob_day ? 1 : 0);

    return 12 * full_years + full_months;
}

/**
 * @brief Calculate the age in (completed) months for a given birthday and the date of interest, returns -1 if not born yet at the given date.
 *
 * @param dob Date of Birthe
 * @param date_at Date at which to calculate the age
 * @return int Age in (completed) months.
 */
inline int get_age_at_date(const PeriodDate &dob, const PeriodDate& date_at)
{
    return get_age_at_date(dob.year, dob.month, dob.day, date_at.year, date_at.month, date_at.day);
}

#endif
#ifndef C_PORTFOLIO_H
#define C_PORTFOLIO_H

#include <vector>
#include <iostream>
#include <string>
#include <cstdint>

// #include "risk_factors.h"
// #include "providers.h"

using namespace std;

class CPolicy
{
protected:
    int64_t cession_id;

    // issue date
    int issue_year;
    int issue_month;
    int issue_day;

    // date of birth
    int dob_year;
    int dob_month;
    int dob_day;

    // disablement_date
    bool _has_disablement_date;
    int date_dis_year = 0;
    int date_dis_month = 0;
    int date_dis_day = 0;


public:
    int64_t get_cession_id() const { return cession_id; }

    int get_issue_year() const { return issue_year; }
    int get_issue_month() const { return issue_month; }
    int get_issue_day() const { return issue_day; }

    int get_dob_year() const { return dob_year; }
    int get_dob_month() const { return dob_month; }
    int get_dob_day() const { return dob_day; }

    bool has_disablement_date() const { return _has_disablement_date; }
    int get_date_dis_year() const { return date_dis_year; }
    int get_date_dis_month() const { return date_dis_month; }
    int get_date_dis_day() const { return date_dis_day; }

    CPolicy(int64_t cession_id,
            int64_t dob_long,
            int64_t issue_date_long,
            int64_t disablement_date_long
    )
    {
        this->cession_id = cession_id;

        // issue date
        this->issue_year = (int)(issue_date_long / 10000);
        this->issue_month = (int)((issue_date_long % 10000) / 100);
        this->issue_day = (int)(issue_date_long % 100);

        // date of birth
        this->dob_year = (int)(dob_long / 10000);
        this->dob_month = (int)((dob_long % 10000) / 100);
        this->dob_day = (int)(dob_long % 100);

        // disablement_date
        this->_has_disablement_date = disablement_date_long >= 0;
        if (this->_has_disablement_date) {
            this->date_dis_year = (int)(disablement_date_long / 10000);
            this->date_dis_month = (int)((disablement_date_long % 10000) / 100);
            this->date_dis_day = (int)(disablement_date_long % 100);
        }

        //   string prodUpper = product;
        //   transform(prodUpper.begin(), prodUpper.end(), prodUpper.begin(), ::toupper);

        //   // start out with unknown product
        //   this-> prod = ProdOther;
        //   for(int j=0; j < NUM_PRODS; j++) {
        //       string thisProdUpper = ProductNames[j];
        //       transform(thisProdUpper.begin(), thisProdUpper.end(), thisProdUpper.begin(), ::toupper);

        //       if (thisProdUpper.compare(prodUpper) == 0) {
        //         this -> prod = static_cast<Product>(j);
        //         break;
        //       }
        //   }
        //   this -> gender = static_cast<Gender> (gender < 3 ? gender : 2);

        //   issue_age = get_age_at_date(dob_year, dob_month, dob_day,
        //                               issue_year, issue_month, issue_day);

        //   this -> coverage_years = coverage_years;
        //   this -> sum_insured = sum_insured;

        //   age_projection_start =  get_age_at_date(dob_year, dob_month, dob_day,
        //                                           portfolio_year, portfolio_month, portfolio_day);
    }

    string to_string() const
    {
        string s = "<CPolicy [";
        //return s;
        return  s + // to_string(issue_age) +
               //std::to_string(", ") +        // get_product() + ", " + get_gender() +
               "BIRTH=" + std::to_string(get_dob_year()) + "-" + std::to_string(get_dob_month()) + "-" + std::to_string(get_dob_day()) +
               ", ISSUE=" + std::to_string(get_issue_year()) + "-" + std::to_string(get_issue_month()) + "-" + std::to_string(get_issue_day()) +
               ", DISABLED=" + std::to_string(get_date_dis_year()) + "-" + std::to_string(get_date_dis_month()) + "-" + std::to_string(get_date_dis_day()) +
               "]>";
    }
};

class CPolicyPortfolio
{
protected:
    vector<shared_ptr<CPolicy>> _policies;

    size_t _num_policies = 0;

    // portfolio date
    short _ptf_year, _ptf_month, _ptf_day;

public:
    CPolicyPortfolio(short ptf_year, short ptf_month, short ptf_day) : _ptf_year(ptf_year),
                                                                       _ptf_month(ptf_month),
                                                                       _ptf_day(ptf_day)
    {
    }

    size_t size() const {
        return _num_policies;
    }

    void add(shared_ptr<CPolicy> record_ptr)
    {
        _policies.push_back(record_ptr);
        _num_policies++;
    }

    void reserve(size_t capa)
    {
        _policies.reserve(capa);
    }

    const CPolicy &at(size_t j) const
    {
        return *_policies[j];
    }
};

class CPortfolioBuilder
{

private:
    size_t num_policies = 0;

    bool has_portfolio_date = false;
    short ptf_year, ptf_month, ptf_day;

    bool has_cession_ids = false;
    int64_t *ptr_cession_id;

    bool has_dob = false;
    int64_t *ptr_dob;

    bool has_issue_dates = false;
    int64_t *ptr_issue_date;

    bool has_dis_dates = false;
    int64_t *ptr_disablement_date;

public:
    CPortfolioBuilder(size_t s) : num_policies(s) {}

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

    /// function that creates a CPolicyPortfolio
    shared_ptr<CPolicyPortfolio> build()
    {

        if (!has_portfolio_date) {
            throw domain_error("Portfolio date not set.");
        }

        if (!has_dis_dates) {
            throw domain_error("Disablement dates not set.");
        }
        
        if (!has_issue_dates) {
            throw domain_error("Issue dates dates not set.");
        }

        if (!has_dob) {
            throw domain_error("Dates of birth not set.");
        }

        if (!has_cession_ids) {
            throw domain_error("Cession IDs not set.t");
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
                                                              ptr_disablement_date[k]);

            portfolio.add(record);
        }

        return ptr_portfolio;
    }
};

#endif
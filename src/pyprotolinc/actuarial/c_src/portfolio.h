#ifndef C_PORTFOLIO_H
#define C_PORTFOLIO_H

#include <vector>
#include <iostream>
#include <string>

// #include "risk_factors.h"
// #include "providers.h"

using namespace std;


class CPolicy
{
protected:

public:

};


class CPolicyPortfolio
{
protected:
    vector<shared_ptr<CPolicy>> _policies;
    
    int _num_policies = 0;

    // portfolio date
    short _ptf_year, _ptf_month, _ptf_day; 
public:

    CPolicyPortfolio(short ptf_year, short ptf_month, short ptf_day): _ptf_year(ptf_year),
                                                                      _ptf_month(ptf_month),
                                                                      _ptf_day(ptf_day)
    {}

    void reserve(size_t capa) {
        _policies.reserve(capa);
    }

    const CPolicy &at(size_t j) const {
        return *_policies[j];
    }

};

class CPortfolioBuilder {

private:
    size_t num_policies = 0;

    short ptf_year, ptf_month, ptf_day; 

public:

    CPortfolioBuilder(size_t s) : num_policies(s) {}

    CPortfolioBuilder &set_portfolio_date(short ptf_year, short ptf_month, short ptf_day) {
        this -> ptf_year = ptf_year;
        this -> ptf_month = ptf_month;
        this -> ptf_day = ptf_day;
        return *this;
    }
 
    /// function that creates a CPolicyPortfolio
    shared_ptr[CPolicyPortfolio] build(size_t num_policies) {

        shared_ptr[CPolicyPortfolio] ptr_portfolio = make_shared<CPolicyPortfolio>(ptf_year, ptf_month, ptf_day);
        ptr_portfolio -> reserve(num_policies);

        return ptr_portfolio;
    }
}


#endif
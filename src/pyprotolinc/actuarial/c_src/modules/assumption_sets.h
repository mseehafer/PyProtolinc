/* CPP implementation of the assumption providers. */

#ifndef C_ASSUMPTIONSETS_H
#define C_ASSUMPTIONSETS_H

#include <vector>
#include <memory>
#include <array>
#include <iostream>
#include <string>

#include "risk_factors.h"
#include "providers.h"

using namespace std;


typedef shared_ptr<CBaseRateProvider> PtrCBaseRateProvider;
typedef vector<vector<PtrCBaseRateProvider>> MatPtrCBaseRateProvider;


/// Container to hold the providers required for
/// a run or a policy
class CAssumptionSet
{

protected:
    unsigned n; // the dimension
    MatPtrCBaseRateProvider providers;

public:
    CAssumptionSet(unsigned dim):  n(dim) {
        
        // make sure we initialize to the right size and put null in
        for (unsigned r = 0; r < n; r++)
        {
            // create row vector and add to matrix
            vector<PtrCBaseRateProvider> row_vec = vector<PtrCBaseRateProvider>(n, nullptr);
            providers.push_back(row_vec);
        }
    }

    void clone_into(CAssumptionSet &other) const {
        if (other.n != this->n) {
            throw domain_error("Cloning asssumption set requires same dimensions");
        }
        for(unsigned r = 0; r < n; r++) {
            for (unsigned c = 0; c < n; c++) {
                shared_ptr<CBaseRateProvider> this_rc_comp = providers[r][c];
                if (this_rc_comp) {
                    other.providers[r][c] = this_rc_comp->clone();
                } else {
                    other.providers[r][c] = nullptr;
                }
            }
        }
    }

    
    void slice_into(const vector<int> &indices, CAssumptionSet &other) const {
        if (other.n != this->n) {
            throw domain_error("Cloning asssumption set requires same dimensions");
        }
        for(unsigned r = 0; r < n; r++) {
            for (unsigned c = 0; c < n; c++) {

                cout << "CAssumptionSet::slice_into() r=" << r << ", c=" << c << endl;
                shared_ptr<CBaseRateProvider> this_rc_comp = providers[r][c];
                shared_ptr<CBaseRateProvider> other_rc_comp = other.providers[r][c];

                if (this_rc_comp) {
                    // cout << "Try slicing" << endl;

                    // cout << "this_rc_comp->to_string()" << this_rc_comp->to_string() << endl;
                    // cout << "other_rc_comp->to_string()" << other_rc_comp->to_string() << endl;                    
                    
                    this_rc_comp->slice_into(indices, other_rc_comp.get());
                } else {
                    other.providers[r][c] = nullptr;
                }
            }
        }
    }    

    unsigned get_dimension() const {
        return n;
    }

    string get_provider_info(int r, int c) const {
        PtrCBaseRateProvider prvdr = providers.at(r).at(c);
        if (!prvdr)
          return "";
        else
          return prvdr -> to_string(); 
    }
    
    void set_provider(int row, int col, PtrCBaseRateProvider prvdr)
    {
        providers[row][col] = prvdr;
    }

    // Return a bool vector of the length of the risk factors indicating 
    // if the assumptions set depends on the risk factor or not
    void get_relevant_risk_factor_indexes(vector<bool> &relevant_risk_factors) {
        //vector<bool> relevant_risk_factors(NUMBER_OF_RISK_FACTORS, false);
        for (unsigned r = 0; r < n; r++)
        {
            for (unsigned c = 0; c < n; c++)
            {
                if (providers[r][c]) {
                    const vector<CRiskFactors> &vrf = providers[r][c]->get_risk_factors();

                    for(auto rf: vrf) {
                        relevant_risk_factors[(int)rf] = true;
                    }
                }
            }
        }
        //return relevant_risk_factors;
    }

    void get_single_rateset(const vector<int> &rf_indexes, double *rates_ext) const
    {
        // the index represent the values of each risk factor in their order

        if (rf_indexes.size() != NUMBER_OF_RISK_FACTORS)
        {
            throw domain_error("Unexpected length of risk factor vector!");
        }

        // indices for the looped-over provider
        vector<int> this_provider_indexes = vector<int>(n, 0);

        // loop over the risk factors, get the indexes relevant for them,
        // get the rates and store them in the external array
        for (unsigned r = 0; r < n; r++)
        {
            for (unsigned c = 0; c < n; c++)
            {
                //PtrCBaseRateProvider &prvdr = providers[r][c];

                // cout << "get_single_rateset(): " << r << ", " << c;

                if (!providers[r][c].get()) {
                    //rates_ext[r * NUMBER_OF_RISK_FACTORS + c] = 0;
                    rates_ext[r * n + c] = 0;
                    // cout << " ZERO" << endl;
                    continue;
                }

                // cout << " OTHER" << endl;

                const vector<CRiskFactors> &rf_for_this_prvdr = providers[r][c]->get_risk_factors();

                int req_size = (int) rf_for_this_prvdr.size();
                this_provider_indexes.resize(req_size);
                for (int l = 0; l < req_size; l++)
                {
                    int rf = static_cast<int>(rf_for_this_prvdr[l]);
                    this_provider_indexes[l] = rf_indexes.at(rf);
                }

                // cout << "PTR" << providers[r][c];
                double rate = providers[r][c] -> get_rate(this_provider_indexes);
                // cout << rate << endl;
                rates_ext[r * n + c] = rate;
            }
        }
    }
};

#endif
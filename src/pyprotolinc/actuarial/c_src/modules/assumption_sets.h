/**
 * @file assumption_sets.h
 * @author M. Seehafer
 * @brief Implementation of the assumption providers.
 * @version 0.1
 * @date 2022-08-27
 * 
 * @copyright Copyright (c) 2022
 * 
 */

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

/// Pointer to a provider object
typedef shared_ptr<CBaseRateProvider> PtrCBaseRateProvider;

/// "Matrix" of pointers to provider objects
typedef vector<vector<PtrCBaseRateProvider>> MatPtrCBaseRateProvider;



/**
 * @brief Container to hold the providers required for a run of a policy or a portfolio, houses a matrix of providers.
 * 
 */
class CAssumptionSet
{

protected:
    unsigned n; // the dimension
    MatPtrCBaseRateProvider providers;

public:
    /**
     * @brief Construct a new CAssumptionSet object
     * 
     * @param dim Number of states in the State-Model
     */
    CAssumptionSet(unsigned dim):  n(dim) {
        
        // make sure we initialize to the right size and put null in
        for (unsigned r = 0; r < n; r++)
        {
            // create row vector and add to matrix
            vector<PtrCBaseRateProvider> row_vec = vector<PtrCBaseRateProvider>(n, nullptr);
            providers.push_back(row_vec);
        }
    }

    /// Copy this assumption by making a deep copy of the underlying data.
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

    /// Perform a slicing operation on all provider objects contained in this object
    // and store the results in the provider passed in.
    void slice_into(const vector<int> &indices, CAssumptionSet &other) const {
        if (other.n != this->n) {
            cout << "CAssumptionSet::slice_into() dimension error" << endl;
            throw domain_error("Cloning asssumption set requires same dimensions");
        }
        for(unsigned r = 0; r < n; r++) {
            for (unsigned c = 0; c < n; c++) {

                //cout << "CAssumptionSet::slice_into() r=" << r << ", c=" << c << ", n=" << this->n << endl;
                shared_ptr<CBaseRateProvider> this_rc_comp = providers[r][c];
                shared_ptr<CBaseRateProvider> other_rc_comp = other.providers[r][c];

                if (this_rc_comp) {

                    // need to reduce the indices to the risk drivers used?
                    const vector<CRiskFactors> &rf_vec = this_rc_comp -> get_risk_factors();
                    vector<int> indices_for_provider;
                    for (CRiskFactors rf: rf_vec) {
                        indices_for_provider.push_back(indices[(int)rf]);
                    }
                    //this_rc_comp->slice_into(indices, other_rc_comp.get());
                    this_rc_comp->slice_into(indices_for_provider, other_rc_comp.get());
                } else {
                    other.providers[r][c] = nullptr;
                }
            }
        }
    }    

    /// Returns the number of dimensions of the state model.
    unsigned get_dimension() const {
        return n;
    }

    /// Returns a description of the provider in row r and column c.
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

    /// Return a bool vector of the length of the risk factors indicating 
    /// if the assumptions set depends on the risk factor or not
    void get_relevant_risk_factor_indexes(vector<bool> &relevant_risk_factors) {
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
    }

    /// Populate the an external array with the matrix of rates selected by the index vector passed in.
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
                if (!providers[r][c].get()) {
                    rates_ext[r * n + c] = 0;
                    continue;
                }

                const vector<CRiskFactors> &rf_for_this_prvdr = providers[r][c]->get_risk_factors();

                int req_size = (int) rf_for_this_prvdr.size();
                this_provider_indexes.resize(req_size);
                for (int l = 0; l < req_size; l++)
                {
                    int rf = static_cast<int>(rf_for_this_prvdr[l]);
                    this_provider_indexes[l] = rf_indexes.at(rf);
                }

                double rate = providers[r][c] -> get_rate(this_provider_indexes);
                rates_ext[r * n + c] = rate;
            }
        }
    }
};

#endif
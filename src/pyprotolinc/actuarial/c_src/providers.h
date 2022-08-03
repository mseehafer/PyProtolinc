/* CPP implementation of the assumption providers. */

#ifndef C_VALUATION_PROVIDERS_H
#define C_VALUATION_PROVIDERS_H

#include <vector>
#include <string>
#include <iostream>
#include "risk_factors.h"

using namespace std;

// fwd. declaration
void print_vec(vector<int> v, string name);

class CBaseRateProvider {
    // Abstract base class for `rates providers`.

protected:
    vector<CRiskFactors> risk_factors;

public:

    virtual ~CBaseRateProvider() {}
    virtual void get_rates(double *out_array, size_t length, vector<int *> &indices) const {
        throw domain_error("Method not implemented in abstract class.");
    }

    // def initialize(self, **kwargs):
    //     """ The ìnitialize hook can be used for setup actions. """
    //     # print(self.__class__.__name__, "Init-Hook")
    //     pass
    
    // do nothing
    virtual void add_risk_factor(CRiskFactors rf) {} 

    virtual double get_rate(vector<int> &indices) {
        throw domain_error("Method not implemented in abstract class.");
    }

    const vector<CRiskFactors>& get_risk_factors() const {
        return risk_factors;
    }

    virtual string to_string() const {
        return "<CBaseRatesProvider (abstract)>";
    }
};


class CConstantRateProvider: public CBaseRateProvider {

protected:
    double val = 0.0;

public:
    CConstantRateProvider(double rate) { val = rate; }

    virtual ~CConstantRateProvider() {}

    void get_rates(double *out_array, size_t length, vector<int *> &indices) const {
        for (size_t j = 0; j < length; j++) {
            out_array[j] = val;
        }
    }

    double get_rate(vector<int> &indices) {
        // cout << "CConstantRateProvider::get_rate \n";
        return val;
    }

    string to_string() const {
        return "<CConstantRateProvider with constant " + std::to_string(val) + ">";
    }

};


class CStandardRateProvider: public CBaseRateProvider {

protected:
    double *values = nullptr;   // the data array
    bool has_values = false;    // flag if the data array is set

    int number_values = 0;      // number of values in the data

    vector<int> shape_vec;      // the dimensions/shape
    vector<int> strides;        // steps width in the respective dimension
    vector<int> offsets;        // offset to be applied when queried for rates
    int dimensions = 0;         // number of dimensions of the data array

public:

    CStandardRateProvider() {}

    int get_dimension() {return dimensions;}
    int size() {return number_values;}
    
    void get_values(double *ext_vals) {
        // copy the data (manually for now), the caller must allocate memory before
        for (int j = 0; j < number_values; j++) {
             ext_vals[j] = values[j];
        }
    }

    virtual ~CStandardRateProvider() {
        if (has_values) {
             // cout << "DESTCRUCTOR w/ DELETE, number_values="  << number_values << " \n";
             delete[] values;
        } else {
            //cout << "DESTCRUCTOR NO DELETE, number_values="  << number_values << " \n";
        }
    }

    void set_values(vector<int> &shape_vec_in, vector<int> &offsets_in, double *ext_vals) {
        // this method allocates memory for the values, copies them and
        // sets the related member variables

        if (has_values) {
            // cout << "Freeing Memory" << "\n";
            // delete[] values;
            // values = nullptr;
            // has_values = false;
            throw domain_error("Values already set.");
        }
        
        // copy vectors
        shape_vec = shape_vec_in;
        offsets = offsets_in;
        dimensions = shape_vec_in.size();
        // a constant gets the dimension 0
        if (dimensions == 1 && shape_vec_in[0] == 1) {
            dimensions = 0;
        }
        
        // calculate the strides
        strides = shape_vec_in; // some arbitrary initialization
        int acc_dims = 1;
        for (int i = shape_vec_in.size() - 1; i >= 0; i--) {
            strides[i] = acc_dims;
            acc_dims *= shape_vec_in[i];
        }

        // checks:
        if (offsets.size() != dimensions && dimensions != 0 && offsets.size() != 1) {
            throw domain_error("Offset size must match dimension of values!");
        }

 
        // number of elements in values
        number_values = 1;
        if (dimensions > 0) {
            for (int i = 0; i < shape_vec_in.size(); i++) {
                number_values *= shape_vec_in[i];
            }
        }

        // checks:
        if (risk_factors.size() != dimensions) {
            cout << "risk_factors: " ;
            for (auto i = 0; i < risk_factors.size(); i++) {
                std::cout << CRiskFactors_names(risk_factors.at(i)) << ' ';
            }
            cout << "\n";            
            throw domain_error("risk_factor size must match dimension of values! " + std::to_string(risk_factors.size()) + " " + std::to_string(dimensions));
        }      

        // // some ouputs
        // cout << "dimensions: "  << dimensions << "\n";
        // cout << "number_values: "  << number_values << "\n";
        // // shapevec
        // cout << "shape_vec: " ;
        // for (auto i = 0; i < shape_vec.size(); i++) {
        //     std::cout << shape_vec.at(i) << ' ';
        // }
        // cout << "\n";
        // // strides
        // cout << "strides: " ;
        // for (auto i = 0; i < strides.size(); i++) {
        //     std::cout << strides.at(i) << ' ';
        // }
        // cout << "\n";
        // // offsets
        // cout << "offsets: " ;
        // for (auto i = 0; i < offsets.size(); i++) {
        //     std::cout << offsets.at(i) << ' ';
        // }    
        // cout << "\n";    

        // allocate a new array on the heap
        values = new double[number_values];
        has_values = true;

        // copy the data (manually for now)
        for (int j = 0; j < number_values; j++) {
             values[j] = ext_vals[j];
        }
    }

    void add_risk_factor(CRiskFactors rf) {
        // check if rf is already in the list, then do nothing
        for (auto i_rf : risk_factors) {
            if (rf == i_rf) {
                throw logic_error("Adding a risk factor for the second time.");
            }
        }

        risk_factors.push_back(rf);
    }

    string to_string() const {
        
        string s = "<CStandardRateProvider with RF (";
        bool first = true;
        for (auto rf : risk_factors) {
            if (!first) {
                s += ", ";
             }
            s += CRiskFactors_names(rf);
            first = false;
        }
        return s + ")>";
    }

    double get_rate(vector<int> &indices) const {
        if (!has_values) {
            throw logic_error("No values have been set before querying.");                   // TODO: testcase
        }

        if (indices.size() != dimensions) {
            throw domain_error("Dimension of indices does not match those of the data");      // TODO: testcase
        }

        int index = 0;
        for (int k = 0; k < dimensions; k++) {
            int ind_temp = indices[k] - offsets[k];
            if (ind_temp < 0 || ind_temp >= shape_vec[k]) {
                throw out_of_range("Indices out of Range for dimension #" + std::to_string(k) 
                   + ", max index allowed is " + std::to_string(shape_vec[k] - 1) + ".");
            }
            index += strides[k] * ind_temp;
        }
        // cout << "index=" << index << "\n";

        // output values
        // for (int i = 0; i < number_values; i++) {
        //     cout << " " << i << "=" << values[i];
        // }
        // cout << "\n";

        return values[index];
    }    

    virtual void get_rates(double *out_array, size_t length, vector<int *> &indices) const {

        if (!has_values) {
            throw logic_error("Not values have been set before querying.");                   // TODO: testcase
        }

        if (indices.size() != dimensions) {
            throw domain_error("Dimension of indices does not match those of the data");      // TODO: testcase
        }
        
        for (int j=0; j<length;j ++) {

            int index = 0;
            for (int k = 0; k < dimensions; k++) {
                int ind_temp = indices[k][j] - offsets[k];
                if (ind_temp < 0 || ind_temp >= shape_vec[k]) {
                    throw out_of_range("Indices out of Range for dimension #" + std::to_string(k) + ", max length is " + std::to_string(shape_vec[k]) + ".");
                }
                index += strides[k] * ind_temp;
            }

            out_array[j] = values[index];
        }
    }    

    virtual shared_ptr<CStandardRateProvider> slice(vector<int> &indices) const {
        /// Given a vector of indexes take only the dimensions where the values is "-1" in full
        //  and otherwise restrict to the index provided

        if (indices.size() != dimensions) {
            throw domain_error("Dimension of indices does not match those of the data");      // TODO: testcase
        }

        auto slicedProviderPtr = make_shared<CStandardRateProvider>();

        vector<int> shape_vec_sliced;
        vector<int> offsets_sliced;        
     
        // find all fixed dimensions
        vector<bool> dims_fixed(shape_vec.size(), false);
        int required_size = 1;
        for (int d = 0; d < dimensions; d++) {
            if (indices[d] != -1) {
                dims_fixed[d] = true;
            } else {
                required_size *= shape_vec[d]; 
                cout << "Adding rf: " << CRiskFactors_names(risk_factors[d]);
                slicedProviderPtr -> add_risk_factor(risk_factors[d]);
                shape_vec_sliced.push_back(shape_vec[d]);
                offsets_sliced.push_back(offsets[d]);
            }
        }

        print_vec(indices, "indices");
        print_vec(offsets_sliced, "offsets_sliced");
        print_vec(shape_vec_sliced, "shape_vec_sliced");  

        vector<int> bounds_lower(shape_vec.size(), 0);
        vector<int> bounds_upper(shape_vec.size(), 0);


        cout << "Required sized: " << required_size << "\n";

        // temporary storage space
        double *new_vals = new double[required_size];

        // determine the bounds
        for (int d = 0; d < dimensions; d++) {
            if (dims_fixed[d]) {
                bounds_lower[d] = indices[d] - offsets[d];
                bounds_upper[d] = indices[d] - offsets[d] + 1;  // exclusive
                if (bounds_lower[d] < 0 || bounds_upper[d] > shape_vec[d]) {
                    throw domain_error("Slicing indexes exceed dimensions");      // TODO: testcase
                }
            } else {
                bounds_lower[d] = 0;
                bounds_upper[d] = shape_vec[d];  // exclusive
            }
        }

        // print_vec(bounds_lower, "bounds_lower");
        // print_vec(bounds_upper, "bounds_upper");

        vector<int> counters = bounds_lower;
        int new_val_counter = 0;
        bool incremented;
        do {
            // calculate the index belonging to our current counter
            int index = 0;
            for (int k = 0; k < dimensions; k++) {
                index += strides[k] * counters[k];
            }

            // cout << "Adding ";
            // print_vec(counters, "counters");

            new_vals[new_val_counter++] = values[index];
                
            // increment
            incremented = false;
            for (int d = dimensions - 1; d >=0; d--) {
                if (counters[d] + 1 < bounds_upper[d]) {
                    counters[d] += 1;
                    for (int d2 = d + 1; d2 <= dimensions-1; d2++) {
                        counters[d2] = bounds_lower[d2];
                    }
                    incremented = true;
                    break;
                } 
            }
        } while (incremented);

        cout << "new_vals: " ;
        for (auto i = 0; i < required_size; i++) {
           std::cout << new_vals[i] << ' ';
        }    
        cout << "\n";        

        // special case: reduction to constant provider
        if (required_size == 1) {
            if (shape_vec_sliced.size() == 0) {
                shape_vec_sliced.push_back(1);
            }
            if (offsets_sliced.size() == 0) {
                offsets_sliced.push_back(0);
            }            
        }

        slicedProviderPtr -> set_values(shape_vec_sliced, offsets_sliced, new_vals);

        delete[] new_vals;
        
        return slicedProviderPtr;
    }

};


void print_vec(vector<int> v, string name) {
        cout << name << ": " ;
        for (auto i = 0; i < v.size(); i++) {
            std::cout << v.at(i) << ' ';
        }    
        cout << "\n";     
}

#endif
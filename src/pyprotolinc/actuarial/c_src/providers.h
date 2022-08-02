/* CPP implementation of the assumption providers. */

#ifndef C_VALUATION_PROVIDERS_H
#define C_VALUATION_PROVIDERS_H

#include <vector>
#include <string>
#include <iostream>

using namespace std;


enum class CRiskFactors: int {
    Age,      // 0
    Gender,   // 1
};


const char* CRiskFactors_names(CRiskFactors rf){
    switch (rf){
        case CRiskFactors::Age:
            return "Age";
        case CRiskFactors::Gender:
            return "Gender";
    }
}


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
        cout << "CConstantRateProvider::get_rate \n";
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
    int dimensions = 0;         // number of dimensions of the data array
    int number_values = 0;      // number of values in the data

    vector<int> shape_vec;      // the dimensions/shape
    vector<int> strides;        // steps width in the respective dimension
    vector<int> offsets;        // offset to be applied when queried for rates

public:

    CStandardRateProvider() {}

    virtual ~CStandardRateProvider() {
        if (has_values) {
             delete[] values;
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
        
        // calculate the strides
        strides = shape_vec_in; // some arbitrary initialization
        int acc_dims = 1;
        for (int i = shape_vec_in.size() - 1; i >= 0; i--) {
            strides[i] = acc_dims;
            acc_dims *= shape_vec_in[i];
        }

        // checks:
        if (offsets.size() != dimensions) {
            throw domain_error("Offset size miust match dimension of values!");
        }

        // number of elements in values
        int num_elems = 0;
        if (dimensions > 0) {
            num_elems = 1;
            for (int i = 0; i < shape_vec_in.size(); i++) {
                num_elems *= shape_vec_in[i];
            }
        }
        number_values = num_elems;

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
        // Return the rate for the specified index
        //cout << "CStandardRatesProvider::get_rate \n";

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

};



#endif
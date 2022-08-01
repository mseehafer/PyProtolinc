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


class CBaseRatesProvider {
    // Base class for `rates providers`.

protected:
    vector<CRiskFactors> risk_factors;

public:
    virtual void get_rates(double *out_array, size_t length) const = 0;

    // def initialize(self, **kwargs):
    //     """ The ìnitialize hook can be used for setup actions. """
    //     # print(self.__class__.__name__, "Init-Hook")
    //     pass
    
    // do nothing
    virtual void add_risk_factor(CRiskFactors rf) {}    

    const vector<CRiskFactors>& get_risk_factors() const {
        return risk_factors;
    }

    virtual string to_string() const {
        return "<CBaseRatesProvider>";
    }
};


class CZeroRateProvider: public CBaseRatesProvider {

protected:
    double val = 0.0;

public:
    CZeroRateProvider() {}

    virtual void get_rates(double *out_array, size_t length) const {
        for (int j=0; j<length;j ++) {
            out_array[j] = val;
        }
    }

    virtual string to_string() const {
        return "<CZeroRateProvider>";
    }
};


class CConstantRateProvider: public CZeroRateProvider {

public:
    CConstantRateProvider(double rate) { val = rate; }
    CConstantRateProvider() { val = 1; }

    // void set_rate(double rate) {val = rate;}

    virtual string to_string() const {
        return "<CConstantRateProvider with constant " + std::to_string(val) + ">";
    }

};


class CStandardRateProvider: public CZeroRateProvider {

protected:
    double *values = nullptr;
    bool has_values = false;
    int dimensions;
    int number_values;

    vector<int> shape_vec;
    vector<int> strides;   // contains the steps width in the respective dimension
    vector<int> offsets;

public:

    CStandardRateProvider() {has_values = false;}

    ~CStandardRateProvider() {
        if (has_values) {
             delete[] values;
    //         delete[] offsets;
        }
    }

    void set_values(vector<int> &shape_vec_in, vector<int> &offsets_in, double *ext_vals) {
        // this method allocates memory for the values, copies them and
        // sets the related member variables

        cout << "TEST1";

        if (has_values) {
            cout << "Freeing Memory" << "\n";
            delete[] values;
            values = nullptr;
            has_values = false;
            // or better: Exception -> we should not be allowed to overwrite the assumptions data
        }
        
        cout << "TEST2\n";

        // copy vectors
        shape_vec = shape_vec_in;

        cout << "TEST3\n";
        
        // calculate the strides
        strides = shape_vec_in; // some initialization
        int acc_dims = 1;
        for (int i = shape_vec_in.size() - 1; i >= 0; i--) {
            strides[i] = acc_dims;
            acc_dims *= shape_vec_in[i];
        }

        cout << "TEST4\n";
        offsets = offsets_in;

        dimensions = shape_vec_in.size();

        cout << "TEST5\n";    

        // checks:
        if (offsets.size() != dimensions) {
            // Exception!
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
        cout << "TEST6\n";        

        // some ouputs
        cout << "dimensions: "  << dimensions << "\n";
        cout << "number_values: "  << number_values << "\n";
        // shapevec
        cout << "shape_vec: " ;
        for (auto i = 0; i < shape_vec.size(); i++) {
            std::cout << shape_vec.at(i) << ' ';
        }
        cout << "\n";
        // strides
        cout << "strides: " ;
        for (auto i = 0; i < strides.size(); i++) {
            std::cout << strides.at(i) << ' ';
        }
        cout << "\n";
        // offsets
        cout << "offsets: " ;
        for (auto i = 0; i < offsets.size(); i++) {
            std::cout << offsets.at(i) << ' ';
        }    
        cout << "\n";    


        // allocate a new array on the heap
        values = new double[number_values];
        has_values = true;

        // // copy the data (manually for now)
        // for (int j = 0; j < number_values; j++) {
        //     values[j] = ext_vals[j];
        // }
    }

    void add_risk_factor(CRiskFactors rf) {
        // check if rf is already in the list, then do nothing
        for (auto i_rf : risk_factors) {
            if (rf == i_rf) {
                return; // or raise Exception?
            }
        }

        risk_factors.push_back(rf);
    }

    virtual string to_string() const {
        return "<CStandardRateProvider>";
    }

    virtual void get_rates(double *out_array, size_t length, vector<int *> &indices) const {

        if (indices.size() != dimensions) {
            // TODO: Exception
        }
        
        for (int j=0; j<length;j ++) {

            int index = 0;
            for (int k = 0; k < dimensions; k++) {
                int ind_temp = indices[k][j] - offsets[k];
                if (ind_temp < 0 || ind_temp >= shape_vec[k]) {
                    // Exception -> Out of Bounds
                    // or limit to allowed range?
                }
                index += strides[k] * ind_temp;
            }

            out_array[j] = values[index];
        }
    }    

};



#endif
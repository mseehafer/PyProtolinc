/* CPP implementation of the assumption providers. */

#ifndef C_VALUATION_PROVIDERS_H
#define C_VALUATION_PROVIDERS_H

#include <string>

using namespace std;


class CBaseRatesProvider {
    // Base class for `rates providers`.

public:
    virtual void get_rates(double *out_array, size_t length) const = 0;

    // def initialize(self, **kwargs):
    //     """ The ìnitialize hook can be used for setup actions. """
    //     # print(self.__class__.__name__, "Init-Hook")
    //     pass

    //virtual void get_risk_factors() const = 0;

    virtual string to_string() const {
        return "CBaseRatesProvider";
    }
};


class CZeroRateProvider: public CBaseRatesProvider {

protected:
    double val = 0.0;

public:

    virtual void get_rates(double *out_array, size_t length) const {
        for (int j=0; j<length;j ++) {
            out_array[j] = val;
        }
    }

    virtual string to_string() const {
        return "CZeroRateProvider";
    }
};


class CConstantRateProvider: public CZeroRateProvider {

public:
    CConstantRateProvider(double rate) { val = rate; }
    CConstantRateProvider() { val = 1; }

    void set_rate(double rate) {val = rate;}

    virtual string to_string() const {
        return "CConstantRateProvider";
    }

    // virtual void get_rates(double *out_array, size_t length) {
    //     for (int j=0; j<length;j ++) {
    //         out_array[j] = val;
    //     }
    // }    

};



#endif
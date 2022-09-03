/**
 * @file providers.h
 * @author M. Seehafer
 * @brief CPP implementation of the assumption providers.
 * @version 0.1
 * @date 2022-08-27
 * 
 * @copyright Copyright (c) 2022
 * 
 */



#ifndef C_VALUATION_PROVIDERS_H
#define C_VALUATION_PROVIDERS_H

#include <vector>
#include <string>
#include <iostream>
#include <memory>
#include <algorithm>
#include "risk_factors.h"

using namespace std;

/// Convenience function that prints a vector to the console
template <typename T>
void print_vec(vector<T> v, string name)
{
    cout << name << ": ";
    for (size_t i = 0; i < v.size(); i++)
    {
        std::cout << v.at(i) << ' ';
    }
    cout << "\n";
}

/**
 * @brief Abstract base class for the assumptions providers.
 * 
 */
class CBaseRateProvider
{
protected:
    vector<CRiskFactors> risk_factors;

public:
    virtual ~CBaseRateProvider() {}

    virtual void add_risk_factor(CRiskFactors rf) {} // do nothing

    virtual double get_rate(const vector<int> &indices) const
    {
        throw domain_error("Method not implemented in abstract class.");
    }

    virtual void get_rates(double *out_array, size_t length, const vector<int *> &indices) const
    {
        throw domain_error("Method not implemented in abstract class.");
    }

    const vector<CRiskFactors> &get_risk_factors() const
    {
        return risk_factors;
    }

    virtual string to_string() const
    {
        return "<CBaseRatesProvider (abstract)>";
    }

    virtual shared_ptr<CBaseRateProvider> clone() const = 0;

    virtual void slice_into(const vector<int> &indices, CBaseRateProvider *other) const = 0;
};

class CConstantRateProvider : public CBaseRateProvider
{

protected:
    double val = 0.0;

public:
    CConstantRateProvider(double rate) { val = rate; }
    // CConstantRateProvider() {}
    // void set_rate(double val_) {val = val_;} 


    virtual ~CConstantRateProvider() {}

    double get_rate(const vector<int> &indices) const override
    {
        return val;
    }

    void get_rates(double *out_array, size_t length, const vector<int *> &indices) const override
    {
        for (size_t j = 0; j < length; j++)
        {
            out_array[j] = val;
        }
    }

    string to_string() const override
    {
        return "<CConstantRateProvider with constant " + std::to_string(val) + ">";
    }

    void slice_into(const vector<int> &indices, CBaseRateProvider *other) const override
    {
        //cout << "CConstantRateProvider::slice_into()" << endl;
        // do nothing
    }    

    shared_ptr<CBaseRateProvider> clone() const override
    {
        //return make_shared<CConstantRateProvider>(val);
        return static_pointer_cast<CBaseRateProvider>(make_shared<CConstantRateProvider>(val));
    }


};

class CStandardRateProvider : public CBaseRateProvider
{

protected:
    shared_ptr<double[]> values = nullptr;
    bool has_values = false; // flag if the data array is set
    int number_values = 0;   // number of values used in the data
    int capacity = 0;        // number of elements currently accolacted (can be bigger than number_values)

    vector<int> shape_vec;       // the dimensions/shape
    vector<int> strides;         // steps width in the respective dimension
    vector<int> offsets;         // offset to be applied when queried for rates
    unsigned int dimensions = 0; // number of dimensions of the data array

    // private methods
    void set_strides();

public:
    CStandardRateProvider() {}
    virtual ~CStandardRateProvider() {}

    shared_ptr<CBaseRateProvider> clone() const override;

    int get_dimension() const { return dimensions; }
    int get_capacity() const { return capacity; }
    int size() const { return number_values; }

    void get_values(double *ext_vals) const
    {
        std::copy(values.get(), values.get() + number_values, ext_vals);
    }

    void set_values(vector<int> &shape_vec_in, vector<int> &offsets_in, double *ext_vals);

    void add_risk_factor(CRiskFactors rf) override
    {
        // check if rf is already in the list and throw an exception in this case
        for (auto i_rf : risk_factors)
        {
            if (rf == i_rf)
            {
                throw logic_error("Adding a risk factor for the second time.");
            }
        }

        risk_factors.push_back(rf);
    }

    string to_string() const override;

    double get_rate(const vector<int> &indices) const override
    {
        if (!has_values)
        {
            throw logic_error("No values have been set before querying."); // TODO: testcase
        }

        if (indices.size() != dimensions)
        {
            throw domain_error("Dimension of indices does not match those of the data"); // TODO: testcase
        }

        int index = 0;
        for (unsigned k = 0; k < dimensions; k++)
        {
            int ind_temp = indices[k] - offsets[k];
            if (ind_temp < 0 || ind_temp >= shape_vec[k])
            {
                throw out_of_range("Indices out of Range for dimension #" + std::to_string(k) + ", max index allowed is " + std::to_string(shape_vec[k] - 1) + ".");
            }
            index += strides[k] * ind_temp;
        }

        return values.get()[index];
    }

    virtual void get_rates(double *out_array, size_t length, const vector<int *> &indices) const
    {

        if (!has_values)
        {
            throw logic_error("Not values have been set before querying."); // TODO: testcase
        }

        if (indices.size() != dimensions)
        {
            throw domain_error("Dimension of indices does not match those of the data"); // TODO: testcase
        }

        for (size_t j = 0; j < length; j++)
        {

            int index = 0;
            for (unsigned k = 0; k < dimensions; k++)
            {
                int ind_temp = indices[k][j] - offsets[k];
                if (ind_temp < 0 || ind_temp >= shape_vec[k])
                {
                    throw out_of_range("Indices out of Range for dimension #" + std::to_string(k) + ", max length is " + std::to_string(shape_vec[k]) + ".");
                }
                index += strides[k] * ind_temp;
            }

            out_array[j] = values.get()[index];
        }
    }

    /// Given a vector of indexes take only the dimensions where the values is "-1" in full
    //  and otherwise restrict to the index provided
    virtual shared_ptr<CStandardRateProvider> slice(const vector<int> &indices) const;

    // perform a slicing operation into another provider object, if possible
    // using the already allocated memory of the other provider
    void slice_into(const vector<int> &indices, CBaseRateProvider *other) const override;
};

shared_ptr<CBaseRateProvider> CStandardRateProvider::clone() const
{
    auto p_clone = make_shared<CStandardRateProvider>();

    // deep copy of all attributes
    if (this->values != nullptr)
    {
        p_clone->values = std::shared_ptr<double[]>(new double[capacity], std::default_delete<double[]>());
        for (int j = 0; j < capacity; j++)
        {
            p_clone->values[j] = this->values[j];
        }
    }

    p_clone->has_values = this->has_values;
    p_clone->number_values = this->number_values;
    p_clone->capacity = this->capacity;

    copy(this->risk_factors.begin(), this->risk_factors.end(), back_inserter(p_clone->risk_factors));

    copy(this->shape_vec.begin(), this->shape_vec.end(), back_inserter(p_clone->shape_vec));
    copy(this->strides.begin(), this->strides.end(), back_inserter(p_clone->strides));
    copy(this->offsets.begin(), this->offsets.end(), back_inserter(p_clone->offsets));

    p_clone->dimensions = this->dimensions;

    return p_clone;
}

void CStandardRateProvider::set_values(vector<int> &shape_vec_in, vector<int> &offsets_in, double *ext_vals)
{
    // this method allocates memory for the values, copies them and
    // sets the related member variables

    if (has_values)
    {
        // cout << "Freeing Memory" << "\n";
        // delete[] values;
        // values = nullptr;
        // has_values = false;
        throw domain_error("Values already set.");
    }

    // dimension is determined by the number of risk factors
    dimensions = (unsigned)risk_factors.size();

    // validate and copy vectors
    if (dimensions == 0)
    {
        if (offsets_in.size() != 1)
        {
            throw domain_error("Dimension 0 requires exactly one offset value.");
        }
        if (shape_vec_in.size() != 1)
        {
            throw domain_error("Dimension 0 requires exactly one shape_vec value.");
        }
        if (shape_vec_in[0] != 1)
        {
            throw domain_error("Dimension 0 requires exactly a shape vector [1].");
        }
        if (offsets_in[0] != 0)
        {
            throw domain_error("Dimension 0 requires an offset vector [0].");
        }
    }
    else
    {
        if (offsets_in.size() != dimensions)
        {
            throw domain_error("Offsets length must match number of risk_factors.");
        }
        if (shape_vec_in.size() != dimensions)
        {
            throw domain_error("Shape_vec length must match number of risk_factors.");
        }
    }
    shape_vec = shape_vec_in;
    offsets = offsets_in;

    set_strides();
    // // calculate the strides
    // strides = vector<int>(shape_vec_in.size(), 1); // initialize with 1s
    // int acc_dims = 1;
    // for (int i = (int)shape_vec_in.size() - 1; i >= 0; i--)
    // {
    //     strides[i] = acc_dims;
    //     acc_dims *= shape_vec_in[i];
    // }

    // determine number of elements in values
    number_values = 1; // applies if dimension == 0
    if (dimensions > 0)
    {
        for (unsigned i = 0; i < (unsigned)shape_vec_in.size(); i++)
        {
            number_values *= shape_vec_in[i];
        }
    }

    // allocate a new array on the heap
    // values = new double[number_values];
    capacity = number_values;
    values = std::shared_ptr<double[]>(new double[capacity], std::default_delete<double[]>());
    has_values = true;

    // copy the data over
    for (int j = 0; j < number_values; j++)
    {
        values.get()[j] = ext_vals[j];
    }
}

string CStandardRateProvider::to_string() const
{
    string s = "<CStandardRateProvider with RF (";
    bool first = true;
    for (auto rf : risk_factors)
    {
        if (!first)
        {
            s += ", ";
        }
        s += CRiskFactors_names(rf);
        first = false;
    }
    return s + ")>";
}

shared_ptr<CStandardRateProvider> CStandardRateProvider::slice(const vector<int> &indices) const
{
    /// Given a vector of indexes take only the dimensions where the values is "-1" in full
    //  and otherwise restrict to the index provided

    if (indices.size() != dimensions)
    {
        throw domain_error("Dimension of indices does not match those of the data"); // TODO: testcase
    }

    auto slicedProviderPtr = make_shared<CStandardRateProvider>();

    vector<int> shape_vec_sliced;
    vector<int> offsets_sliced;

    // find all fixed dimensions
    vector<bool> dims_fixed(shape_vec.size(), false);
    int required_size = 1;
    for (unsigned d = 0; d < dimensions; d++)
    {
        if (indices[d] != -1)
        {
            dims_fixed[d] = true;
        }
        else
        {
            required_size *= shape_vec[d];
            // cout << "Adding rf: " << CRiskFactors_names(risk_factors[d]);
            slicedProviderPtr->add_risk_factor(risk_factors[d]);
            shape_vec_sliced.push_back(shape_vec[d]);
            offsets_sliced.push_back(offsets[d]);
        }
    }

    // print_vec<int>(indices, "indices");
    // print_vec<int>(offsets_sliced, "offsets_sliced");
    // print_vec<int>(shape_vec_sliced, "shape_vec_sliced");

    vector<int> bounds_lower(shape_vec.size(), 0);
    vector<int> bounds_upper(shape_vec.size(), 0);

    // cout << "Required sized: " << required_size << "\n";

    // temporary storage space
    double *new_vals = new double[required_size];

    // determine the bounds
    for (unsigned d = 0; d < dimensions; d++)
    {
        if (dims_fixed[d])
        {
            bounds_lower[d] = indices[d] - offsets[d];
            bounds_upper[d] = indices[d] - offsets[d] + 1; // exclusive
            if (bounds_lower[d] < 0 || bounds_upper[d] > shape_vec[d])
            {
                throw domain_error("Slicing indexes exceed dimensions"); // TODO: testcase
            }
        }
        else
        {
            bounds_lower[d] = 0;
            bounds_upper[d] = shape_vec[d]; // exclusive
        }
    }

    // print_vec<int>(bounds_lower, "bounds_lower");
    // print_vec<int>(bounds_upper, "bounds_upper");

    vector<int> counters = bounds_lower;
    int new_val_counter = 0;
    bool incremented;
    do
    {
        // calculate the index belonging to our current counter
        int index = 0;
        for (unsigned k = 0; k < dimensions; k++)
        {
            index += strides[k] * counters[k];
        }

        // cout << "Adding ";
        // print_vec(counters, "counters");

        new_vals[new_val_counter++] = values.get()[index];

        // increment
        incremented = false;
        for (int d = dimensions - 1; d >= 0; d--)
        {
            if (counters[d] + 1 < bounds_upper[d])
            {
                counters[d] += 1;
                for (int d2 = d + 1; d2 <= ((int)dimensions) - 1; d2++)
                {
                    counters[d2] = bounds_lower[d2];
                }
                incremented = true;
                break;
            }
        }
    } while (incremented);

    // special case: reduction to constant provider
    if (required_size == 1)
    {
        if (shape_vec_sliced.size() == 0)
        {
            shape_vec_sliced.push_back(1);
        }
        if (offsets_sliced.size() == 0)
        {
            offsets_sliced.push_back(0);
        }
    }

    // print_vec<int>(shape_vec_sliced, "shape_vec_sliced");
    // print_vec<int>(offsets_sliced, "offsets_sliced");
    // cout << "Dimension slice" << slicedProviderPtr->risk_factors.size() << "\n";
    // cout << "new_vals: " ;
    // for (auto i = 0; i < required_size; i++) {
    //    std::cout << new_vals[i] << ' ';
    // }
    // cout << "\n";

    slicedProviderPtr->set_values(shape_vec_sliced, offsets_sliced, new_vals);

    delete[] new_vals;

    return slicedProviderPtr;
}

// Perform a slicing operation into another provider object, if possible
// using the already allocated memory of the other provider.
// Slicing means given a vector of indexes (the first argument) take only the dimensions where the values is "-1" in full
// and otherwise restrict to the index provided.
void CStandardRateProvider::slice_into(const vector<int> &indices, CBaseRateProvider *other_in) const
{

    // CStandardRateProvider &other = *dynamic_pointer_cast<CStandardRateProvider>(other_in);

    CStandardRateProvider *other = dynamic_cast<CStandardRateProvider *>(other_in);

    if (indices.size() != dimensions)
    {
        throw domain_error("Dimension of indices does not match those of the data"); // TODO: testcase
    }

    if (!other->has_values)
    {
        throw domain_error("Memory needs to be allocated when slicing into");
    }

    other->risk_factors.resize(0);
    other->shape_vec.resize(0);
    other->offsets.resize(0);
    other->dimensions = 0;

    // find all fixed dimensions
    vector<bool> dims_fixed(shape_vec.size(), false);
    int required_size = 1;
    for (unsigned d = 0; d < dimensions; d++)
    {
        if (indices[d] != -1)
        {
            dims_fixed[d] = true;
        }
        else
        {
            required_size *= shape_vec[d];
            other->add_risk_factor(risk_factors[d]);
            other->shape_vec.push_back(shape_vec[d]);
            other->offsets.push_back(offsets[d]);
            other->dimensions++;
        }
    }

    vector<int> bounds_lower(shape_vec.size(), 0);
    vector<int> bounds_upper(shape_vec.size(), 0);

    if (other->capacity < required_size)
    {
        throw domain_error("Capacity too small for slicing."); // TODO: testcase
    }

    other->number_values = required_size;
    double *new_vals = other->values.get(); //  double[required_size];

    // determine the bounds
    for (unsigned d = 0; d < dimensions; d++)
    {
        if (dims_fixed[d])
        {
            bounds_lower[d] = indices[d] - offsets[d];
            bounds_upper[d] = indices[d] - offsets[d] + 1; // exclusive
            if (bounds_lower[d] < 0 || bounds_upper[d] > shape_vec[d])
            {
                throw domain_error("Slicing indexes exceed dimensions"); // TODO: testcase
            }
        }
        else
        {
            bounds_lower[d] = 0;
            bounds_upper[d] = shape_vec[d]; // exclusive
        }
    }

    vector<int> counters = bounds_lower;
    int new_val_counter = 0;
    bool incremented;
    do
    {
        // calculate the index belonging to our current counter
        int index = 0;
        for (unsigned k = 0; k < dimensions; k++)
        {
            index += strides[k] * counters[k];
        }

        // cout << "Adding ";
        // print_vec(counters, "counters");

        new_vals[new_val_counter++] = values.get()[index];

        // increment
        incremented = false;
        for (int d = dimensions - 1; d >= 0; d--)
        {
            if (counters[d] + 1 < bounds_upper[d])
            {
                counters[d] += 1;
                for (int d2 = d + 1; d2 <= ((int)dimensions) - 1; d2++)
                {
                    counters[d2] = bounds_lower[d2];
                }
                incremented = true;
                break;
            }
        }
    } while (incremented);

    // special case: reduction to constant provider
    if (required_size == 1)
    {
        if (other->shape_vec.size() == 0)
        {
            other->shape_vec.push_back(1);
        }
        if (other->offsets.size() == 0)
        {
            other->offsets.push_back(0);
        }
    }

    // calculate the strides
    other->set_strides();
}

void CStandardRateProvider::set_strides()
{
    // calculate the strides
    strides.assign(shape_vec.size(), 1);
    int acc_dims = 1;
    for (int i = (int)shape_vec.size() - 1; i >= 0; i--)
    {
        strides[i] = acc_dims;
        acc_dims *= shape_vec[i];
    }
}

#endif
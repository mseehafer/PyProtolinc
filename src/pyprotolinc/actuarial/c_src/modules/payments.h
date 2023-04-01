/**
 * @file payments.h
 * @author M. Seehafer
 * @brief Data structures related to the payments
 * @version 0.2.0
 * @date 2022-10-16
 *
 * @copyright Copyright (c) 2022
 *
 */
#ifndef C_PAYMENTS_H
#define C_PAYMENTS_H

#include <vector>
#include <utility>
#include <unordered_map>
#include <memory>
#include <iostream>
#include <chrono>
#include <set>

// include to allow unordered_dicts with pairs as key
#include "utils.h"

using namespace std;


struct ConditionalPayout
{
    /// @brief type of payment
    int payment_index;

    /// @brief Sequence of conditonal payments
    vector<double> cond_payments;

    // ConditionalPayout(ConditionalPayout &&o): payment_index(o.payment_index), cond_payments(std::move(o.cond_payments)) {}

    // ConditionalPayout() {}
    string to_string() {
        return "<ConditionalPayout(payment_index=" + std::to_string(payment_index) 
        + ", cond_payments=[" + std::to_string(cond_payments[0]) + ", " + std::to_string(cond_payments[0]) + "...]"
        + ">";
    }
};

/// @brief Payments that are due when in a given state
struct StateConditionalRecordPayout
{
    int state_index;
    vector<ConditionalPayout> payments;

    StateConditionalRecordPayout(int si): state_index(si) {}

    StateConditionalRecordPayout(StateConditionalRecordPayout &&o): state_index(o.state_index), payments(std::move(o.payments)) {}

    string to_string() {
         return "<StateConditionalRecordPayout(state_index=" + std::to_string(state_index);
    }
};

/// @brief Payments that are due when a state transition occurs
struct TransitionConditionalRecordPayout
{
    int _state_index_from;
    int _state_index_to;
    vector<ConditionalPayout> payments;

    TransitionConditionalRecordPayout(int state_index_from, int state_index_to): _state_index_from(state_index_from), _state_index_to(state_index_to) {}
    
    TransitionConditionalRecordPayout(TransitionConditionalRecordPayout &&o): _state_index_from(o._state_index_from), 
                                                                              _state_index_to(o._state_index_to),
                                                                              payments(std::move(o.payments)) {}
};


/**
 * @brief Represent the payment matrices of a subportfolio
 * 
 */
class AggregatePayments
{
private:
    // for each record maintain a pointer to a map. The map associates the state_index with
    // a StateConditionalRecordPayout structure
    vector<shared_ptr<unordered_map<int, StateConditionalRecordPayout>>> state_payouts;

    // for each record maintain a pointer to a map. The map associates the 
    // pair (from_state_index, to_state_index) with
    // a TransitionConditionalRecordPayout structure
    vector<shared_ptr<unordered_map<pair<int, int>,  TransitionConditionalRecordPayout>>> transition_payouts;

    // unique_ptr<double[]> payments_test;
    int max_payment_type_index_used = -1;
    std::set<int> payment_types_used;
    size_t _size;

public:
    AggregatePayments(size_t size): _size(size) {
        state_payouts.reserve(size);
        transition_payouts.reserve(size);

        // initialize
        for(int j = 0; j < size; j++) {
            state_payouts.push_back(make_shared<unordered_map<int, StateConditionalRecordPayout>>());
            transition_payouts.push_back(make_shared<unordered_map<pair<int, int>, TransitionConditionalRecordPayout>>());
        }
    }

    // check and comment what this constructor is for
    AggregatePayments(size_t size, const std::set<int> &_payment_types_used): _size(size),
                                                                              payment_types_used(_payment_types_used) {
        state_payouts.reserve(size);
        transition_payouts.reserve(size);

        auto iter =  _payment_types_used.begin();
        while (iter !=  _payment_types_used.end()) {
            if(*iter > max_payment_type_index_used) {
                max_payment_type_index_used = *iter;
            }
            ++iter;
        }

        // initialize
        for(int j = 0; j < size; j++) {
            state_payouts.push_back(make_shared<unordered_map<int, StateConditionalRecordPayout>>());
            transition_payouts.push_back(make_shared<unordered_map<pair<int, int>, TransitionConditionalRecordPayout>>());
        }
    }

    const std::set<int> &get_payment_types_used() const {
        return payment_types_used;
    }

    int get_max_payment_index_used() const {
        return max_payment_type_index_used;
    }

    /// @brief  Inject a payment matrix from python
    /// @param state_index 
    /// @param payment_type_index 
    /// @param payment_matrix 
    /// @param num_policies 
    /// @param num_timesteps 
    void add_cond_state_payment(int state_index,
                                int payment_type_index,
                                double *payment_matrix,
                                const int num_policies,
                                const int num_timesteps)
    {

         // cout << "Adding payment with payment_index=" << payment_type_index << std::endl;
         if (state_payouts.size() != num_policies) 
         {
            throw domain_error("Incompatible Payout sizes.");
         }

        // check if payment type is already used
        if (payment_types_used.count(payment_type_index) > 0) {
            throw domain_error("Payment type index used multiple times.");
        } else {
            payment_types_used.insert(payment_type_index);
            if (max_payment_type_index_used < payment_type_index) {
                max_payment_type_index_used = payment_type_index;
            }
        }

        // // do a single copy operation
        // std::chrono::duration<double> duration_payment_copy_at_once;
        // const auto time_before_copy_at_once = std::chrono::system_clock::now();
        // payments_test = unique_ptr<double[]>(new double[num_policies * num_timesteps], std::default_delete<double[]>());
        // memcpy(payments_test.get(), &payment_matrix[0], num_policies * num_timesteps * sizeof(double));
        // duration_payment_copy_at_once += std::chrono::system_clock::now() - time_before_copy_at_once;
        // std::cout << "Copy payments at once took " << duration_payment_copy_at_once.count()<< "s" << std::endl;

        std::chrono::duration<double> duration_payment_copy;
        // iterate over the policies
        int row_count = 0;
        for (auto p_map: state_payouts) {

            auto state_cond_payout = p_map->find(state_index);
            if (state_cond_payout == p_map->end()) {
                // state does not yet exist
                p_map -> insert(pair<int, StateConditionalRecordPayout>(state_index, StateConditionalRecordPayout(state_index)));
                state_cond_payout = p_map->find(state_index); // do I need to search again?
            }

            StateConditionalRecordPayout &payout = (*state_cond_payout).second;
            ConditionalPayout cp;
            cp.payment_index = payment_type_index;
            cp.cond_payments.reserve(num_timesteps);

            // copy data over into vector
            const auto time_before_copy = std::chrono::system_clock::now();
            cp.cond_payments.insert(cp.cond_payments.begin(), &payment_matrix[row_count * num_timesteps], &payment_matrix[(row_count + 1)* num_timesteps]);
            duration_payment_copy += std::chrono::system_clock::now() - time_before_copy;
            // cp.cond_payments.resize(num_timesteps);
            // memcpy(&cp.cond_payments[0], &payment_matrix[row_count * num_timesteps], num_timesteps * sizeof(double));
            payout.payments.push_back(std::move(cp));
            row_count++;
        }
        // std::cout << "Copy payments in loop took " << duration_payment_copy.count() << "s" << std::endl;        
    }


    /// @brief  Inject a payment matrix from python
    /// @param state_index_from  State before the transition
    /// @param state_index_to  State after the transition
    /// @param payment_type_index 
    /// @param payment_matrix 
    /// @param num_policies 
    /// @param num_timesteps 
    void add_transition_payment(int state_index_from,
                                int state_index_to,
                                int payment_type_index,
                                double *payment_matrix,
                                const int num_policies,
                                const int num_timesteps)
    {
         if (transition_payouts.size() != num_policies) 
         {
            throw domain_error("Incompatible Payout sizes.");
         }

        // check if payment type is already used
        if (payment_types_used.count(payment_type_index) > 0) {
            throw domain_error("Payment type index used multiple times.");
        } else {
            payment_types_used.insert(payment_type_index);
            if (max_payment_type_index_used < payment_type_index) {
                max_payment_type_index_used = payment_type_index;
            }
        }

        // iterate over the policies
        int row_count = 0;
        for (auto p_map: transition_payouts) {
            pair<int, int> pair_index = pair<int, int>(state_index_from, state_index_to);

            auto transition_payout_it = p_map->find(pair_index);
            if (transition_payout_it == p_map->end()) {
                // state does not yet exist
                p_map -> insert(pair<pair<int, int>, TransitionConditionalRecordPayout>(pair_index, TransitionConditionalRecordPayout(state_index_from, state_index_to)));
                transition_payout_it = p_map->find(pair_index);
            }

            TransitionConditionalRecordPayout &payout = (*transition_payout_it).second;
            ConditionalPayout cp;
            cp.payment_index = payment_type_index;
            cp.cond_payments.reserve(num_timesteps);

            // copy data over into vector
            cp.cond_payments.insert(cp.cond_payments.begin(), &payment_matrix[row_count * num_timesteps], &payment_matrix[(row_count + 1)* num_timesteps]);
            payout.payments.push_back(std::move(cp));
            row_count++;
        }
    }


    /// use internally in C++ when splitting the payments into groups (for the parallelization)
    void add_single_record_payments(shared_ptr<unordered_map<int, StateConditionalRecordPayout>> single_record_payments, size_t ind) {
        state_payouts[ind] = single_record_payments;
    }

    /// use internally in C++ when splitting the payments into groups (for the parallelization)
    void add_single_record_transition_payments(shared_ptr<unordered_map<pair<int, int>, TransitionConditionalRecordPayout>> single_record_payments, size_t ind) {
        transition_payouts[ind] = single_record_payments;
    }

    shared_ptr<unordered_map<int, StateConditionalRecordPayout>> get_single_record_payments(size_t index) const {
        return state_payouts[index];
    }

    shared_ptr<unordered_map<pair<int, int>, TransitionConditionalRecordPayout>> get_single_record_transition_payments(size_t index) const {
        return transition_payouts[index];
    }

};



#endif
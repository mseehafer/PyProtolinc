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
#include <unordered_map>
#include <memory>
#include <iostream>
#include <chrono>

using namespace std;

struct ConditionalPayout
{
    /// @brief type of payment
    int payment_index;

    /// @brief Sequence of conditonal payments
    vector<double> cond_payments;

    // ConditionalPayout(ConditionalPayout &&o): payment_index(o.payment_index), cond_payments(std::move(o.cond_payments)) {}

    // ConditionalPayout() {}
};

struct StateConditionalRecordPayout
{
    int state_index;
    vector<ConditionalPayout> payments;

    StateConditionalRecordPayout(int si): state_index(si) {}

    StateConditionalRecordPayout(StateConditionalRecordPayout &&o): state_index(o.state_index), payments(std::move(o.payments)) {}
};

// struct TransitionConditionalRecordPayout
// {
//     int state_index_from;
//     int state_index_to;
//     vector<ConditionalPayout> payments;
// }


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


public:
    AggregatePayments(size_t reserve_size) {
        state_payouts.reserve(reserve_size);
    }

    void add_cond_state_payment(int state_index, int payment_type_index, double *payment_matrix, const int num_policies, const int num_timesteps)
    {

        // check if this is the first payment added
        if (state_payouts.size() == 0)
        {

            // initialize
            for(int j = 0; j < num_policies; j++) {
                state_payouts.push_back(make_shared<unordered_map<int, StateConditionalRecordPayout>>());
            }

        } else if (state_payouts.size() != num_policies) 
        {
            throw domain_error("Incompatible Payout sizes.");
    
        }

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

        
        std::cout << "Copy payments in loop took " << duration_payment_copy.count() << "s" << std::endl;

    }

};



#endif
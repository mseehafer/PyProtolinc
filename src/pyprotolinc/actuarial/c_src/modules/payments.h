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

using namespace std;


struct ConditionalPayout
{
    /// @brief type of payment
    int payment_index;

    /// @brief Sequence of conditonal payments
    vector<double> cond_payments;
};

struct StateConditionalRecordPayout
{
    int state_index;
    vector<ConditionalPayout> payments;

    StateConditionalRecordPayout(int si): state_index(si) {}
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

    void add_cond_state_payment(int state_index, int payment_type_index, double *payment_matrix, int num_policies, int num_timesteps)
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
            for(int c=0; c < num_timesteps; c++) {
                cp.cond_payments.push_back(payment_matrix[row_count * num_timesteps + c]);
            }
            payout.payments.push_back(cp);

            row_count++;
        }

    }

};



#endif
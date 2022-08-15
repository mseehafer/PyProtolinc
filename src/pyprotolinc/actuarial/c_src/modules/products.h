
#ifndef C_VALUATION_PRODS_H
#define C_VALUATION_PRODS_H

#include "c_valuation.h"


class MortalityProductDefinition {
protected:
    int premium_payment_mode;   // 0 - single premium
                                // 1 yearly premiums
                                // 2 monthly premiums
    int lapse_possibilites;     // 0 - at contract year end
                                // 1 - at end of month

    int lapse_benefit_type;     // 0 - nothing
                                // 1 - local gaap reserve

    int death_benefit_type;     // 0 - nothing
                                // 1 - fixed individual amount
    
    int maturity_benefit_type;  // 0 - nothing
                                // 1 - fixed individual amount

    int escalation_type;        // 0 - no escalation
                                // 1 - fixed escalation percentage
    double fixed_escalation_perc; 
};


// eine Art abstrakte Klasse
class GenericMortalityProduct {
protected:
CSeriatimRecord &_rec;
public:
    GenericMortalityProduct(CSeriatimRecord &rec) : _rec(rec) {}

    virtual double get_benefit_if_died(int year, int month) {return 0;}
    virtual double get_benefit_if_survived(int year, int month) {return 0;}
    virtual double get_benefit_if_lapsed(int year, int month) {return 0;}
    virtual bool is_premium_due(int year, int month) {return false;}
};


class SimpleTermProduct: public GenericMortalityProduct {
public:
    SimpleTermProduct(CSeriatimRecord &rec): GenericMortalityProduct(rec) {}

    virtual double get_benefit_if_died(int year, int month) {
        return (double) _rec.get_sum_insured();
    }

    virtual double get_benefit_if_survived(int year, int month) { return 0;}

    virtual double get_benefit_if_lapsed(int year, int month) {return 0;}
    
    virtual bool is_premium_due(int year, int month) {
        // returns true if this is a premium paying month
        return _rec.get_issue_month() == month;
    }
};





#endif
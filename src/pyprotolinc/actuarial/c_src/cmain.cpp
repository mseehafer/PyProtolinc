

#include <iostream>
#include "modules/time_axis.h"
#include "modules/providers.h"
#include "modules/assumption_sets.h"
#include "modules/portfolio.h"
#include "modules/run_config.h"
#include "modules/run_result.h"
#include "modules/runner.h"


using namespace std;


void add_policies(CPolicyPortfolio &portfolio) {
   // create a policy and add to the portfolio
    shared_ptr<CPolicy> policy = make_shared<CPolicy>(
                   1,            // cession_id,
                   19850407,     // dob_long,
                   20200801,     // issue_date_long,
                   0,            // disablement_date_long,
                   0,            // gender,
                   0,            // smoker_status,
                   100000,       //sum_insured,
                   0.02,         // reserving_rate,
                   "TERM"         // product
                   );
    portfolio.add(policy);
}


void run_calculation(void) {

    cout << "PyProtolincCore -- testrun" << endl;
    
    unsigned state_dimension = 2;
    
    short ptf_year = 2021;
    short ptf_month = 12;
    short ptf_day = 20;
    
    // create portfolio
    auto portfolio = make_shared<CPolicyPortfolio> (ptf_year, ptf_month, ptf_day);
    add_policies(*portfolio);

    // create assumptions set
    auto assumption_set = make_shared<CAssumptionSet>(state_dimension);
    auto rp = make_shared<CConstantRateProvider>(0.1);
    assumption_set->set_provider(0, 1, rp);

    // create a config object
    TimeStep time_step = TimeStep::MONTHLY;
    int years_to_simulate = 2;
    int num_cpus = 1;
    bool use_multicore = false;
    auto run_config = CRunConfig(state_dimension, time_step, years_to_simulate, num_cpus, use_multicore, assumption_set);

    // create results set
    //shared_ptr<TimeAxis> ta = make_time_axis(run_config, ptf_year, ptf_month, ptf_day);
    auto run_results = RunResult();

    // calculation
    run_c_valuation(run_config, portfolio, run_results);

    // inspect the result


    cout << "DONE" << endl;

}



int main(void) {

    cout << "PyProtolincCore -- testrun" << endl;
    run_calculation();

    return 0;
}
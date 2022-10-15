/**
 * @file cmain.cpp
 * @author M. Seehafer
 * @brief 
 * @version 0.2.0
 * @date 2022-08-27
 * 
 * @copyright Copyright (c) 2022
 * 
 * File is used during development to value a single policy.
 * 
 */

#include <iostream>
#include <fstream>

#include "modules/log.h"

#include "modules/time_axis.h"
#include "modules/providers.h"
#include "modules/assumption_sets.h"
#include "modules/portfolio.h"
#include "modules/run_config.h"
#include "modules/run_result.h"
#include "modules/runner.h"


using namespace std;


/**
 * @brief Adds a number of (hard-coded)policies to the portfolio
 * 
 * @param portfolio 
 */
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
                   "TERM",       // product
                   0             // initial state
                   );
    portfolio.add(policy);
}


/// Write the result matrix to a CSV file
void output_results(RunResult &run_result, string outfile_name="cresults.csv", bool output_to_console = false) {
    
    // get result dimension and headers
    auto rows = run_result.size();
    auto headers = run_result.get_result_header_names();
    auto cols = headers.size();

    // copy result into array
    auto res_array_ptr = std::unique_ptr<double[]>(new double[rows*cols], std::default_delete<double[]>());
    for(int i=0; i<rows*cols;i++) {
        res_array_ptr.get()[i] = 0;
    }
    run_result.copy_results(res_array_ptr.get(), (int) rows, (int) cols);

    std::ofstream result_file;
    result_file.open(outfile_name);

    // write the headers
    bool is_first = true;
    for(auto c: headers) {
        if (!is_first) {
            result_file << ",";
            if (output_to_console) {
                cout << ",";    
            }
        } else {
            is_first = false;
        }
        result_file << c;
        if (output_to_console) {
            cout << c;
        }
    }
    result_file << "\n";
    if (output_to_console) {
        cout << "\n";
    }

    // write data rows
    for(auto r=0; r < rows; r++) {
        is_first = true;
        for(auto c=0; c < cols; c++) {
            if (!is_first) {
                result_file << ",";
                if (output_to_console) {
                    cout << ",";
                }
            } else {
                is_first = false;
            }
            result_file << res_array_ptr.get()[cols*r + c];
            if (output_to_console) {
                cout << res_array_ptr.get()[cols*r + c];
            }
        }
        result_file << "\n";
        if (output_to_console) {
            cout << "\n";
        }
    }

   result_file.close();

}

/// Encapsulate the calculation run. Creates test data, passes them to the runner for processing and outputs the results.
///
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
    auto rp2 = make_shared<CConstantRateProvider>(0.01);
    assumption_set->set_provider(0, 1, rp);
    assumption_set->set_provider(1, 0, rp2);

    // create a config object
    TimeStep time_step = TimeStep::MONTHLY;
    int years_to_simulate = 120;
    int num_cpus = 1;
    bool use_multicore = false;
    int max_age = 120;
    auto run_config = CRunConfig(state_dimension, time_step, years_to_simulate, num_cpus, use_multicore, assumption_set, max_age);

    // create results set
    //shared_ptr<TimeAxis> ta = make_time_axis(run_config, ptf_year, ptf_month, ptf_day);
    //auto run_results = RunResult();

    // calculation
    auto run_result = run_c_valuation(run_config, portfolio);

    output_results(*run_result);

    cout << "DONE" << endl;

}



int main(void) {
    initLogger( "clogfile.log", ldebug);
    
    L_(linfo) << "info";
    
    //L_(lwarning) << "Ops, variable x should be " << expectedX << "; is " << realX;
    
    run_calculation();

    endLogger();    

    

    return 0;
}
/*
c_valuation.cpp

*/

#include "c_valuation.h"
#include "products.h"

#include <string>
#include <unordered_map>
#include <cmath>

using namespace std;



void get_simulation_duration(CSeriatimRecord &rec, int (&simul_duration)[2]) {

    // assert issue_date <= portfolio-date
    // assert issue_date + coverage_years > portfolio-date
    
    // assert portfolio_date is end-of-month or first of month -> will be treated
    // as end of that month
    
    // simulation will always start on the first of that month (respectively the month after)

    // policy start date is always moved to the nearst first of the month 
    int issue_year = rec.get_issue_year(); 
    int issue_month = (rec.get_issue_day() >= 15 ? 1 : 0) + rec.get_issue_month();
    if (issue_month == 13) {
        issue_month = 1;
        issue_year++;
    }

    // simulation_end_date - last month to be included in the simulation
    // the end date is the issue date shifted by coverage-years into the future
    int end_year = rec.get_issue_year() + rec.get_coverage_years();
    int end_month = issue_month - 1;
    if (end_month == 0) {
        end_year--;
        end_month = 12;
    }

    // remaining duration is now from portfolio date until end-date, both the dates are end of month
    int total_month_remaining = end_month - rec.get_portfolio_month() + 12*(end_year -rec.get_portfolio_year());

    simul_duration[0] = total_month_remaining / 12;
    simul_duration[1] = total_month_remaining % 12;
}


// Calculate projection for one record
// return the number of rows filled
int project_record(CSeriatimRecord &rec,
                   double* proj_premiums,
                   double* proj_claims,
                   double* reserve_lg_boy,
                   double* sum_insured_boy,
                   std::shared_ptr<std::vector<double>> p_mort_assump_be,
                   std::shared_ptr<std::vector<double>> p_mort_assump_locgaap,
                   std::shared_ptr<std::vector<double>> p_lapse_assump_be,
                   std::shared_ptr<std::vector<double>> p_lapse_assump_locgaap,
                   std::shared_ptr<std::vector<double>> p_prem_assump_be,
                   std::shared_ptr<std::vector<double>> p_prem_assump_locgaap
                   ) {

    double survival_prob_be = 1.0;
    double survival_prob_lg = 1.0;
    
    int age_in_months = rec.get_age_projection_start();
    const int age_in_years_pr_start = age_in_months / 12;
    
    std::shared_ptr<GenericMortalityProduct> prod = std::make_shared<SimpleTermProduct>(rec);
    
    // simulation duration in years and months
    int simul_duration[2] = {0,0};
    get_simulation_duration(rec, simul_duration);
    int sim_years = simul_duration[0];
    int sim_months = min(12*VECTOR_LENGTH_YEARS, max(0, 12*sim_years + simul_duration[1]));

    // set year and month, at this point this should be the month
    // before the calculation starts
    int _year = rec.get_portfolio_year();
    int _month = rec.get_portfolio_month();
    
    // assumption selection, value "-1" ensure they will be 
    // updated when going the first time through the loop
    int index_for_assumptions = -1;
    double q_be, q_lg, q_pr_be, q_pr_lg, l1;
    double q_be_yrly, q_lg_yrly, q_pr_be_yrly, q_pr_lg_yrly, l1_yrly;

    // the cash flows conditioned on survival
    // this should generate "0"-initialized arrays 
    // cf.https://stackoverflow.com/questions/5591492/array-initialization-with-0-0
    double cond_claims_lg[12*VECTOR_LENGTH_YEARS] = {};
    double cond_premium_lg[12*VECTOR_LENGTH_YEARS] = {};
    double cond_res_lg[12*VECTOR_LENGTH_YEARS] = {};

    double acc_survival_prob_be[12*VECTOR_LENGTH_YEARS] = {};
    double period_survival_prob_lg[12*VECTOR_LENGTH_YEARS] = {};

    for (int i = 0; i < sim_months; i++) {
        _month++;
        if (_month == 13) {
            _month = 1;
            _year++;
        }
 
        double benefit_if_survived = prod->get_benefit_if_survived(_year, _month);
        double benefit_if_lapsed = prod->get_benefit_if_lapsed(_year, _month);
        double benefit_if_died = prod->get_benefit_if_died(_year, _month);
        
        bool premium_is_due = prod->is_premium_due(_year, _month);
 
        sum_insured_boy[i] = survival_prob_be * benefit_if_died;

        // extract first and second order mortality assumptions
        // mortality rates are taken starting from the age at
        // projection start
        // double q_be = (is_final_year ? last_sim_year_frac : 1.0) * (*p_mort_assump_be)[i] / 1000.0;
        // double q_pr = (is_final_year ? last_sim_year_frac : 1.0) * (*p_mort_assump_locgaap)[i] / 1000.0;

        // assumption selection - depends on age for mortality
        // TODO: depends on time since issue age for lapse
        if (index_for_assumptions  != age_in_months / 12 - age_in_years_pr_start) {
            index_for_assumptions = age_in_months / 12 - age_in_years_pr_start;
            q_be_yrly =  (*p_mort_assump_be)[index_for_assumptions] / 1000.0;
            q_lg_yrly =  (*p_mort_assump_locgaap)[index_for_assumptions] / 1000.0;
            q_pr_be_yrly =  (*p_prem_assump_be)[index_for_assumptions] / 1000.0;
            q_pr_lg_yrly =  (*p_prem_assump_locgaap)[index_for_assumptions] / 1000.0;

            // extract lapse assumptions
            l1_yrly = (*p_lapse_assump_be)[index_for_assumptions] / 1000.0;

            // convert to monthly rates
            // here one method to convert the rates to monthly
            // q_be /= 12.0;
            // q_pr /= 12.0;
            // l1 /= 12.0;
            // q_pr_be /= 12.0;
            // q_pr_lg /= 12.0;
         
            // here another one (which is relatively really expensive in run time)
            q_be = min(1.0, 1.0 - pow(max(0.0, 1.0 - q_be_yrly), 1.0/12.0));
            q_lg = min(1.0, 1.0 - pow(max(0.0, 1.0 - q_lg_yrly), 1.0/12.0));
            q_pr_be = min(1.0, 1.0 - pow(max(0.0, 1.0 - q_pr_be_yrly), 1.0/12.0));
            q_pr_lg = min(1.0, 1.0 - pow(max(0.0, 1.0 - q_pr_lg_yrly), 1.0/12.0));
            l1 = min(1.0, 1.0 - pow(max(0.0, 1.0 - l1_yrly), 1.0/12.0));
        }

        // premiums will be collected at the beginning of the month,
        // i.e. before the survival probabilities are updated
        
        // yearly premium paying mode:
        proj_premiums[i] = premium_is_due ? benefit_if_died * survival_prob_be * q_pr_be_yrly : 0.0; // TODO: add component for lapse and survival
        // monthly premium paying mode:
        //proj_premiums[i] =  benefit_if_died * survival_prob_be * q_pr_be; // TODO: add component for lapse and survival
        
        proj_claims[i] = -benefit_if_died * survival_prob_be * q_be;
    
        cond_claims_lg[i] = -benefit_if_died * q_lg;
        cond_premium_lg[i] = benefit_if_died * q_pr_lg;

        period_survival_prob_lg[i] = (1 - q_lg) * (1 - l1);
        survival_prob_lg *= period_survival_prob_lg[i];
        
        survival_prob_be *= (1 - q_be) * (1 - l1);
        acc_survival_prob_be[i] = survival_prob_be;

        age_in_months++;        
    } // end projection loop
    
    // calculation of local gaap reserves
    if (sim_months > 0) {

        double reserving_interest = pow(1 + 0.05, 1.0/12.0);
        double reserve_discount = 1.0 / reserving_interest;

        // we first calculate the reserve vector conditionally on survival
        int J=sim_months-1;
        // premium is beg.of month and needs no discounting
        reserve_lg_boy[J] = -(reserve_discount *  cond_claims_lg[J]  + cond_premium_lg[J]);
        J--;

        for(; J>=0; J--) {
            reserve_lg_boy[J] = reserve_discount * (reserve_lg_boy[J+1]*period_survival_prob_lg[J] 
                                                     - cond_claims_lg[J])
                               - cond_premium_lg[J];
            // now combine the value from the next year
            // with the survival probability 
            reserve_lg_boy[J+1] *= acc_survival_prob_be[J];
        }
        // note: value for J=0 does not need the survival probability as it is one anyway

    }

    // calculation of expenses
    // TODO
    return sim_months;
}


void _valuation(shared_ptr<double> output_in,
                int no_cols,
                vector<shared_ptr<CSeriatimRecord>> &pf,
                CBaseAssumptions *be_ass,
                CBaseAssumptions *locgaap_ass
                ) {
    
    double *output = output_in.get();

    // caches
    auto mortality_map_be = AssumptionMap();
    auto mortality_map_locgaap = AssumptionMap();
    auto lapse_map_be = AssumptionMap();
    auto lapse_map_locgaap = AssumptionMap();
    auto prem_map_be = AssumptionMap();
    auto prem_map_locgaap = AssumptionMap();

    // look up assumptions or calculate new
    shared_ptr<vector<double>> ma_be = nullptr;
    shared_ptr<vector<double>> pa_be = nullptr;
    shared_ptr<vector<double>> la_be = nullptr;
    shared_ptr<vector<double>> ma_locgaap = nullptr;
    shared_ptr<vector<double>> pa_locgaap = nullptr;
    shared_ptr<vector<double>> la_locgaap = nullptr;

    // containers for the results
    double projected_premiums[VECTOR_LENGTH_YEARS*12];
    double projected_claims[VECTOR_LENGTH_YEARS*12];
    double reserve_lg_boy[VECTOR_LENGTH_YEARS*12];
    double sum_insured_boy[VECTOR_LENGTH_YEARS*12];

    // records the number of rows actually needed in the last run
    // and thereby allows some optimization
    int rows_filled_in_run = VECTOR_LENGTH_YEARS*12;

    // iterate over records
    for(auto it = pf.begin(); it != pf.end(); ++it) {
        
        shared_ptr<CSeriatimRecord> rec = *it;

        // if (is_first) {
        //     portfolio_month = rec -> get_portfolio_month();
        //     portfolio_year = rec -> get_portfolio_year();
        // }
        
        // clear output containers for the next iteration
        // TODO: keep a variable which is passed down and which knows
        // how many values need to be overwritten
        for(int j=0; j<rows_filled_in_run; j++) {
            projected_premiums[j] = 0;
            projected_claims[j] = 0;
            reserve_lg_boy[j] = 0;
            sum_insured_boy[j] = 0;
        }

        // look-up assumptions to the current record
        // TODO: incorporate the monthly logic
        int age_proj_start = (*rec).get_age_projection_start() / 12;
        int issue_age = (*rec).get_issue_age() / 12;

        auto ma_iter = mortality_map_be.find(age_proj_start);
        if (ma_iter != mortality_map_be.end()) {
            ma_be = (*ma_iter).second;
            ma_locgaap = mortality_map_locgaap[age_proj_start];
            pa_be = prem_map_be[age_proj_start];
            pa_locgaap = prem_map_locgaap[age_proj_start];
        } else {
            // recalculate
            ma_be = be_ass->get_mortality_rates(age_proj_start, 1.0, 0);
            pa_be = be_ass->get_premium_rates(age_proj_start, 1.0, 0);
            ma_locgaap = locgaap_ass->get_mortality_rates(age_proj_start, 1.0, 0);
            pa_locgaap = locgaap_ass->get_premium_rates(age_proj_start, 1.0, 0);
            
            // add to maps
            mortality_map_be[age_proj_start] = ma_be;
            mortality_map_locgaap[age_proj_start] = ma_locgaap;
            prem_map_be[age_proj_start] = pa_be;
            prem_map_locgaap[age_proj_start] = pa_locgaap;
        }

        auto lapse_iter = lapse_map_be.find(age_proj_start - issue_age);
        if (lapse_iter != lapse_map_be.end()) {
            la_be = (*lapse_iter).second;
            la_locgaap = lapse_map_locgaap[age_proj_start - issue_age];
        } else {
            // calc policy age by some method
            la_be = be_ass->get_lapse_rates(age_proj_start - issue_age, 1.0);
            la_locgaap = locgaap_ass->get_lapse_rates(age_proj_start - issue_age, 1.0);

            // add to map
            lapse_map_be[age_proj_start - issue_age] = la_be;
            lapse_map_locgaap[age_proj_start - issue_age] = la_locgaap;
        }

        // generate results for the current record
        rows_filled_in_run = project_record(*rec,
                       projected_premiums, projected_claims,  // for the output
                       reserve_lg_boy, sum_insured_boy,
                       ma_be, ma_locgaap, la_be, la_locgaap, pa_be, pa_locgaap);

        // calculate BEL etc.
    
        // add current results to aggregated output
        for(int j=0; j<rows_filled_in_run; j++) {
            // output[no_cols*j+2] += isnan(projected_premiums[j]) ? 0.0 : projected_premiums[j];
            // output[no_cols*j+3] += isnan(projected_claims[j]) ? 0.0 : projected_claims[j];
            output[no_cols*j+2] += projected_premiums[j];
            output[no_cols*j+3] += projected_claims[j];
            output[no_cols*j+4] += reserve_lg_boy[j];
            output[no_cols*j+5] += sum_insured_boy[j];
        }

    }         
}


void valuation(double* output,
               const int no_cols,
               CPortfolio* pf,
               CBaseAssumptions *be_ass,
               CBaseAssumptions *locgaap_ass
               ) {


    // split portfolio in N groups
    const int NUM_GROUPS = 8;
    int j = 0;
    vector<shared_ptr<CSeriatimRecord>> vecs[NUM_GROUPS];
    std::vector<shared_ptr<CSeriatimRecord>>& records = pf -> get_records();

    if (records.size() == 0) {
        return;
    }

    int portfolio_year = records[0] -> get_portfolio_year();
    int portfolio_month = records[0] -> get_portfolio_month();
  
    // round robin distribution of the records into the groups
    for(auto it = records.begin(); it != records.end(); ++it) {
        vecs[j++].push_back(*it);
        if (j >= NUM_GROUPS){
            j=0;
        }
    }

    // container for the result is a vector with entries
    // for each local group. Each entry is an array
    // with length 120*12*no_cols
    // which is initialized with zero
    vector<shared_ptr<double>> output_loc;
    for(int j=0;j<NUM_GROUPS;j++) {
        std::shared_ptr<double> sp(new double[VECTOR_LENGTH_YEARS*12*no_cols], std::default_delete<double[]>());
        for(long k=0; k < VECTOR_LENGTH_YEARS * 12 * no_cols; k++) {
            sp.get()[k] = 0;
            //(*sp)[k] = 0;
        }
        output_loc.push_back(sp);
    }
    

    // value subportfolios
    #pragma omp parallel for
    for(j=0; j < NUM_GROUPS; j++) {
        // container for the local result
        //_valuation(output_loc[j], vecs[j], be_ass, locgaap_ass);
        _valuation(output_loc[j], no_cols, vecs[j], be_ass, locgaap_ass);
    }

    // sum up the results just calculated
    for (int k=0; k<NUM_GROUPS;k++) {
        for(int j=0; j<VECTOR_LENGTH_YEARS*12; j++) {
            // skip columns for year and month
            for (int i=2; i < no_cols; i++) {
                output[no_cols*j+i] += (output_loc[k]).get()[no_cols*j+i];    
            }
        }    
    }
    
    // set year and month
    int pf_year = portfolio_year;
    int pf_month = portfolio_month;
    for(int j=0; j<VECTOR_LENGTH_YEARS*12; j++) {
        pf_month++;
        if (pf_month == 13) {
            pf_month = 1;
            pf_year++;
        }
        output[no_cols*j+0] = pf_year;
        output[no_cols*j+1] = pf_month;
    }
  
}


// calculate the age in (completed) months
// given the birthday and the date of interest;
// returns -1 if not born yet at the given date
int get_age_at_date(int dob_year, int dob_month, int dob_day, int dt_year, int dt_month, int dt_day) {
    // check that person is born at dt already
    if (dt_year < dob_year || dt_year == dob_year && dt_month < dob_month ||
        dt_year == dob_year && dt_month == dob_month && dt_day < dob_day) {
          return -1; // use as a error signal
    }

    // special case equality of dates
    if (dt_year == dob_year && dt_month == dob_month && dt_day == dob_day) {
      return 0;
    }

    int full_years = (dt_month > dob_month || dob_month == dt_month && dob_day <= dt_day) ? 
                    dt_year - dob_year : dt_year - dob_year - 1;
    
    // so the last birthday before dt was at dob_year + full_years/dob_month/dob_day
    int full_months = (dt_month < dob_month || dt_month == dob_month && dt_day < dob_day) ?
                     12 + dt_month - dob_month - (dt_day < dob_day ? 1 :0)
                     : dt_month - dob_month - (dt_day < dob_day ? 1 :0);

    return 12 * full_years + full_months;

}
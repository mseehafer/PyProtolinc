
#ifndef C_VALUATION_H
#define C_VALUATION_H


#include <string>
#include <cctype>
#include <algorithm>	
#include <vector>
#include <memory>
#include <unordered_map>

const int VECTOR_LENGTH_YEARS = 120;

typedef struct  {
  int steps_per_year;  // 1 - yearly, 4- quarterly, 12-monthly
  int shifted_age;
} RunParametersTerm;



enum Gender { GenderMale, GenderFemale, GenderUnknown };
const std::string GenderNames[3]  {"Male", "Female", "Unknown"};

const int NUM_PRODS = 3;
enum Product { ProdTerm, ProdEndowment, ProdOther };
const std::string ProductNames[NUM_PRODS]  {"TR", "EW", "UnknownProduct"};



int get_age_at_date(int dob_year, int dob_month, int dob_day, int dt_year, int dt_month, int dt_day);


class CSeriatimRecord {
  private:
    int cession_id;

    Product prod;
    Gender gender;

    int issue_age;

    int issue_year;
    int issue_month;
    int issue_day;
    
    int dob_year;
    int dob_month;
    int dob_day;

    int coverage_years;
    long long sum_insured;

    int portfolio_year;
    int portfolio_month;
    int portfolio_day;
    
    int age_projection_start;

  public:

    int get_cession_id() const {return cession_id;}
    
    std::string get_product() const {return ProductNames[prod];} 
    std::string get_gender() const {return GenderNames[gender];} 
    
    int get_issue_age() const {return issue_age;}
    int get_issue_year() const {return issue_year;}
    int get_issue_month() const {return issue_month;}
    int get_issue_day() const {return issue_day;}

    int get_dob_year() const {return dob_year;}
    int get_dob_month() const {return dob_month;}
    int get_dob_day() const {return dob_day;}

    int get_coverage_years() const {return coverage_years;}
    //long long get_sum_insured() const {return sum_insured;}
    double get_sum_insured() const {return sum_insured;}

    int get_portfolio_year() const {return portfolio_year;}
    int get_portfolio_month() const {return portfolio_month;}
    int get_portfolio_day() const {return portfolio_day;}
    
    int get_age_projection_start() const {return age_projection_start;}

    CSeriatimRecord() {
      // leave other members uninitialized
      this-> prod = ProdOther;
      this -> gender = GenderUnknown;
    }; 
       
    CSeriatimRecord(int cession_id, const std::string &product, int gender,
                   long dob_long, long issue_date_long,
                   int coverage_years, long long sum_insured,
                   long portfolio_date_long) {
      this -> cession_id = cession_id;

      std::string prodUpper = product;
      std::transform(prodUpper.begin(), prodUpper.end(), prodUpper.begin(), ::toupper);

      // start out with unknown product
      this-> prod = ProdOther;
      for(int j=0; j < NUM_PRODS; j++) {
          std::string thisProdUpper = ProductNames[j];
          std::transform(thisProdUpper.begin(), thisProdUpper.end(), thisProdUpper.begin(), ::toupper);

          if (thisProdUpper.compare(prodUpper) == 0) {
            this -> prod = static_cast<Product>(j);
            break;
          }
      }
      this -> gender = static_cast<Gender> (gender < 3 ? gender : 2);
      
      issue_year = (int) (issue_date_long / 10000);
      issue_month = (int) ((issue_date_long % 10000) / 100);
      issue_day = (int) (issue_date_long % 100);

      dob_year = (int) (dob_long / 10000);
      dob_month = (int) ((dob_long % 10000) / 100);
      dob_day = (int) (dob_long % 100);


      issue_age = get_age_at_date(dob_year, dob_month, dob_day,
                                  issue_year, issue_month, issue_day);

      this -> coverage_years = coverage_years;
      this -> sum_insured = sum_insured;

      portfolio_year = (int) (portfolio_date_long / 10000);
      portfolio_month = (int) ((portfolio_date_long % 10000) / 100);
      portfolio_day = (int) (portfolio_date_long % 100);

      age_projection_start =  get_age_at_date(dob_year, dob_month, dob_day,
                                              portfolio_year, portfolio_month, portfolio_day);
    };

    ~CSeriatimRecord() {};

    std::string to_string() const {
      return "CSeriatimRecord: " + std::to_string(issue_age) + 
             ", " + get_product() + ", " + get_gender() +
             ", " + std::to_string(get_issue_year()) + "-" + std::to_string(get_issue_month())+ "-" + std::to_string(get_issue_day());
    }
};


class CPortfolio {
private:

  std::string portfolio_name;  
  std::vector<std::shared_ptr<CSeriatimRecord>> records;

public:
  CPortfolio() {}

  void set_portfolio_name(std::string name) {this->portfolio_name = name;}
  std::string get_portfolio_name(std::string name) {return portfolio_name;}

  std::vector<std::shared_ptr<CSeriatimRecord>>& get_records() {return records;}

  size_t len() {
    return records.size();
  }

  void add(const std::shared_ptr<CSeriatimRecord> &ref) {
    records.push_back(ref);
  }

 void reserve(size_t n) {
    records.reserve(n);
  }

  const std::shared_ptr<CSeriatimRecord> get(int index) {
    return records[index];
  }
};



class CBaseAssumptions {
  protected:
    std::vector<double> mortality_rates;
    std::vector<double> premium_rates;    
    std::vector<double> lapse_rates;
    
  public:

    CBaseAssumptions() {
      for(int i=0; i<VECTOR_LENGTH_YEARS;i++) {
        mortality_rates.push_back(0);
        premium_rates.push_back(0);
        lapse_rates.push_back(0);
      }
    }

    CBaseAssumptions& set_mortality(double *vec) {
      for(int i=0; i<VECTOR_LENGTH_YEARS;i++) {
        mortality_rates[i] = vec[i];
      }
      return *this;
    }

    CBaseAssumptions& set_lapse(double *vec) {
      for(int i=0; i<VECTOR_LENGTH_YEARS;i++) {
        lapse_rates[i] = vec[i];
      }
      return *this;
    }

    CBaseAssumptions& set_premium_rates(double *vec) {
      for(int i=0; i<VECTOR_LENGTH_YEARS;i++) {
        premium_rates[i] = vec[i];
      }
      return *this;
    }

    std::shared_ptr<std::vector<double>> get_mortality_rates(int age, double multiplier, int select_years) const {
      // returns a pointer to a vector with the appropriate rates for the input parameters
      auto ret_value = std::make_shared<std::vector<double> >();
      for(int i=age; i<VECTOR_LENGTH_YEARS;i++) {
        // TODO: account for select years
        (*ret_value).push_back(multiplier * mortality_rates[i]);
      }
      return ret_value;
    }

    std::shared_ptr<std::vector<double>> get_premium_rates(int age, double multiplier, int select_years) const {
      // returns a pointer to a vector with the appropriate rates for the input parameters
      auto ret_value = std::make_shared<std::vector<double> >();
      for(int i=age; i<VECTOR_LENGTH_YEARS;i++) {
        // TODO: account for select years
        (*ret_value).push_back(multiplier * premium_rates[i]);
      }
      return ret_value;
    }

    std::shared_ptr<std::vector<double>> get_lapse_rates(int active_years, double multiplier) const {
      // returns a pointer to a vector with the appropriate rates for the input parameters
      auto ret_value = std::make_shared<std::vector<double> >();
      for(int i=active_years; i<VECTOR_LENGTH_YEARS;i++) {
        // TODO: account for select years
        (*ret_value).push_back(multiplier * lapse_rates[i]);
      }
      return ret_value;
    }

};


void valuation(double* output,
               int no_cols,
               CPortfolio* pf,
               CBaseAssumptions *be_ass,
               CBaseAssumptions *locgaap_ass
              //  std::vector<double> *p_mort_assump_be,
              //  std::vector<double> *p_mort_assump_locgaap,
              //  std::vector<double> *p_lapse_assump_be,
              //  std::vector<double> *p_lapse_assump_locgaap
               );


typedef std::unordered_map<int, std::shared_ptr<std::vector<double>>> AssumptionMap;

void get_simulation_duration(CSeriatimRecord &rec, int (&simul_duration)[2]);




#endif
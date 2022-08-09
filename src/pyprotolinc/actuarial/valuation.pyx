# distutils: language = c++

import cython
from cython.operator cimport dereference
import numpy as np

from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.memory cimport shared_ptr, make_shared, static_pointer_cast

cimport numpy as np
import pandas as pd


# include all required pdx files
# include "crisk_factors.pxd"
# cimport crisk_factors     # these imports seems to miss the Python wrapper
# from crisk_factors cimport CRiskFactors
# from crisk_factors import CRiskFactors

#include "providers.pxd"
#cimport providers
#from providers cimport ConstantRateProvider, StandardRateProvider


include "providers.pxd"   # transitively: include "crisk_factors.pxd"

include "portfolio.pxd"   # transitively: include "crisk_factors.pxd"

# def provider_wrapper(int _len, double val):

#     cdef np.ndarray[double, ndim=1, mode="c"] output = np.zeros(_len)
#     cdef double[::1] output_memview = output

#     cdef CConstantRateProvider const_prov
#     const_prov.set_rate(val)

#     const_prov.get_rates(&output_memview[0], output_memview.shape[0])
#     # const_prov.get_rates(<double*> output.data, _len)
#     return output




# should go into .pxd file?
cdef extern from "c_valuation.h":

    cdef int VECTOR_LENGTH_YEARS

    cdef cppclass CSeriatimRecord:
        CSeriatimRecord() except +
        CSeriatimRecord(int cession_id, string product, int gender,
                        long dob_long, long issue_date_long,
                        int coverage_years, long long sum_insured,
                        long portfolio_date_long) except +

        int get_cession_id()
    
        string get_product()
        string get_gender()
    
        int get_issue_age() const
        int get_issue_year() const
        int get_issue_month() const
        int get_issue_day() const

        int get_dob_year() const
        int get_dob_month() const
        int get_dob_day() const

        int get_coverage_years() const
        # long long get_sum_insured() const
        double get_sum_insured() const

        int get_portfolio_year() const
        int get_portfolio_month() const
        int get_portfolio_day() const
    
        int get_age_projection_start()
  
        string to_string()

 
    cdef cppclass CPortfolio:
        CPortfolio() except +
        size_t len()
        void add(const shared_ptr[CSeriatimRecord] &ref)
        const shared_ptr[CSeriatimRecord] get(int index)
        void reserve(size_t n)
        void set_portfolio_name(string name)
        string get_portfolio_name(string name)


    void valuation(double* output, int no_cols, CPortfolio* pf,
               CBaseAssumptions *be_ass,
               CBaseAssumptions *locgaap_ass
               ) nogil

    cdef cppclass CBaseAssumptions:
        CBaseAssumptions() except +
        
        CBaseAssumptions& set_mortality(double *vec)
        CBaseAssumptions& set_lapse(double *vec) 
        CBaseAssumptions& set_premium_rates(double *vec) 
        
        shared_ptr[vector[double]] get_mortality_rates(int age, double multiplier, int select_years) const
        shared_ptr[vector[double]] get_premium_rates(int age, double multiplier, int select_years) const 
        shared_ptr[vector[double]] get_lapse_rates(int active_years, double multiplier) const 


cdef class SeriatimRecord:
    
    cdef shared_ptr[CSeriatimRecord] rec

    def __cinit__(self, int cession_id, bytes product, bytes gender,
                  size_t dob_date_long, size_t issue_date_long,
                  int coverage_years, long long sum_insured,
                  size_t portfolio_date_long):

        cdef int _gndr

        if gender[0] == 77:    # chr(gender[0]) ==  'M'
            _gndr = 0
        elif gender[0] == 70:  # chr(gender[0]) ==  'F'
            _gndr = 1
        else:
            _gndr = 2
        
        self.rec = make_shared[CSeriatimRecord](cession_id, product, _gndr,
                                   dob_date_long, issue_date_long,
                                   coverage_years, sum_insured,
                                   portfolio_date_long)

    def __repr__(self):
        cdef bytes rpr = self.rec.get()[0].to_string()
        return "Wrapper for " + rpr.decode("UTF8")
    
 
cdef class Portfolio:
    
    # wrap the C++-class
    cdef CPortfolio portfolio
    
    def __cinit__(self):
        pass
    
    def __init__(self, df_portfolio, portfolio_name):
        # list of relevant columns
        cols = ['CESSIONID', 'GENDER', 'ISSUE_AGE', 'ISSUE_DATE_LONG',
                'COVERAGE_YEARS', 'SUM_INSURED', "PORTFOLIO_DATE_LONG", "AGE_INFORCE_DATE"]
        col2 = ['CESSIONID', 'PRODUCTTYPE', 'GENDER', 'DATE_OF_BIRTH_LONG', 'ISSUE_DATE_LONG',
                'COVERAGE_YEARS', 'VOLUME',     'PORTFOLIO_DATE_LONG']
                #  , 'STATUS', , 'VOLUMETYPE',
                #  'DISABLEMENT_DATE_LONG,
                #     'REINPREMPAYPERIOD', 'REINCOVERAGEPERIOD', 'FIRSTINSCOVERAGEPERIOD',
                #     'FIRSTINSPREMPAYPERIOD', 'MAXTOAGEBENEFITPERIOD', 'SMOKERSTATUS',
                #     'OCCUPATIONCLASS', , 'DATE_OF_BIRTH_LONG',
                #     ]

        inp = [df_portfolio[c].values for c in col2]
        self._add_records(*inp)
        self.portfolio.set_portfolio_name(portfolio_name.encode("UTF8"))
        
    @cython.boundscheck(False)
    def _add_records(self, np.ndarray[np.int64_t] cession_ids, 
                     np.ndarray[object] product_types,
                     np.ndarray[object] gender,
                     np.ndarray[np.int64_t] dob_dates_long,
                     np.ndarray[np.int64_t] issue_dates_long,
                     np.ndarray[np.int32_t] coverage_years,
                     np.ndarray[np.int64_t] sums_insured,
                     np.ndarray[np.int64_t] portfolio_dates_long
                     ):
        cdef:
            Py_ssize_t i, n
            np.float64_t foo
        
        n = len(cession_ids)
        self.portfolio.reserve(n)
        
        for i from 0 <= i < n:
            rec = SeriatimRecord(cession_ids[i],
                                 product_types[i].encode("UTF8"), gender[i].encode("UTF8"), 
                                 dob_dates_long[i], issue_dates_long[i],
                                 coverage_years[i], sums_insured[i], 
                                 portfolio_dates_long[i])
            self.portfolio.add(rec.rec)

    def __len__(self):
        return self.portfolio.len()

    def __repr__(self):
        return "Portfolio: ()"

    def get(self, int index):
        """ Get a tuple represenation of the record. """
        cdef CSeriatimRecord rec = dereference(self.portfolio.get(index))

        return (rec.get_issue_age(),
                rec.get_gender().decode("UTF8"),
                rec.get_product().decode("UTF8"),
                rec.get_sum_insured(),
                rec.get_issue_year(),
                rec.get_issue_month(),
                rec.get_issue_day())
    

cdef class BaseAssumptions:
    """ Base mortatlity assumptions class, manages as set of mortality and
        lapse assumptions, always consisting of a pair of best_estimate
        and local_gaap values. """
    
    cdef vector[double] mort_ass_be
    cdef vector[double] mort_ass_locgaap
    
    cdef vector[double] lapse_ass_be
    cdef vector[double] lapse_ass_locgaap

    cdef vector[double] premium_rates_be
    cdef vector[double] premium_rates_locgaap

    cdef CBaseAssumptions base_assumptions_be
    cdef CBaseAssumptions base_assumptions_locgaap

    @cython.boundscheck(False)
    def __init__(self, int start_age_mort,
                 np.ndarray[double, ndim=1, mode="c"] q_be,
                 np.ndarray[double, ndim=1, mode="c"] q_local_gaap,
                 np.ndarray[double, ndim=1, mode="c"] premium_table,                 
                 np.ndarray[double, ndim=1, mode="c"] l_be,
                 np.ndarray[double, ndim=1, mode="c"] l_local_gaap
                 ):

        # extend the mortality vectors to length 120 such that
        # they start at age "0", extend the last value until age 119
        # and fill with first value at the beginning
        cdef size_t length_mort = q_be.shape[0]
        cdef size_t length_lapse = l_be.shape[0]

        cdef np.ndarray[double, ndim=1, mode="c"] tmp_vec = np.zeros(VECTOR_LENGTH_YEARS)

        # mortality tables shall be consistent
        assert length_mort == q_local_gaap.shape[0] and length_mort > 0
        
        # premium table shall have equal length than mortality tables
        assert length_mort == premium_table.shape[0] and length_mort > 0
        
        # length of lapse tables consistent
        assert length_lapse == l_local_gaap.shape[0] and length_lapse > 0
        
        cdef np.ndarray[double, ndim=2, mode="c"] mort_assumptions = np.zeros((VECTOR_LENGTH_YEARS, 2))
        
        mort_assumptions[:start_age_mort, 0] = q_be[0]
        mort_assumptions[start_age_mort:start_age_mort + length_mort, 0] = q_be
        mort_assumptions[start_age_mort + length_mort:, 0] = q_be[length_mort - 1]
        
        mort_assumptions[:start_age_mort, 1] = q_local_gaap[0]
        mort_assumptions[start_age_mort:start_age_mort + length_mort, 1] = q_local_gaap
        mort_assumptions[start_age_mort + length_mort:, 1] = q_local_gaap[length_mort - 1]

        cdef np.ndarray[double, ndim=1, mode="c"] premium_assumptions = np.zeros(VECTOR_LENGTH_YEARS)
        premium_assumptions[:start_age_mort] = premium_table[0]
        premium_assumptions[start_age_mort:start_age_mort + length_mort] = premium_table
        premium_assumptions[start_age_mort + length_mort:] = premium_table[length_mort - 1]
        
        cdef np.ndarray[double, ndim=2, mode="c"] lapse_assumptions = np.zeros((VECTOR_LENGTH_YEARS, 2))
        lapse_assumptions[:length_lapse, 0] = l_be
        lapse_assumptions[:length_lapse, 1] = l_local_gaap

        # set C-level assumptions
        tmp_vec[:] = mort_assumptions[:, 0]
        self.base_assumptions_be.set_mortality(<double*> tmp_vec.data)

        tmp_vec[:] = mort_assumptions[:, 1]
        self.base_assumptions_locgaap.set_mortality(<double*> tmp_vec.data)

        self.base_assumptions_be.set_premium_rates(<double*> premium_assumptions.data)
        self.base_assumptions_locgaap.set_premium_rates(<double*> premium_assumptions.data)

        tmp_vec[:] = lapse_assumptions[:, 0]
        self.base_assumptions_be.set_lapse(<double*> tmp_vec.data)

        tmp_vec[:] = lapse_assumptions[:, 1]
        self.base_assumptions_locgaap.set_lapse(<double*> tmp_vec.data)
        
#        cdef int j
#        for j in range(VECTOR_LENGTH_YEARS):
#            self.mort_ass_be.push_back(mort_assumptions[j, 0])
#            self.mort_ass_locgaap.push_back(mort_assumptions[j, 1])
#            self.lapse_ass_be.push_back(lapse_assumptions[j, 0])
#            self.lapse_ass_locgaap.push_back(lapse_assumptions[j, 1])
#            
#    @cython.boundscheck(False)
#    @cython.wraparound(False)    
#    def get_for_age(self, int age_proj_start):
#        """ Return the assumptions as tuple of numpy ndarrays. """
#        
#        cdef int j
#        cdef np.ndarray[double, ndim=2, mode="c"] mort_assumptions = np.zeros((VECTOR_LENGTH_YEARS - age_proj_start, 2))
#        cdef np.ndarray[double, ndim=2, mode="c"] lapse_assumptions = np.zeros((VECTOR_LENGTH_YEARS - age_proj_start, 2))        
#        
#        for j in range(age_proj_start, VECTOR_LENGTH_YEARS):
#            mort_assumptions[j - age_proj_start, 0] = self.mort_ass_be[j]
#            mort_assumptions[j - age_proj_start, 1] = self.mort_ass_locgaap[j]
#            lapse_assumptions[j - age_proj_start, 0] = self.lapse_ass_be[j - age_proj_start]
#            lapse_assumptions[j - age_proj_start, 1] = self.lapse_ass_locgaap[j - age_proj_start]
#        
#        return (mort_assumptions, lapse_assumptions)
    
    def get_for_age_c(self, int age_proj_start, int policy_age, double multiplier=1.0):
        cdef shared_ptr[vector[double]] tmp_mort = self.base_assumptions_be.get_mortality_rates(age_proj_start, multiplier, 0)
        cdef shared_ptr[vector[double]] tmp_prem = self.base_assumptions_be.get_premium_rates(age_proj_start, multiplier, 0)
        cdef shared_ptr[vector[double]] tmp_lapse = self.base_assumptions_be.get_lapse_rates(policy_age, multiplier)

        cdef vector[double]* p_vec_mort = tmp_mort.get()
        cdef vector[double]* p_vec_prem = tmp_prem.get()
        cdef vector[double]* p_vec_lap = tmp_lapse.get()

        cdef np.ndarray[double, ndim=1, mode="c"] mort_assumptions = np.zeros(VECTOR_LENGTH_YEARS - age_proj_start)
        cdef np.ndarray[double, ndim=1, mode="c"] prem_assumptions = np.zeros(VECTOR_LENGTH_YEARS - age_proj_start)
        cdef np.ndarray[double, ndim=1, mode="c"] lapse_assumptions = np.zeros(VECTOR_LENGTH_YEARS - age_proj_start)

        cdef int j
        for j in range(VECTOR_LENGTH_YEARS - age_proj_start):
            mort_assumptions[j] = p_vec_mort[0][j]
            prem_assumptions[j] = p_vec_prem[0][j]
            lapse_assumptions[j] = p_vec_lap[0][j]
            
        return (mort_assumptions, prem_assumptions, lapse_assumptions)


cdef _portfolio_valuation(double* output, int no_cols, CPortfolio *p_c_pf, CBaseAssumptions *p_be_ass, CBaseAssumptions *p_locgaap_ass):
    """ A valuation run. """

    valuation(output,
              no_cols,
              p_c_pf,
              p_be_ass,
              p_locgaap_ass
              )


def portfolio_valuation(valuation_date, BaseAssumptions base_assump, Portfolio pf):
    """ A valuation run. """
    
    # reserve memory for aggregate the result
    output_columns = ["YEAR", "MONTH", "Premium", "DeathClaims", "LG_Reserve", "SumInsured"]
    # reserve output space for 120 years and 12 months each
    cdef int no_cols = len(output_columns)
    cdef np.ndarray[double, ndim=2, mode="c"] output = np.zeros((VECTOR_LENGTH_YEARS * 12, no_cols))

    # get pointers to C level input objects
    cdef CPortfolio *p_c_pf = &pf.portfolio
    cdef CBaseAssumptions *p_be_ass = &base_assump.base_assumptions_be
    cdef CBaseAssumptions *p_locgaap_ass = &base_assump.base_assumptions_locgaap
 
    _portfolio_valuation(<double*> output.data,
                         no_cols,
                         p_c_pf,
                         p_be_ass,
                         p_locgaap_ass)

    df = pd.DataFrame(data=output,    
                      index=np.arange(1, 1 + output.shape[0]),   
                      columns=output_columns)
    
    df["YEAR"] = df["YEAR"].astype(int)
    df["MONTH"] = df["MONTH"].astype(int) 

    return df

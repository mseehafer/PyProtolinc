
from libc.stdint cimport int64_t, int32_t, int16_t
from cython.operator cimport dereference
from libcpp.memory cimport shared_ptr, make_shared, static_pointer_cast


cdef extern from "portfolio.h":

    cdef cppclass CPolicy:        
        string to_string() const

    
    cdef cppclass CPolicyPortfolio:
        size_t size() const
        const CPolicy &at(size_t j) const
        short _ptf_year, _ptf_month, _ptf_day


    cdef cppclass CPortfolioBuilder:
        CPortfolioBuilder(size_t s)

        CPortfolioBuilder &set_portfolio_date(short ptf_year, short ptf_month, short ptf_day)
        CPortfolioBuilder &set_cession_id(int64_t *ptr_cession_id)
        CPortfolioBuilder &set_date_of_birth(int64_t *ptr_dob)
        CPortfolioBuilder &set_issue_date(int64_t *ptr_issue_date)
        CPortfolioBuilder &set_date_disablement(int64_t *ptr_disablement_date)
        CPortfolioBuilder &set_gender(int32_t *)
        CPortfolioBuilder &set_smoker_status(int32_t *)
        CPortfolioBuilder &set_sum_insured(double *)
        CPortfolioBuilder &set_reserving_rate(double *)
        CPortfolioBuilder &set_initial_state(int16_t *)
        shared_ptr[CPolicyPortfolio] build() except +


cdef class CPortfolioWrapper:
    
    cdef shared_ptr[CPolicyPortfolio] ptf

    cdef _set_ptf(self, shared_ptr[CPolicyPortfolio] ptr_ptf):
        self.ptf = ptr_ptf

    def get_info(self, int k):
        if k >= dereference(self.ptf).size():
            raise Exception("Out of bounds")
        return dereference(self.ptf).at(k).to_string().decode(encoding='ASCII')
    
    def __len__(self):
        return dereference(self.ptf).size()


def build_c_portfolio(py_portfolio):
    """ Takes a Python portfolio and returns a c-Portfolio. """

    # extract size of portfolio and product
    cdef size_t num_policies = len(py_portfolio)

    if not py_portfolio.homogenous_wrt_product:
        raise Exception("All records in portfolio must have the same product.")
    cdef string product = py_portfolio.products.values[0].encode() if num_policies > 0 else b"DUMMY"

    # create the builder object and set the attributes
    cdef shared_ptr[CPortfolioBuilder] cp_builder_ptr = make_shared[CPortfolioBuilder](num_policies, product)
    
    # set portfolio date
    dereference(cp_builder_ptr).set_portfolio_date(py_portfolio.portfolio_date.year,
                                                   py_portfolio.portfolio_date.month,
                                                   py_portfolio.portfolio_date.day)

    # set cession ids
    cdef int64_t[::1] ids_mv = py_portfolio.cession_ids 
    dereference(cp_builder_ptr).set_cession_id(&ids_mv[0])

    # set dates of birth
    cdef np.ndarray[int64_t, ndim=1, mode="c"] dobs = np.zeros(num_policies, dtype=np.int64)
    dobs += py_portfolio.years_of_birth.astype(np.int64) * 10000 + py_portfolio.months_of_birth.astype(np.int64) * 100 + py_portfolio.days_of_birth
    # print("DOBS", dobs)
    cdef int64_t[::1] dobs_mv = dobs
    dereference(cp_builder_ptr).set_date_of_birth(&dobs_mv[0])

    # issue dates
    cdef np.ndarray[int64_t, ndim=1, mode="c"] doi = np.zeros(num_policies, dtype=np.int64)
    doi += py_portfolio.policy_inception_yr.astype(np.int64) * 10000 + py_portfolio.policy_inception_month.astype(np.int64) * 100\
        + py_portfolio.policy_inception_day
    cdef int64_t[::1] doi_mv = doi
    dereference(cp_builder_ptr).set_issue_date(&doi_mv[0])
    
    # date of disablement
    cdef np.ndarray[int64_t, ndim=1, mode="c"] dod = np.zeros(num_policies, dtype=np.int64)
    dod += py_portfolio.disablement_year.astype(np.int64) * 10000 + py_portfolio.disablement_month.astype(np.int64) * 100\
        + py_portfolio.disablement_day
    cdef int64_t[::1] dod_mv = dod
    dereference(cp_builder_ptr).set_date_disablement(&dod_mv[0])

    # gender
    cdef int32_t[::1] gender_mv = py_portfolio.gender
    dereference(cp_builder_ptr).set_gender(&gender_mv[0])

    # smoker status
    cdef int32_t[::1] smoker_mv = py_portfolio.smokerstatus
    dereference(cp_builder_ptr).set_smoker_status(&smoker_mv[0])

    # sum_insured
    cdef double[::1] sum_insured_mv = py_portfolio.sum_insured
    dereference(cp_builder_ptr).set_sum_insured(&sum_insured_mv[0])

    # reserving rate
    cdef double[::1] res_rate_mv = py_portfolio.reserving_rate
    dereference(cp_builder_ptr).set_reserving_rate(&res_rate_mv[0])

    # initial states
    cdef int16_t[::1] initial_states = py_portfolio.initial_states
    dereference(cp_builder_ptr).set_initial_state(&initial_states[0])


    # build and wrap portfolio
    cdef shared_ptr[CPolicyPortfolio] ptf = dereference(cp_builder_ptr).build()
    cdef CPortfolioWrapper cp_wrapper = CPortfolioWrapper()
    cp_wrapper._set_ptf(ptf)

    return cp_wrapper


from multiprocessing import cpu_count
from libcpp.memory cimport shared_ptr, unique_ptr, make_shared, static_pointer_cast


from libcpp cimport bool
from libcpp.string cimport string
from libcpp.vector cimport vector

include "crisk_factors.pxd"
include "portfolio.pxd"


# should go into .pxd file?
cdef extern from "providers.h":


    cdef cppclass CBaseRateProvider:
        void add_risk_factor(CRiskFactors rf) except +
        vector[CRiskFactors] &get_risk_factors() const
        
        double get_rate(vector[int] &indices)  except +
        void get_rates(double *out_array, int length, vector[int *] &indices) except +
        
        string to_string() const

    cdef cppclass CConstantRateProvider(CBaseRateProvider):

        CConstantRateProvider(double)
        CConstantRateProvider()


    cdef cppclass CStandardRateProvider(CBaseRateProvider):
        
        CStandardRateProvider()
        int get_dimension()
        int size()
        void get_values(double *ext_vals)        

        void set_values(vector[int] &shape_vec_in, vector[int] &offsets_in, double *ext_vals) except +
        
        shared_ptr[CStandardRateProvider] slice(vector[int] &indices) except +


cdef class ConstantRateProvider:
    cdef shared_ptr[CConstantRateProvider] c_provider
    cdef vector[int] indexes_dummy
    cdef vector[int *] indexes_dummy2


    # try declaring a C level method
    cdef shared_ptr[CConstantRateProvider] get_provider(self):
        return self.c_provider

    def __cinit__(self, double val=0):
        self.c_provider = make_shared[CConstantRateProvider](val)
    
    def __repr__(self):
        return self.c_provider.get()[0].to_string().decode()

    def get_risk_factors(self):
        cdef vector[CRiskFactors] rfs = self.c_provider.get()[0].get_risk_factors()
        return [CRiskFactors(rf) for rf in rfs]

    def add_risk_factor(self, rf):
        self.c_provider.get()[0].add_risk_factor(rf)

    def get_rate(self, indices=None):
        return self.c_provider.get()[0].get_rate(self.indexes_dummy)

    def get_rates(self, int _len, **kwargs):
        assert _len >= 1, "Required lengh must be >= 1"
        cdef np.ndarray[double, ndim=1, mode="c"] output = np.zeros(_len)
        cdef double[::1] output_memview = output
        self.c_provider.get()[0].get_rates(&output_memview[0], output_memview.shape[0], self.indexes_dummy2)
        return output
    
    def initialize(self, **kwargs):
        pass


cdef class StandardRateProvider:

    cdef shared_ptr[CStandardRateProvider] c_provider
    cdef unsigned int dim

    # try declaring a C level method
    cdef shared_ptr[CStandardRateProvider] get_provider(self):
        return self.c_provider

    def __cinit__(self, rfs, values, np.ndarray[int, ndim=1, mode="c"] offsets):
        cdef vector[int] shapevec
        cdef int k
        cdef int d

        # assert `values` is np.ndarray of type double

        if not (values.ndim == 1 or values.ndim == 2 or values.ndim == 3 or values.ndim == 4):
            raise ValueError("Dimension of data should be 1, 2, 3 or 4.")

        # check that offsets length matches dim!!
        assert offsets.shape[0] == values.ndim, "Number of `offsets` must match dimension of lookup array."

        self.dim = values.ndim
        self.c_provider = make_shared[CStandardRateProvider]()

        for rf in rfs:
            self.c_provider.get()[0].add_risk_factor(CRiskFactors(rf))

        # construct the shape vec
        for k in range(values.ndim):
            d = values.shape[k]
            shapevec.push_back(d)        

        cdef double[::1] values_memview = values.flatten()
        self.c_provider.get()[0].set_values(shapevec, offsets, &values_memview[0])

    def get_risk_factors(self):
        cdef vector[CRiskFactors] rfs = self.c_provider.get()[0].get_risk_factors()
        return [CRiskFactors(rf) for rf in rfs]

    def __repr__(self):
        return self.c_provider.get()[0].to_string().decode(encoding='ASCII')

    def get_rates(self, int _len, **kwargs):
        assert _len >= 1, "Required lengh must be >= 1"

        cdef np.ndarray[double, ndim=1, mode="c"] output = np.zeros(_len)
        cdef double[::1] output_memview = output
        
        cdef vector[int*] indices
        cdef int[:] an_index_vector
        cdef CRiskFactors rf
        
        cdef vector[CRiskFactors] applicable_rfs = self.c_provider.get()[0].get_risk_factors()
        
        # extract the required risk factors from the named arguments and bring them 
        # in the expected order
        kwargs_lv = {k.lower(): v for k, v in kwargs.items()}
        for rf in applicable_rfs:
            pyrf = CRiskFactors(rf)
            an_index_vector = kwargs_lv[pyrf.name.lower()]      # TODO: add test that checks what happens when this lookup fails
            assert len(an_index_vector) == _len, "Lookup indices for {} has unexpected length!".format(pyrf.name)
            indices.push_back(&an_index_vector[0])

        self.c_provider.get()[0].get_rates(&output_memview[0], _len, indices)
        return output

    def get_rate(self, indices):
        cdef vector[int] indexes
        cdef int k
        for k in indices:
            indexes.push_back(k)
        return self.c_provider.get()[0].get_rate(indexes)

    def initialize(self, **kwargs):
        pass

    def slice(self, **kwargs):

        cdef vector[int] indices
        # cdef int an_index
        
        # extract the required risk factors from the named arguments and bring them 
        # in the expected order
        cdef vector[CRiskFactors] applicable_rfs = self.c_provider.get()[0].get_risk_factors()
        # print([q for q in applicable_rfs])

        kwargs_lv = {k.lower(): v for k, v in kwargs.items()}
        for rf in applicable_rfs:
            pyrf = CRiskFactors(rf)
            an_index = kwargs_lv.get(pyrf.name.lower())

            if an_index is not None:
                indices.push_back(int(an_index))
            else:
                indices.push_back(-1)
        
        # print("indices before", [i for i in indices])
        
        cdef shared_ptr[CStandardRateProvider] slicedCSRP = self.c_provider.get()[0].slice(indices) 

        sliced_srp = StandardRateProvider([], np.zeros(1), np.array([0], dtype=np.int32))
        sliced_srp.c_provider = slicedCSRP
        sliced_srp.dim = slicedCSRP.get()[0].get_dimension()
        return sliced_srp
    
    def get_values(self):
        print(self.c_provider.get()[0].size())
        cdef np.ndarray[double, ndim=1, mode="c"] values_placeholder = np.zeros(self.c_provider.get()[0].size())
        print(values_placeholder)
        cdef double[::1] values_memview = values_placeholder
        self.c_provider.get()[0].get_values(&values_memview[0])
        return values_placeholder
        


cdef extern from "assumption_sets.h":

    cdef cppclass CAssumptionSet:
        CAssumptionSet(unsigned dim)
        void set_provider(int row, int col, const shared_ptr[CBaseRateProvider] &prvdr)
        void get_single_rateset(const vector[int] &rf_indexes, double *rates_ext) except +


cdef class AssumptionSet:

    cdef shared_ptr[CAssumptionSet] c_assumption_set
    cdef unsigned int dim

    def __cinit__(self, int _dim):

        self.c_assumption_set = make_shared[CAssumptionSet](_dim)
        self.dim = _dim

    def add_provider_std(self, int r, int c, StandardRateProvider rp):
        cdef shared_ptr[CStandardRateProvider] srp = rp.get_provider()
        cdef shared_ptr[CBaseRateProvider] brp
        # srp = rp.get_provider().get()
        brp = static_pointer_cast[CBaseRateProvider, CStandardRateProvider] (srp)
        # brp = make_shared[CBaseRateProvider](static_cast[CBaseRateProvider, CStandardRateProvider] ())
        # brp = static_cast[CBaseRateProvider, CStandardRateProvider] (srp)
        self.c_assumption_set.get()[0].set_provider(r, c, brp)

    def add_provider_const(self, int r, int c, ConstantRateProvider rp):
        cdef shared_ptr[CConstantRateProvider] srp = rp.get_provider()
        cdef shared_ptr[CBaseRateProvider] brp
        brp = static_pointer_cast[CBaseRateProvider, CConstantRateProvider] (srp)
        self.c_assumption_set.get()[0].set_provider(r, c, brp)
    

    def get_single_rateset(self, risk_factor_values):

        assert len(risk_factor_values) == NUMBER_OF_RISK_FACTORS
        cdef vector[int] rf_indexes

        for rf in risk_factor_values:
            rf_indexes.push_back(rf)

        cdef np.ndarray[double, ndim=1, mode="c"] output = np.zeros(self.dim * self.dim)
        cdef double[::1] output_memview = output
        self.c_assumption_set.get()[0].get_single_rateset(rf_indexes, &output_memview[0])
        return output




# should go into .pxd file?
cdef extern from "time_axis.h":

    cpdef enum class TimeStep(int):
        MONTHLY,
        QUARTERLY,
        YEARLY,
    
    cdef cppclass TimeAxis:
        int get_length() const



cdef extern from "run_config.h":

    cdef cppclass CRunConfig:
         CRunConfig(unsigned dim, TimeStep time_step, int years_to_simulate, int num_cpus, bool use_multicore, shared_ptr[CAssumptionSet] _be_assumptions) except +
         void add_assumption_set(shared_ptr[CAssumptionSet])
         # int get_total_timesteps()
    
    shared_ptr[TimeAxis] make_time_axis(const CRunConfig &run_config, short _ptf_year, short _ptf_month, short _ptf_day)


cdef extern from "run_result.h":

    # this vector provides the headers for the result
    const vector[string] result_names

    cdef cppclass RunResult:
    
        RunResult(const TimeAxis &ta)

        void copy_results(double *ext_result)


cdef extern from "runner.h":

    # void run_c_valuation(const CRunConfig& run_config, shared_ptr[CPolicyPortfolio] ptr_portfolio, double*) nogil except +
    void run_c_valuation(const CRunConfig &run_config, shared_ptr[CPolicyPortfolio] ptr_portfolio, RunResult& run_result) nogil except +



def py_run_c_valuation(AssumptionSet be_ass, CPortfolioWrapper cportfolio_wapper, TimeStep time_step):

    cdef unsigned dim = be_ass.dim
    cdef int num_cpus = cpu_count()
    cdef bool use_multicore = True
    cdef shared_ptr[CAssumptionSet] c_assumption_set = be_ass.c_assumption_set
    cdef int years_to_simulate = 120
    cdef shared_ptr[CRunConfig] crun_config = make_shared[CRunConfig](dim, time_step, years_to_simulate, num_cpus, use_multicore, c_assumption_set)

    output_columns = []
    cdef string cn
    for i in range(result_names.size()):
        cn = result_names[i]  # copy to get rid of the const modifier which is not easy to use in cython for iteration
        output_columns.append(cn.decode())
    
    cdef short _ptf_year = dereference(cportfolio_wapper.ptf)._ptf_year
    cdef short _ptf_month = dereference(cportfolio_wapper.ptf)._ptf_month
    cdef short _ptf_day = dereference(cportfolio_wapper.ptf)._ptf_day
    cdef shared_ptr[TimeAxis] ta_ptr = make_time_axis(dereference(crun_config), _ptf_year, _ptf_month, _ptf_day)
    cdef unique_ptr[RunResult] ptr_run_result = unique_ptr[RunResult](new RunResult(dereference(ta_ptr)))  # make_unique[RunResult](ta)

    # run cpp code
    run_c_valuation(crun_config.get()[0], cportfolio_wapper.ptf, dereference(ptr_run_result))
    
    # copy the result over to numpy array
    cdef int no_cols = len(output_columns)
    cdef int total_timesteps = dereference(ta_ptr).get_length()
    cdef np.ndarray[double, ndim=2, mode="c"] output = np.zeros((total_timesteps, no_cols))
    cdef double[:, ::1] ext_res_view = output
    
    dereference(ptr_run_result).copy_results(&ext_res_view[0, 0])
    
    return output



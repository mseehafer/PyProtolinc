
include "crisk_factors.pxd"

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
        

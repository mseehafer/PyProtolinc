import os

import numpy as np
import pandas as pd

import pyprotolinc
from pyprotolinc.assumptions.providers import StandardRateProvider
from pyprotolinc.riskfactors.risk_factors import Gender, SmokerStatus, Age
from pyprotolinc.assumptions.providers import AssumptionType


class DAV2008T:
    """ Represents the DAV2008T table family for mortality character products
        with risk factors age, gender and smoker status.

        Providers can be obtained for:

          - best estimate ("BE", "2. Ordnung")
          - with safety loadings ("LOADED", "1. Ordnung")

    """
    def __init__(self, base_directory=None):

        if base_directory is None:
            base_directory = os.path.join(pyprotolinc._DEFAULT_TABLES_PATH, "Germany_Endowments_DAV2008T")

        # path to CSV with definitions
        self.base_rates_path = os.path.abspath(os.path.join(base_directory, "Germany_Endowments_DAV2008T.csv"))

        # load and transform base rates
        tab_DAV2008T = pd.read_csv(self.base_rates_path, header=[0, 3, 4])

        # forward fill headers
        filled_headers = [[], [], []]
        for row_count, ind_row in enumerate(tab_DAV2008T.columns):
            for header_ind in range(len(filled_headers)):
                if row_count > 0 and ind_row[header_ind].startswith("Unnamed:"):
                    filled_headers[header_ind].append(filled_headers[header_ind][-1])
                else:
                    filled_headers[header_ind].append(ind_row[header_ind])
        new_headers = pd.MultiIndex.from_arrays(filled_headers, names=('GENDER_IND', 'PRUDENCE_RELATED', "SMOKER_RELATED"))
        tab_DAV2008T.columns = new_headers

        # restrict to the necessary columns
        tab_DAV2008T_transf = tab_DAV2008T[new_headers[list(range(4, 10)) + list(range(14, len(new_headers)))]]

        # remap headers again so that we get the indices correct
        remapped_headers = []

        gender_map = {
            'DAV 2008T R/NR Männer': Gender.M,
            'DAV 2008T R/NR Frauen': Gender.F
        }

        assumption_type_map = {
            'Sterblichkeit 2. Ordnung': AssumptionType.BE,
            'Sterblichkeit 1. Ordnung': AssumptionType.RES,
        }

        smoker_map = {
            'Aggregat': SmokerStatus.A,
            ' Nichtraucher': SmokerStatus.N,
            'Raucher': SmokerStatus.S,
            'Aggregat (Zuschlag 34%)': SmokerStatus.A,
            'Nichtraucher (Zuschlag 45%)': SmokerStatus.N,
            'Raucher (Zuschlag 45%)': SmokerStatus.S
        }

        for col in tab_DAV2008T_transf.columns:
            remapped_headers.append((gender_map[col[0]], assumption_type_map[col[1]], smoker_map[col[2]]))

        tab_DAV2008T_transf.columns = remapped_headers

        # use a 3D array to store the rates with dimensions
        # Age x Gender x Smoker
        self.be_rates = np.zeros((len(tab_DAV2008T), 2, 3))
        self.res_rates = np.zeros((len(tab_DAV2008T), 2, 3))

        for g, at, ss in remapped_headers:
            if at == AssumptionType.BE:
                self.be_rates[:, g, ss] = tab_DAV2008T_transf[(g, at, ss)]
            elif at == AssumptionType.RES:
                self.res_rates[:, g, ss] = tab_DAV2008T_transf[(g, at, ss)]
            else:
                raise Exception("Unknown assumption type")

    def rates_provider(self, estimate_type="BE"):

        estimate_type = estimate_type.upper()

        if estimate_type == "BE":
            return StandardRateProvider(self.be_rates, (Age, Gender, SmokerStatus), offsets=(0, 0, 0))
        elif estimate_type == "LOADED":
            return StandardRateProvider(self.res_rates, (Age, Gender, SmokerStatus), offsets=(0, 0, 0))
        else:
            raise Exception("Unknow estimate type: {}".format(estimate_type))

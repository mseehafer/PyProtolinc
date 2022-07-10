import os

import numpy as np
import pandas as pd

import pyprotolinc
import pyprotolinc.models.risk_factors as risk_factors
from pyprotolinc.assumptions.providers import StandardRatesProvider


class DAV2004R:
    """ Represents the DAV2004R table family for annuities. The table is a generation type family
        with risk factors age, gender and (optionally) the select year.

        Providers can be obtained for:

          - best estimate ("BE", "2. Ordnung")
          - with safety loadings ("LOADED", "1. Ordnung")

    """
    def __init__(self, base_directory=None, trend_t1=10, trend_t2=25):

        if base_directory is None:
            base_directory = os.path.join(pyprotolinc._DEFAULT_TABLES_PATH, "Germany_Annuities_DAV2004R")

        self.base_rates_path = os.path.abspath(os.path.join(base_directory, "Germany_Annuities_DAV2004R.csv"))
        self.select_rates_path = os.path.abspath(os.path.join(base_directory, "Germany_Annuities_DAV2004R_Select.csv"))
        self.trend_rates_path = os.path.abspath(os.path.join(base_directory, "Germany_Annuities_DAV2004R_Trends.csv"))

        self.base_year_trend = 1999
        # trend_t1 and trend_t2 are used for the trend flattening
        self.trend_t1 = trend_t1
        self.trend_t2 = trend_t2

        # load and transform base rates
        tab_DAV2004R_base = pd.read_csv(self.base_rates_path, header=[0, 2, 3], index_col=0)
        df_tmp = tab_DAV2004R_base.unstack()
        df_tmp.index.names = ["TABLE_TYPE", "ESTIMATE_TYPE", "GENDER", "AGE"]
        df_tmp = df_tmp.reset_index().rename({0: "QX"}, axis=1)
        df_tmp.GENDER = df_tmp.GENDER.map({"Männer": risk_factors.Gender.M, "Frauen": risk_factors.Gender.F})
        df_tmp.ESTIMATE_TYPE = df_tmp.ESTIMATE_TYPE.map({'2. Ordnung': "BE", 'Bestand': "?", '1. Ordnung': "LOADED"})
        df_tmp.TABLE_TYPE = df_tmp.TABLE_TYPE.map({'Selektionstafel': "SELECT", 'Aggregattafel': "AGGREGATE"})
        self.df_base_rates = df_tmp   # .copy()

        # extract the ages
        self.ages = np.sort(tab_DAV2004R_base.index.values)

        # load and transform the trends
        tab_DAV2004R_trends = pd.read_csv(self.trend_rates_path, header=[0, 2, 3], index_col=0)
        # forward fill trend headers - there are some gaps which we fill
        filled_headers = [[], [], []]
        for row_count, ind_row in enumerate(tab_DAV2004R_trends.columns):
            for header_ind in range(len(filled_headers)):
                if row_count > 0 and ind_row[header_ind].startswith("Unnamed:"):
                    filled_headers[header_ind].append(filled_headers[header_ind][-1])
                else:
                    filled_headers[header_ind].append(ind_row[header_ind])
        new_headers = pd.MultiIndex.from_arrays(filled_headers, names=tab_DAV2004R_trends.columns.names)
        tab_DAV2004R_trends.columns = new_headers
        # re-group the trend frame
        df_tmp = tab_DAV2004R_trends.unstack()
        df_tmp.index.names = ["LONG/SHORT", "ESTIMATE_TYPE", "GENDER", "AGE"]
        df_tmp = df_tmp.reset_index().rename({0: "F"}, axis=1)
        df_tmp.GENDER = df_tmp.GENDER.map({"Männer": risk_factors.Gender.M, "Frauen": risk_factors.Gender.F})
        df_tmp.ESTIMATE_TYPE = df_tmp.ESTIMATE_TYPE.str.strip().map({'2. Ordnung': "BE", 'Bestand': "?", '1. Ordnung': "LOADED"})
        df_tmp["LONG/SHORT"] = df_tmp["LONG/SHORT"].map({
            'F_1(x)': "F1",
            'F_1(y)': "F1",
            'F_2(x)': "F2",
            'F_2(y)': "F2",
            'F(x)': "F",
            'F(y)': "F"
        })
        self.df_trend_rates = df_tmp   # .copy()

    def rates_provider(self, table_type='AGGREGATE', estimate_type="BE", t_begin=1999, t_end=2150):
        """ A rate provider object is returned.

        Arguments:

        :table_table           Can be either 'AGGREGATE' or 'SELECT' depending on the intended purpose (SELECT is not yet implemented)
        :estimate_type         Can be either 'BE' (best estimate, "2. Ordnung") or 'LOADED' (with loading, "1. Ordnung")

        """

        table_type = table_type.upper()
        estimate_type = estimate_type.upper()

        df_base = self.df_base_rates[(self.df_base_rates.TABLE_TYPE == table_type) &
                                     (self.df_base_rates.ESTIMATE_TYPE == estimate_type)]
        df_base = df_base.set_index(['GENDER', 'AGE'])[["QX"]].unstack("GENDER").droplevel(0, axis=1)

        df_trend = self.df_trend_rates[self.df_trend_rates.ESTIMATE_TYPE == estimate_type]\
                       .set_index(["LONG/SHORT", "ESTIMATE_TYPE", "GENDER", "AGE"])\
                       .unstack("GENDER")\
                       .droplevel(0, axis=1)\
                       .unstack("LONG/SHORT")\
                       .droplevel(0, axis=0)

        table = None

        if estimate_type == "BE":
            table = _calculate_be_tables_with_trend(t_begin, t_end, self.trend_t1, self.trend_t2, df_base, df_trend)
        elif estimate_type == "LOADED":
            table = _calculate_loaded_tables_with_trend(t_begin, t_end, self.trend_t1, self.trend_t2, df_base, df_trend)
        else:
            raise Exception("Unknow estimate type: {}".format(estimate_type))

        if table_type == 'AGGREGATE':
            # base rates and trend for 'AGGREGATE'
            provider = StandardRatesProvider(table,
                                             (risk_factors.CalendarYear, risk_factors.Gender, risk_factors.Age),
                                             offsets=(t_begin, 0, 0))
        elif table_type == 'SELECT':
            raise Exception("Not yet implemented.")

        return provider


def _G(t, T1, T2):
    """ Trend interpolation formula, cf.
        2018-01-24_DAV-Richtlinie_Herleitung_DAV2004R.pdf (online), p. 43
    """
    if t < 1999:
        raise Exception("Table not available for years before 1999")
    elif t <= 1999 + T1:
        return 1
    elif t <= 1999 + T2:
        return 1.0 - ((t - 1999 - T1) * (t - 1999 - T1 - 1)) / (2 * (T2 - T1) * (t - 1999))
    else:
        return (T1 + T2 + 1) / (2 * (t - 1999))


def _calculate_be_tables_with_trend(t_begin, t_end, T1, T2, df_base, df_trend):
    """ Only applicable for BE (not LOADED). Return a three dimensional array containing the mortality
        rates indexed by:

          - age
          - sex (index 0=M, 1=F)
          - calendar year (index 0 corresponds with t_begin)
    """

    # create container for the result
    res_table = np.zeros((1 + t_end - t_begin, 2, df_base.shape[0]), dtype=np.float64)

    # base data males
    qx_male = df_base.values[:, risk_factors.Gender.M]
    F1x_male = df_trend[(risk_factors.Gender.M, "F1")].values
    F2x_male = df_trend[(risk_factors.Gender.M, "F2")].values

    # base data females
    qx_female = df_base.values[:, risk_factors.Gender.F]
    F1x_female = df_trend[(risk_factors.Gender.F, "F1")].values
    F2x_female = df_trend[(risk_factors.Gender.F, "F2")].values

    # trend factors
    for t in range(t_begin, 1 + t_end):
        g = _G(t, T1, T2)
        exponential_arg_male = (F2x_male + g * (F1x_male - F2x_male)) * (t - 1999)
        exponential_arg_female = (F2x_female + g * (F1x_female - F2x_female)) * (t - 1999)
        res_table[t - t_begin, 0, :] = qx_male * np.exp(-exponential_arg_male)
        res_table[t - t_begin, 1, :] = qx_female * np.exp(-exponential_arg_female)

    return res_table


def _calculate_loaded_tables_with_trend(t_begin, t_end, T1, T2, df_base, df_trend):
    """ Only applicable for LOADED (not BE)). Return a three dimensional array containing the mortality
        rates indexed by:

          - age
          - sex (index 0=M, 1=F)
          - calendar year (index 0 corresponds with t_begin)
    """

    # create container for the result
    res_table = np.zeros((1 + t_end - t_begin, 2, df_base.shape[0]), dtype=np.float64)

    # base data males
    qx_male = df_base.values[:, risk_factors.Gender.M]
    Fx_male = df_trend[(risk_factors.Gender.M, "F")].values

    # base data females
    qx_female = df_base.values[:, risk_factors.Gender.F]
    Fx_female = df_trend[(risk_factors.Gender.F, "F")].values

    # trend factors
    for t in range(t_begin, 1 + t_end):
        exponential_arg_male = Fx_male * (t - 1999)
        exponential_arg_female = Fx_female * (t - 1999)
        res_table[t - t_begin, 0, :] = qx_male * np.exp(-exponential_arg_male)
        res_table[t - t_begin, 1, :] = qx_female * np.exp(-exponential_arg_female)

    return res_table


class B20RatesProvider(StandardRatesProvider):

    def __init__(self, values, other_risk_factors, offsets=None, shifts_table=None, select_matrix=None):
        assert shifts_table is not None, "No shifts table provided for the B20RatesProvider."
        assert select_matrix is not None, "No select factors table provided for the B20RatesProvider."

        super().__init__(values, other_risk_factors, offsets)
        self.shifts_table = shifts_table
        self.select_matrix = select_matrix
        self.is_initialized = False

    def initialize(self, **kwargs):
        self.years_of_birth = kwargs["years_of_birth"]
        self.gender = kwargs["gender"]

        self.applicable_shifts = self.shifts_table[self.years_of_birth - 1900, self.gender].astype(np.int16)

        self.is_initialized = True

    def get_rates(self, length=None, **kwargs):

        assert self.is_initialized, "B20RatesProvider must be initialized before getting rates."
        # adjust the ages, make sure they don't become negative
        kwargs["age"] = np.maximum(kwargs["age"] + self.applicable_shifts, 0)

        gender = kwargs["gender"]
        yearsdisabledifdisabledatstart = kwargs["yearsdisabledifdisabledatstart"]

        # identify the rows where a select factor applies: should be only those with 0 <= yearsdisabledifdisabledatstart <= 4
        tmp = np.logical_or(np.isnan(yearsdisabledifdisabledatstart), np.nan_to_num(yearsdisabledifdisabledatstart, 0) > 4)
        tmp = np.logical_or(tmp, np.nan_to_num(yearsdisabledifdisabledatstart, 0) < 0)
        relevant_indexes = np.logical_not(tmp)

        ydads_relevant_rows = yearsdisabledifdisabledatstart[relevant_indexes].astype(np.int16)

        # the select factor consists of "1"s except in the "relevant rows"
        # where it is overwritten
        select_factor = np.ones(len(yearsdisabledifdisabledatstart))
        select_factor[relevant_indexes] = self.select_matrix[ydads_relevant_rows, gender[relevant_indexes]]

        # print("yearsdisabledifdisabledatstart ", yearsdisabledifdisabledatstart )
        # print("select_factor", select_factor)

        # lookup using adjusted ages
        return select_factor * super().get_rates(length, **kwargs)


class DAV2004R_B20:
    """ Represents the DAV2004R_B20 table family for annuities. The table is a
        base table with age shifts determined by the year of birth.
        Providers can be obtained for:

          - best estimate ("BE", "B20")
          - with safety loadings ("LOADED", "1. Ordnung")
          - inforce ("IF", "Bestand")

    """
    def __init__(self, base_directory):

        b20base_rates_path = os.path.join(base_directory, "Germany_Annuities_DAV2004R_AVBase.csv")
        av_shifts_path = os.path.join(base_directory, "Germany_Annuities_DAV2004R_AV.csv")
        selects_path = os.path.join(base_directory, "Germany_Annuities_DAV2004R_Select.csv")

        self.df_base_rates = pd.read_csv(b20base_rates_path, header=[0, 1], index_col=0, skiprows=1)
        self.df_shifts = pd.read_csv(av_shifts_path)
        self.df_select_factors = pd.read_csv(selects_path, index_col=0, skiprows=1)

    def rates_provider(self, estimate_type="BE"):

        if estimate_type == "BE" or estimate_type == "B20":
            av_type = "B20"
        elif estimate_type == "IF" or estimate_type == "Bestand":
            av_type = "Bestand"
        elif estimate_type == "LOADED" or estimate_type == "1. Ordnung":
            av_type = "1. Ordnung"
        else:
            raise Exception("Unknown estimate type for DAV2004R_B20: {}".format(estimate_type))

        base_rates = np.zeros((len(self.df_base_rates), 2))
        base_rates[:,  risk_factors.Gender.M] = self.df_base_rates[(av_type, "Männer")].values
        base_rates[:,  risk_factors.Gender.F] = self.df_base_rates[(av_type,  "Frauen")].values

        shifts = np.zeros((len(self.df_shifts), 2), dtype=np.int16)
        shifts[:, risk_factors.Gender.M] = self.df_shifts["Männer " + av_type].values
        shifts[:, risk_factors.Gender.F] = self.df_shifts["Frauen " + av_type].values

        select_matrix = np.zeros((len(self.df_select_factors), 2))
        select_matrix[:, risk_factors.Gender.M] = self.df_select_factors["Männer"]
        select_matrix[:, risk_factors.Gender.F] = self.df_select_factors["Frauen"]

        provider = B20RatesProvider(base_rates,
                                    (risk_factors.Age, risk_factors.Gender),   # NOte: This one is applicable but not in the list risk_factors.YearsDisabledIfDisabledAtStart),
                                    shifts_table=shifts, select_matrix=select_matrix)
        return provider

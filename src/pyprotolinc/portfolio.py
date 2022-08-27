import os
import datetime
import logging
import hashlib
import pickle

import numpy as np
import pandas as pd

# from pyprotolinc.models.model_disability_multistate import MultiStateDisabilityStates
from pyprotolinc.models.risk_factors import Gender, SmokerStatus


logger = logging.getLogger(__name__)


class Portfolio:

    def __len__(self):
        return self.num_of_records

    def __init__(self, portfolio_path, states_model, df_portfolio=None):

        if df_portfolio is None:
            logger.info("Reading portfolio data from file {}.".format(portfolio_path))
            df_portfolio = pd.read_excel(portfolio_path)
            df_portfolio.columns = [c.upper() for c in df_portfolio.columns]
        else:
            logger.debug("Initializing portfolio from dataframe")

        self._init_from_dataframe(df_portfolio, states_model)

    def _init_from_dataframe(self, df_portfolio, states_model):
        # store a copy of the dataframe
        self.df_portfolio = df_portfolio.copy()
        self.states_model = states_model

        self.num_of_records = len(df_portfolio)
        self.cession_ids = self.df_portfolio["ID"].values.astype(np.int64)

        # product features, currently kept as pd.Series
        self.products = self.df_portfolio["PRODUCT"].str.upper()
        self.product_params = self.df_portfolio["PRODUCT_PARAMETERS"]

        # a flag that signals that all rows have the same product
        self.homogenous_wrt_product = len(self.products.unique()) == 1

        # extract the portfolio date
        _portfolio_date_array = df_portfolio["DATE_PORTFOLIO"].unique()
        assert len(_portfolio_date_array) == 1, "More than one portfolio date"
        self.portfolio_date = pd.Timestamp(_portfolio_date_array[0]).to_pydatetime()

        # extract and validate the sex, map to enum coding
        self.gender = df_portfolio["SEX"].str.upper()
        assert set(self.gender.unique()).issubset({g.name for g in Gender})
        self.gender = self.gender.map({g.name: int(g) for g in Gender}).values.astype(np.int32)

        # extract age vector at the portfolio date
        self.initial_ages = completed_months_to_date(df_portfolio["DATE_OF_BIRTH"], self.portfolio_date).astype(np.int32)
        self.years_of_birth = self.df_portfolio["DATE_OF_BIRTH"].dt.year.values.astype(np.int16)
        self.months_of_birth = self.df_portfolio["DATE_OF_BIRTH"].dt.month.values.astype(np.int16)
        self.days_of_birth = self.df_portfolio["DATE_OF_BIRTH"].dt.day.values.astype(np.int16)

        self.policy_inception_yr = df_portfolio["DATE_START_OF_COVER"].dt.year.values.astype(np.int16)
        self.policy_inception_month = df_portfolio["DATE_START_OF_COVER"].dt.month.values.astype(np.int16)
        self.policy_inception_day = df_portfolio["DATE_START_OF_COVER"].dt.day.values.astype(np.int16)

        # extract and map the MultiStateDisabilityStates
        _unknown_status = set(df_portfolio["CURRENT_STATUS"]) - {s.name for s in states_model}
        assert len(_unknown_status) == 0, "Unknow status " + str(_unknown_status)
        self.initial_states = df_portfolio["CURRENT_STATUS"].map({st.name: st for st in states_model}).values.astype(np.int16)

        # extract the sums insured
        self.sum_insured = df_portfolio["SUM_INSURED"].values.astype(np.float64)

        # extract the reserving rate
        self.reserving_rate = df_portfolio["RESERVING_RATE"].values.astype(np.float64)

        # extract the smoker status
        self.smokerstatus = df_portfolio["SMOKERSTATUS"].str.upper()
        _unknown_smoker_status = set(self.smokerstatus) - {s.name for s in SmokerStatus}
        assert len(_unknown_smoker_status) == 0,\
            "Unknow smoker status: " + str(_unknown_smoker_status) + ", use one of " + str({s.name for s in SmokerStatus})
        self.smokerstatus = self.smokerstatus.map(SmokerStatus.index_mapper()).values.astype(np.int32)

        # the number of month since the disablement date, is NaN if no disablement date is given
        self.disablement_year = df_portfolio["DATE_OF_DISABLEMENT"].dt.year.values.astype(np.int16)
        self.disablement_month = df_portfolio["DATE_OF_DISABLEMENT"].dt.month.values.astype(np.int16)
        self.disablement_day = df_portfolio["DATE_OF_DISABLEMENT"].dt.day.values.astype(np.int16)

        self.months_disabled_at_start = completed_months_to_date(df_portfolio["DATE_OF_DISABLEMENT"], self.portfolio_date).astype(np.int)

        # check that when in disabled state at start then the disablement date must be at or before the portfolio_date
        disabled_according_to_date = df_portfolio.CURRENT_STATUS.str[:3] == "DIS"
        sel1 = df_portfolio.DATE_OF_DISABLEMENT[disabled_according_to_date] > df_portfolio["DATE_PORTFOLIO"][disabled_according_to_date]
        assert len(df_portfolio[disabled_according_to_date][sel1]) == 0,\
            "WHEN in state DISABLED the DATE_OF_DISABLEMENT must be less or equal to the DATE_PORTFOLIO"

        # check if the ages are homogenous w.r.t. a months
        month_groups = np.unique(self.initial_ages % 12)
        self.common_month = month_groups[0] if len(month_groups) == 1 else None

    def split_by_product_and_month_in_year(self, chunk_size):
        """ Return a list of sub-portfolios which are homgeneous w.r.t.
            to the ages in months modulo 12. """

        # container for the groups
        subportfolios_ages_maximized = list()

        # split by product
        for prod, df_prod_split in self.df_portfolio.groupby("PRODUCT"):

            logger.debug("Splitting portfolio for product %s.", str(prod).upper())

            # split further into groups homogenous w.r.t. the "birth month"
            ages_groups = completed_months_to_date(df_prod_split["DATE_OF_BIRTH"], self.portfolio_date) % 12
            month_groups = np.unique(ages_groups)

            # generate the age group splits and split them to max size
            subframes_ages = [df_prod_split[ages_groups == k] for k in month_groups]
            for df_subportfolio in subframes_ages:
                subportfolios_ages_maximized.extend(split_to_size(df_subportfolio, chunk_size))

        return [Portfolio(None, states_model=self.states_model, df_portfolio=df_sb_ptf) for df_sb_ptf in subportfolios_ages_maximized]


def split_to_size(df_portfolio, max_size):
    """ Split a dataframe into subsets with a maximum size. """

    splits = []
    # select first n rows using iloc
    remaining_length = len(df_portfolio)
    while remaining_length > max_size:
        splits.append(df_portfolio.iloc[:max_size, :])
        df_portfolio = df_portfolio.iloc[max_size:, :]
        remaining_length -= max_size

    if remaining_length > 0:
        splits.append(df_portfolio)

    return splits


def completed_months_to_date(date_col, the_date):
    """ Calculate completed months between the date col and `the_date`.
        The latter one can be a np.datetime series or a datetime.datetime. """
    class _dt:
        """ Helper class. """
        def __init__(self, year, month, day):
            self.year = year
            self.month = month
            self.day = day

    class _date_emul:
        """ Helper class. """
        def __init__(self, the_date):
            self.dt = _dt(the_date.year, the_date.month, the_date.day)

    if isinstance(the_date, datetime.datetime):
        the_date = _date_emul(the_date)

    # calculate the age in months at the portfolio_date
    age_in_months0 = \
        the_date.dt.year * 12 + the_date.dt.month \
        - date_col.dt.year * 12 - date_col.dt.month \
        - 1 \
        + (the_date.dt.day >= date_col.dt.day).astype(int)
    return age_in_months0.values


class PortfolioLoader:

    def __init__(self, run_config):
        self.run_config = run_config
        self.portfolio = None
        # self.raw_transition_assumptions = None

    def load(self, states_model):

        portfolio_abs_path = os.path.abspath(self.run_config.portfolio_path)
        if not os.path.exists(portfolio_abs_path):
            raise Exception("No such file: {}".format(portfolio_abs_path))
        file_cand = self._get_portfolio_hash(portfolio_abs_path, states_model)
        portfolio = self._load_from_cache(file_cand)
        if portfolio is not None:
            self.portfolio = portfolio
        else:
            # create portfolio object
            self.portfolio = Portfolio(portfolio_abs_path, states_model)
            self._save_in_cache(file_cand, self.portfolio)

        logger.info("Portolio rows: {}".format(len(self.portfolio)))
        # # read the raw assumptions
        # self.raw_transition_assumptions = read_assumptions(self.run_config.assumptions_path)
        return self.portfolio

    def _get_portfolio_hash(self, portfolio_abs_path, states_model):
        """ Build a hash from the file name, the modification time and the states_model
            it was used with. """
        md5 = hashlib.md5()
        md5.update(portfolio_abs_path.encode('utf-8'))
        modification_time = os.path.getmtime(portfolio_abs_path)
        md5.update(str(modification_time).encode('utf-8'))
        md5.update(pickle.dumps(states_model))
        return "portfolio_dump_{}".format(md5.hexdigest())

    def _load_from_cache(self, file_cand):
        file_cand_path = os.path.abspath(os.path.join(self.run_config.portfolio_cache, file_cand))

        portfolio = None
        try:
            with open(file_cand_path, 'rb') as dump_file:
                portfolio = pickle.load(dump_file)
                logger.info("Porfolio loaded from cache")
        except FileNotFoundError:
            logger.debug("Porfolio file not found in cache.")
        return portfolio

    def _save_in_cache(self, file_cand, portolio_obj):
        file_cand_path = os.path.abspath(os.path.join(self.run_config.portfolio_cache, file_cand))
        # create the directory if it does not yet exist
        portfolio_cache_path = os.path.abspath(self.run_config.portfolio_cache)
        if not os.path.exists(portfolio_cache_path):
            logger.info("Created directory for portfolio cache %s", portfolio_cache_path)
            os.makedirs(portfolio_cache_path)
        try:
            with open(file_cand_path, 'wb') as dump_file:
                pickle.dump(portolio_obj, dump_file)
                logger.info("Porfolio saved in cache")
        except FileNotFoundError:
            logger.warn("Caching the portfolio failed.")

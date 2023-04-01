
import logging
from abc import ABC
from typing import Iterable, Optional

import numpy as np
import numpy.typing as npt
import pandas as pd

from pyprotolinc.models.state_models import MortalityStates, AnnuityRunoffStates, MultiStateDisabilityStates, AbstractStateModel
from pyprotolinc.results import CfNames
from pyprotolinc.portfolio import Portfolio
from pyprotolinc.utils import TimeAxis


logger = logging.getLogger(__name__)


def calc_terminal_months(df_portfolio: pd.DataFrame) -> tuple[npt.NDArray[np.int32], npt.NDArray[np.int32]]:
    """ Calculate the final month of the policy given a term in years as input.
        The method shortens policy durations when they started not on the
        first of a month. """

    # cast to int in next statement to force an error if that fails
    duration_in_months = np.array(df_portfolio.PRODUCT_PARAMETERS, dtype=np.int32) * 12
    start_years: npt.NDArray[np.int32] = np.array(df_portfolio.DATE_START_OF_COVER.dt.year.values, dtype=np.int32)
    start_months: npt.NDArray[np.int32] = np.array(df_portfolio.DATE_START_OF_COVER.dt.month.values, dtype=np.int32)

    # "absolute number of completed months" at start of policy is start_years * 12 + (start_months - 1)
    end_abs = start_years * 12 + (start_months - 1)
    # adding the duration in months we get the "absolute number of completed months" after the term has ended
    end_abs += duration_in_months

    # converting back to year and month and adjusting if "0" months are needed
    year_last_month, last_month = end_abs // 12, end_abs % 12
    year_last_month[last_month == 0] -= 1
    last_month[last_month == 0] = 12

    return year_last_month, last_month


def calc_term_end_indicator(time_axis: TimeAxis,
                            year_last_month: npt.NDArray[np.int32],
                            last_month: npt.NDArray[np.int32]) -> npt.NDArray[np.int16]:
    """ Calculate a binary matrix with
        - rows corresponing to insureds
        - columns corresponding to time
        such that the entry is "1" for all times before the
        policy matures. The input is given by a time-axis object and two numpy arrays
        which are indexed by insured and together represent the last month/year
        at which the policy ist still in-force. """
    # ta_abs = time_axis.years * 12 + time_axis.months - 1
    # ta_abs = ta_abs.reshape((ta_abs.shape[0], 1))
    # end_mont_abs = (year_last_month * 12 + last_month - 1).reshape((1, len(year_last_month)))
    # return (ta_abs <= end_mont_abs).astype(np.int16).transpose()
    ta_abs = time_axis.years * 12 + time_axis.months - 1
    ta_abs = ta_abs.reshape((1, ta_abs.shape[0]))
    end_mont_abs = (year_last_month * 12 + last_month - 1).reshape((len(year_last_month), 1))
    return (ta_abs <= end_mont_abs).astype(np.int16)


def calc_term_start_indicator(time_axis: TimeAxis,
                              inception_yr: npt.NDArray[np.int16],
                              inception_month: npt.NDArray[np.int16]) -> npt.NDArray[np.int16]:
    """ Calculate a binary matrix with
        - rows corresponing to insureds
        - columns corresponding to time
        such that the entry is "1" for all times after the policy term begins.
        The input is given by a time-axis object and two numpy arrays
        which are indexed by insured and together represent the last month/year
        at which the policy ist still in-force. """
    # ta_abs = time_axis.years * 12 + time_axis.months - 1
    # ta_abs = ta_abs.reshape((ta_abs.shape[0], 1))
    # start_month_abs = (inception_yr * 12 + inception_month - 1).reshape((1, len(inception_yr)))
    # return (ta_abs >= start_month_abs).astype(np.int16).transpose()
    ta_abs = time_axis.years * 12 + time_axis.months - 1
    ta_abs = ta_abs.reshape((1, ta_abs.shape[0]))
    start_month_abs = (inception_yr * 12 + inception_month - 1).reshape((len(inception_yr), 1))
    return (ta_abs >= start_month_abs).astype(np.int16)


def calc_maturity_transition_indicator(time_axis: TimeAxis,
                                       year_last_month: npt.NDArray[np.int32],
                                       last_month: npt.NDArray[np.int32]) -> npt.NDArray[np.int32]:
    """ Calculate a binary matrix with
        - rows corresponing to insureds
        - columns corresponding to time
        such that the entry is "1" only in the last month of the policy lifetime.
    """
    ta_abs = time_axis.years * 12 + time_axis.months - 1
    end_mont_abs = (year_last_month * 12 + last_month - 1).reshape((1, len(year_last_month)))
    multiplier_term: npt.NDArray[np.int32] = (ta_abs.reshape((ta_abs.shape[0], 1)) == end_mont_abs).astype(np.int32)
    return multiplier_term.transpose()


###################################################
# Abstract Product and registering
###################################################

class AbstractProduct(ABC):
    """ Abstract base class of the various prodduts. """

    STATES_MODEL = AbstractStateModel
    PRODUCT_NAMES: Optional[Iterable[str]] = None

    def __init__(self, portfolio: Portfolio) -> None:
        self.portfolio = portfolio
        self.length = len(self.portfolio)

        # monthly sum insured (=annuity per year) as an (n, 1)-array
        self.sum_insured_per_month = self.portfolio.sum_insured[:, None] / 12.0

    def get_bom_payments(self, time_axis: TimeAxis) -> dict[AbstractStateModel,
                                                            list[tuple[CfNames, npt.NDArray[np.float64]]]]:
        """ Return the 'conditional payments', i.e. those payments that are due if an
            insured is in the corresponding state at the given time. """
        return {}

    def get_state_transition_payments(self, time_axis: TimeAxis) -> dict[tuple[AbstractStateModel,
                                                                               AbstractStateModel],
                                                                         list[tuple[CfNames,
                                                                                    npt.NDArray[np.float64]]]]:
        """ This method returns a datastructure which encodes
           which state stransitions trigger which payments

            Returns: Dictionary mapping StateTransitions parametrized by tuples of the State-Enum
            to a binary matrix of the structure "insured x time".
        """
        return dict()

    def contractual_state_transitions(self, time_axis: TimeAxis) -> Iterable[tuple[AbstractStateModel,
                                                                                   AbstractStateModel,
                                                                                   npt.NDArray[np.int32]]]:
        """ This method returns a datastructure which encodes
            when and for which records contractual state transitions
            are due.

            Returns: Iterable consisting of three-tuples where
              - first member = from-state
              - sencond member = to-state
              - third member is a binary matrix of the structure "insured x time"
                where a "1" represents a contractual move.
        """
        return ()


# a global variable with the mapping "ProductName" -> ProductClass
# and two functions providing the interface to the global variable
_PRODUCT_NAME2CLASS: dict[str, type[AbstractProduct]] = dict()


def _register_product(product_name: str, product_class: type[AbstractProduct]) -> None:
    """ Add a product lookup. """

    # check that the name is not is use already
    # assert product_name.upper() not in _PRODUCT_NAME2CLASS, "ProductName already in use"
    # print("Registering", product_name, product_class.__name__)
    if product_name.upper() in _PRODUCT_NAME2CLASS:
        logger.warn(f"ProductName already in use: {product_name}")

    _PRODUCT_NAME2CLASS[product_name.upper()] = product_class


def product_class_lookup(product_name: str) -> type[AbstractProduct]:
    prdct = _PRODUCT_NAME2CLASS.get(product_name.upper())
    if prdct is None:
        raise Exception(f"Unknown Product: {product_name}")
    else:
        return prdct


def register(cls: type[AbstractProduct]) -> type[AbstractProduct]:
    """ Annotation that will register the product. """
    classname = cls.__name__
    if cls.__name__ != "AbstractProduct":
        if cls.PRODUCT_NAMES:
            # allow that the PRODUCT_NAMES field is a string or an iterable
            if isinstance(cls.PRODUCT_NAMES, str):
                _register_product(cls.PRODUCT_NAMES, cls)
            else:
                for prod_name in cls.PRODUCT_NAMES:
                    _register_product(prod_name, cls)
        else:
            _register_product(classname, cls)
    return cls


def show_products() -> list[tuple[str, type[AbstractProduct], Optional[str]]]:
    """ Return a list containing all registered product. The list items
        are tuples constiting of the product name, the class and the doc-string. """
    return [(prod_name, prod_class, prod_class.__doc__) for prod_name, prod_class in _PRODUCT_NAME2CLASS.items()]


###################################################
# Built-in Product definitions
###################################################

@register
class Product_AnnuityInPayment(AbstractProduct):
    """ Simple product that pays out the sum_insured / 12 each month. """

    STATES_MODEL = AnnuityRunoffStates
    PRODUCT_NAMES = ("AnnuityInPayment", )

    def __init__(self, portfolio: Portfolio) -> None:
        super().__init__(portfolio)
        # self.portfolio = portfolio
        # self.length = len(self.portfolio)

        # # monthly sum insured (=annuity per year) as an (n, 1)-array
        # self.sum_insured_per_month = self.portfolio.sum_insured[:, None] / 12.0

    def get_bom_payments(self, time_axis: TimeAxis) -> dict[AbstractStateModel,
                                                            list[tuple[CfNames, npt.NDArray[np.float64]]]]:
        """ Return the 'conditional payments', i.e. those payments that are due if an
            insured is in the corresponding state at the given time. """
        return {
            self.STATES_MODEL.DIS1: [
                (CfNames.ANNUITY_PAYMENT1, -np.dot(self.sum_insured_per_month,
                                                   np.ones((1, len(time_axis))))
                 )
            ]
        }


@register
class Product_AnnuityInPaymentYearlyAtBirthMonth(AbstractProduct):
    """ Simple product that pays out the sum_insured each year at the
        month of birth. """

    STATES_MODEL = AnnuityRunoffStates
    PRODUCT_NAMES = ("AnnuityInPaymentYearlyAtBirthMonth", )

    def __init__(self, portfolio: Portfolio) -> None:
        super().__init__(portfolio)
        # self.portfolio = portfolio
        # self.length = len(self.portfolio)

        # # monthly sum insured (=annuity per year) as an (n, 1)-array
        # self.sum_insured_per_month = self.portfolio.sum_insured[:, None] / 12.0
        self.months_of_birth = self.portfolio.months_of_birth

    def get_bom_payments(self, time_axis: TimeAxis) -> dict[AbstractStateModel,
                                                            list[tuple[CfNames, npt.NDArray[np.float64]]]]:
        """ Return the 'conditional payments', i.e. those payments that are due if an
            insured is in the corresponding state at the given time. """

        # comparison with broadcasting
        birth_month_indicator = np.dot(np.ones((len(self.portfolio), 1)), time_axis.months.reshape((1, len(time_axis))))\
            == self.portfolio.months_of_birth.reshape((len(self.portfolio), 1))

        birth_month_indicator = birth_month_indicator.astype(int)

        return {
            self.STATES_MODEL.DIS1: [
                (CfNames.ANNUITY_PAYMENT1, -birth_month_indicator * self.sum_insured_per_month * 12)
            ]
        }

    # def get_state_transition_payments(self, time_axis):
    #     # no lump sum payments in this product
    #     return dict()

    # def contractual_state_transitions(self, time_axis):
    #     return ()


@register
class Product_TwoStateDisability(AbstractProduct):
    """ Income protection product with two disabled states. """

    STATES_MODEL = MultiStateDisabilityStates
    PRODUCT_NAMES = ("TwoStateDisability", )

    def __init__(self, portfolio: Portfolio) -> None:
        super().__init__(portfolio)
        # self.portfolio = portfolio
        # self.length = len(self.portfolio)

        # # monthly sum insured (=annuity per year) as an (n,1)-array
        # self.sum_insured_per_month = self.portfolio.sum_insured[:, None] / 12.0

    def get_bom_payments(self, time_axis: TimeAxis) -> dict[AbstractStateModel,
                                                            list[tuple[CfNames, npt.NDArray[np.float64]]]]:
        """ Return the 'conditional payments', i.e. those payments that are due if an
            insured is in the corresponding state at the given time. """
        return {

            # simplification for the premium: should be either an input from the portfolio file
            # or calculated using a premium table
            self.STATES_MODEL.ACTIVE: [
                (CfNames.PREMIUM, 0.1 * np.dot(self.sum_insured_per_month,
                                               np.ones((1, len(time_axis))))
                 )
            ],

            self.STATES_MODEL.DIS1: [
                (CfNames.ANNUITY_PAYMENT1, -np.dot(self.sum_insured_per_month,
                                                   np.ones((1, len(time_axis))))
                 )
            ],

            self.STATES_MODEL.DIS2: [
                (CfNames.ANNUITY_PAYMENT2, -2 * np.dot(self.sum_insured_per_month,
                                                       np.ones((1, len(time_axis))))
                 )
            ]
        }

    # def get_state_transition_payments(self, time_axis):
    #     # no lump sum payments in this case
    #     return dict()

    # def contractual_state_transitions(self, time_axis):
    #     return ()


@register
class Product_MortalityTerm(AbstractProduct):
    """ Simple product that pays out on death."""

    STATES_MODEL = MortalityStates
    PRODUCT_NAMES = ("TERM", "MortalityTerm")

    def __init__(self, portfolio: Portfolio) -> None:
        super().__init__(portfolio)
        # self.portfolio = portfolio
        # self.length = len(self.portfolio)

        # # monthly sum insured (=annuity per year) as an (n, 1)-array
        # self.sum_insured_per_month = self.portfolio.sum_insured[:, None] / 12.0

        self.year_last_month, self.last_month = calc_terminal_months(self.portfolio.df_portfolio)

    def get_bom_payments(self, time_axis: TimeAxis) -> dict[AbstractStateModel,
                                                            list[tuple[CfNames, npt.NDArray[np.float64]]]]:
        """ Return the 'conditional payments', i.e. those payments that are due if an
            insured is in the corresponding state at the given time. """

        multiplier_term_end = calc_term_end_indicator(time_axis,
                                                      self.year_last_month,
                                                      self.last_month)
        multiplier_term_start = calc_term_start_indicator(time_axis,
                                                          self.portfolio.policy_inception_yr,
                                                          self.portfolio.policy_inception_month)
        multiplier_term = multiplier_term_end * multiplier_term_start

        # print(multiplier_term_end.flags['C_CONTIGUOUS'],
        #       multiplier_term_start.flags['C_CONTIGUOUS'],
        #       multiplier_term.flags['C_CONTIGUOUS'])

        return {
            self.STATES_MODEL.ACTIVE: [
                (CfNames.PREMIUM,
                 0.0005 * multiplier_term * self.sum_insured_per_month * 12.0
                 )
            ]
        }

    def get_state_transition_payments(self, time_axis: TimeAxis) -> dict[tuple[AbstractStateModel,
                                                                               AbstractStateModel],
                                                                         list[tuple[CfNames,
                                                                                    npt.NDArray[np.float64]]]]:
        # a flat mortality benefit in this product

        multiplier_term_end = calc_term_end_indicator(time_axis,
                                                      self.year_last_month,
                                                      self.last_month)
        multiplier_term_start = calc_term_start_indicator(time_axis,
                                                          self.portfolio.policy_inception_yr,
                                                          self.portfolio.policy_inception_month)
        multiplier_term = multiplier_term_end * multiplier_term_start

        return {
            (self.STATES_MODEL.ACTIVE, self.STATES_MODEL.DEATH): [
                (CfNames.DEATH_PAYMENT,
                 -multiplier_term * self.sum_insured_per_month * 12.0
                 )
             ]
        }

    def contractual_state_transitions(self, time_axis: TimeAxis) -> Iterable[tuple[AbstractStateModel,
                                                                                   AbstractStateModel,
                                                                                   npt.NDArray[np.int32]]]:
        # for the mortality term product there is only the transition
        # ACTIVE -> MATURED
        return [
            (self.STATES_MODEL.ACTIVE,
             self.STATES_MODEL.MATURED,
             calc_maturity_transition_indicator(time_axis, self.year_last_month, self.last_month)
             )
        ]


# # register the predefined products
# register_product("AnnuityInPayment", Product_AnnuityInPayment)
# register_product("TwoStateDisability", Product_TwoStateDisability)
# register_product("TERM", Product_MortalityTerm)
# register_product("AnnuityInPaymentYearlyAtBirthMonth", Product_AnnuityInPaymentYearlyAtBirthMonth)

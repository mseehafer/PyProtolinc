""" Export of the results. """

import logging
from enum import IntEnum, unique

import pandas as pd


# module level logger
logger = logging.getLogger(__name__)


@unique
class CfNames(IntEnum):
    """ The results vectors describing the evolution of the MultiStateDisabilityStates
        measured in terms probability (i.e., count)"""
    PREMIUM = 0
    ANNUITY_PAYMENT1 = 1
    ANNUITY_PAYMENT2 = 2
    DEATH_PAYMENT = 3
    DI_LUMPSUM_PAYMENT = 4


@unique
class ProbabilityVolumeResults(IntEnum):
    """ The results vectors describing the evolution of the MultiStateDisabilityStates
        measured in terms probability (i.e., count)"""
    VOL_ACTIVE = 0
    VOL_DIS1 = 1
    VOL_DIS2 = 2
    VOL_DEATH = 3
    VOL_LAPSED = 4
    VOL_MATURED = 5
    MV_ACTIVE_DEATH = 6
    MV_ACTIVE_DIS1 = 7
    MV_ACT_DIS2 = 8
    MV_ACT_LAPSED = 9
    MV_ACT_MATURED = 10
    MV_DIS1_DEATH = 11
    MV_DIS1_DIS2 = 12
    MV_DIS1_ACT = 13
    MV_DIS2_DEATH = 14
    MV_DIS2_DIS1 = 15
    MV_DIS2_ACT = 16


def export_results(result_data, outfile):

    logger.info("Exporting NCF to %s", outfile)

    # time_axis = projector.time_axis

    # data = {
    #     "YEAR": time_axis.years,
    #     "QUARTER": time_axis.quarters,
    #     "MONTH": time_axis.months,
    #     "PREMIUM": projector.ncf_portfolio[:, 0],
    #     "DI_ONG_CLAIMS1": projector.ncf_portfolio[:, 1],
    #     "DI_ONG_CLAIMS2": projector.ncf_portfolio[:, 2]
    # }

    # # add the reserves
    # for st in projector.model.states_model:
    #     data["RESERVE_BOM({})".format(st.name)] = projector.reserves_bom[:, st]

    # # add the probabilirty movements
    # for vol_prob_res in ProbabilityVolumeResults:
    #     data[vol_prob_res.name] = projector.probability_movements[:, vol_prob_res]

    df_ncf = pd.DataFrame(result_data)
    df_ncf.to_csv(outfile)

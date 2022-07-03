
from enum import IntEnum, unique

from pyprotolinc.results import ProbabilityVolumeResults


@unique
class MortalityStates(IntEnum):
    ACTIVE = 0      # the "alive state"
    DEATH = 1
    LAPSED = 2
    MATURED = 3

    @classmethod
    def to_std_outputs(cls):
        return {
            ProbabilityVolumeResults.VOL_ACTIVE: cls.ACTIVE,
            ProbabilityVolumeResults.VOL_DEATH: cls.DEATH,
            ProbabilityVolumeResults.VOL_LAPSED: cls.LAPSED,
            ProbabilityVolumeResults.VOL_MATURED: cls.MATURED,

            ProbabilityVolumeResults.MV_ACTIVE_DEATH: (cls.ACTIVE, cls.DEATH),
            ProbabilityVolumeResults.MV_ACT_LAPSED: (cls.ACTIVE, cls.LAPSED),
            ProbabilityVolumeResults.MV_ACT_MATURED: (cls.ACTIVE, cls.MATURED),
        }

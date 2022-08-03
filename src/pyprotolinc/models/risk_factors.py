from enum import IntEnum, unique
from pyprotolinc.models import check_states
from pyprotolinc import MAX_AGE

from pyprotolinc._actuarial import CRiskFactors


_C_RISK_FACTORS = {rf.name: rf for rf in CRiskFactors}


@unique
class RiskFactor(IntEnum):

    @classmethod
    def is_applicable(cls, base_assumption):
        _name = cls.__name__.upper()
        if base_assumption.horz_rf == _name or base_assumption.vert_rf == _name:
            return True
        else:
            return False

    @classmethod
    def validate_axis(cls, attribute_axis):
        raise Exception("Method must be implemented in subclass")

    @classmethod
    def required_length(self):
        raise Exception("Method must be implemented in subclass")

    def __repr__(self):
        return "RiskFactor:{}".format(self.__class__.__name__.upper())

    @classmethod
    def index_mapper(cls):
        # return identity by default
        return lambda x: x
    
    @classmethod
    def get_CRiskFactor(cls):
        return _C_RISK_FACTORS[cls.__name__]


@unique
class Gender(RiskFactor):
    M = 0
    F = 1

    @classmethod
    def required_length(self):
        return 2

    @classmethod
    def validate_axis(cls, attribute_axis):
        required_rf = [g.name for g in Gender]
        if set(attribute_axis) != set(required_rf):
            raise Exception("Risk Factors for Gender must be " + str({g for g in Gender}))

    @classmethod
    def index_mapper(cls):
        map_dict = {}
        for g in cls:
            map_dict[g.name] = int(g)

        return lambda name: map_dict[name]


@unique
class Age(RiskFactor):

    @classmethod
    def required_length(self):
        return MAX_AGE + 1

    @classmethod
    def validate_axis(cls, attribute_axis):
        # indexes = list(base_assumption.df_table.columns)
        if len(attribute_axis) < 120:
            raise Exception("Risk Factor AGE must have at least 120 entries")
        if attribute_axis[0] != 0:
            raise Exception("Risk Factor AGE must start at 0")

        for i in range(1, len(attribute_axis)):
            if attribute_axis[i - 1] + 1 != attribute_axis[i]:
                raise Exception("Risk Factor AGE must be ordered")


@unique
class CalendarYear(RiskFactor):

    @classmethod
    def required_length(self):
        return None

    @classmethod
    def validate_axis(cls, attribute_axis):
        if len(attribute_axis) < 150:
            raise Exception("CalendarYears should have lenght at leats 150")
        if attribute_axis[0] < 1999 or attribute_axis[0] > 2025:
            raise Exception("Risk Factor CALENDARYEAR starting value not plausible ({})"
                            .format(attribute_axis[0]))

        for i in range(1, len(attribute_axis)):
            if attribute_axis[i - 1] + 1 != attribute_axis[i]:
                raise Exception("Risk Factor CALENDARYEAR must be ordered")


@unique
class SmokerStatus(IntEnum):
    S = 0    # smoker
    N = 1    # non-smoker
    A = 2    # aggregate
    U = 3    # unknown

    # @classmethod
    # def is_applicable(cls, base_assumption):
    #     _name = cls.__name__.upper()
    #     if base_assumption.horz_rf == _name or base_assumption.vert_rf == _name:
    #         return True
    #     else:
    #         return False

    @classmethod
    def validate_axis(cls, attribute_axis):
        raise Exception("Method must be implemented in subclass")

    @classmethod
    def required_length(self):
        raise Exception("Method must be implemented in subclass")

    def __repr__(self):
        return "RiskFactor:{}".format(self.__class__.__name__.upper())

    @classmethod
    def index_mapper(cls):
        map_dict = {}
        for g in cls:
            map_dict[g.name] = int(g)
        return map_dict


@unique
class YearsDisabledIfDisabledAtStart(IntEnum):
    """ For certain select assumptions the time since the disablement date plays a role. 
        To apply this to an active needs more tracking than we can currently provide
        but for those being disabled since the start of the projection
        this can work. """

    @classmethod
    def validate_axis(cls, attribute_axis):
        raise Exception("Method must be implemented in subclass")

    @classmethod
    def required_length(self):
        raise Exception("Method must be implemented in subclass")

    def __repr__(self):
        return "RiskFactor:{}".format(self.__class__.__name__.upper())

    @classmethod
    def index_mapper(cls):
        map_dict = {}
        for g in cls:
            map_dict[g.name] = int(g)
        return map_dict



# validate the content of this module
check_states(Gender)

# a list of all risk factors;
# must be maintained manually for now
RISK_FACTORS = [Gender, Age, CalendarYear, SmokerStatus, YearsDisabledIfDisabledAtStart]
_rf_names = [cls.__name__.upper() for cls in RISK_FACTORS]


def get_risk_factor_by_name(rf_name):
    if rf_name is None:
        return None
    try:
        ind = _rf_names.index(rf_name)
    except ValueError:
        raise Exception("Risk Factor {} not known.".format(rf_name))

    return RISK_FACTORS[ind]


""" Abstract declaration of state models. """
from enum import IntEnum, unique
from abc import abstractmethod
from typing import Union
from pyprotolinc.results import ProbabilityVolumeResults


# here the state models are registered
_state_model_registry: dict[str, type] = {}


def check_state_model(EnumToCheck: type[IntEnum]) -> tuple[int, int]:
    """ Make sure that a state model uses consecutively numbered starting from zero.  """

    assert issubclass(EnumToCheck, IntEnum), "State Model must inherit from IntEnum"
    assert len(EnumToCheck) > 0, "State model must have at least one state"

    # find min/max and check everything in between is filled
    max_val = -1
    min_val = 999999
    state_vals = set()
    for st in EnumToCheck:
        max_val = max(int(st), max_val)
        min_val = min(int(st), min_val)
        state_vals.add(int(st))

    # print("Checking", EnumToCheck.__name__)
    assert min_val == 0, "Minimum value in state model must be 0"
    assert max_val == len(EnumToCheck) - 1, "Values must be consecutive integers"
    assert len(state_vals) == len(EnumToCheck), "Values must be unique"
    return min_val, max_val


def _register_state_model(cls: type["AbstractStateModel"]) -> None:
    """ Register a new statemodel- """
    if cls.__name__ in _state_model_registry:
        raise Exception(f"StateModel {cls.__name__} already defined.")
    if cls.__name__ != "AbstractStateModel":    # note the hardcoded name, keep in sync with class name below
        check_state_model(cls)
        _state_model_registry[cls.__name__] = cls


def show_state_models() -> dict[str, type]:
    """ Returns a dict containing the currently registered state models. """
    return dict(_state_model_registry)


def states_model(cls: type["AbstractStateModel"]) -> type["AbstractStateModel"]:
    """ To be used as a decorator on StateModel that will registers those. """
    _register_state_model(cls)
    return cls


@states_model
class AbstractStateModel(IntEnum):
    """ The base class for state models. """

    @classmethod
    @abstractmethod
    def describe(cls: type["AbstractStateModel"]) -> str:
        return cls.__name__ + ": " + str(cls.__doc__)

    @classmethod
    @abstractmethod
    def to_std_outputs(cls: type["AbstractStateModel"]) -> dict[ProbabilityVolumeResults, Union["AbstractStateModel", tuple["AbstractStateModel", "AbstractStateModel"]]]:
        return {}


def state_model_by_name(name: str) -> type[AbstractStateModel]:
    """ Return the state model class belonging to the name. """
    return _state_model_registry[name]

############################################################
# Definition of the built-in state models are defined
############################################################


@states_model
@unique
class AnnuityRunoffStates(AbstractStateModel):
    """ A state model consisting of two states:
        - DIS1 (=0) representing the annuity phase
        - DEATH (=1)
    """
    DIS1 = 0    # the "annuitant state"
    DEATH = 1   # the death state

    @classmethod
    def to_std_outputs(cls: type["AnnuityRunoffStates"]) -> dict[ProbabilityVolumeResults, Union["AbstractStateModel", tuple["AbstractStateModel", "AbstractStateModel"]]]:
        return {
            # ProbabilityVolumeResults.VOL_ACTIVE: None,
            ProbabilityVolumeResults.VOL_DIS1: cls.DIS1,
            # ProbabilityVolumeResults.VOL_DIS2: None,
            ProbabilityVolumeResults.VOL_DEATH: cls.DEATH,
            # ProbabilityVolumeResults.VOL_LAPSED: None,

            # ProbabilityVolumeResults.MV_ACTIVE_DEATH: (None, None),
            # ProbabilityVolumeResults.MV_ACTIVE_DIS1: (None, None),
            # ProbabilityVolumeResults.MV_ACT_DIS2: (None, None),
            # ProbabilityVolumeResults.MV_ACT_LAPSED: (None, None),

            ProbabilityVolumeResults.MV_DIS1_DEATH: (cls.DIS1, cls.DEATH),
            # ProbabilityVolumeResults.MV_DIS1_DIS2: (None, None),
            # ProbabilityVolumeResults.MV_DIS1_ACT: (None, None),

            # ProbabilityVolumeResults.MV_DIS2_DEATH: (None, None),
            # ProbabilityVolumeResults.MV_DIS2_DIS1: (None, None),
            # ProbabilityVolumeResults.MV_DIS2_ACT: (None, None),
        }


@states_model
@unique
class MortalityStates(AbstractStateModel):
    """ A state model with four states that can be used to model simple mortality term/perm products.
        - ACTIVE = 0
        - DEATH = 1
        - LAPSED = 2
        - MATURED = 3
    """
    ACTIVE = 0      # the "alive state"
    DEATH = 1
    LAPSED = 2
    MATURED = 3

    @classmethod
    def to_std_outputs(cls: type["MortalityStates"]) -> dict[ProbabilityVolumeResults, Union["AbstractStateModel", tuple["AbstractStateModel", "AbstractStateModel"]]]:
        return {
            ProbabilityVolumeResults.VOL_ACTIVE: cls.ACTIVE,
            ProbabilityVolumeResults.VOL_DEATH: cls.DEATH,
            ProbabilityVolumeResults.VOL_LAPSED: cls.LAPSED,
            ProbabilityVolumeResults.VOL_MATURED: cls.MATURED,

            ProbabilityVolumeResults.MV_ACTIVE_DEATH: (cls.ACTIVE, cls.DEATH),
            ProbabilityVolumeResults.MV_ACT_LAPSED: (cls.ACTIVE, cls.LAPSED),
            ProbabilityVolumeResults.MV_ACT_MATURED: (cls.ACTIVE, cls.MATURED),
        }


@states_model
@unique
class MultiStateDisabilityStates(AbstractStateModel):
    """ A state model for a disabiility product with two disabled states. 
        - ACTIVE = 0
        - DIS1 = 1
        - DIS2 = 2
        - DEATH = 3
        - LAPSED = 4
    """
    ACTIVE = 0
    DIS1 = 1
    DIS2 = 2
    DEATH = 3
    LAPSED = 4

    @classmethod
    def to_std_outputs(cls: type["MultiStateDisabilityStates"]) -> dict[ProbabilityVolumeResults, Union["AbstractStateModel", tuple["AbstractStateModel", "AbstractStateModel"]]]:
        return {
            ProbabilityVolumeResults.VOL_ACTIVE: cls.ACTIVE,
            ProbabilityVolumeResults.VOL_DIS1: cls.DIS1,
            ProbabilityVolumeResults.VOL_DIS2: cls.DIS2,
            ProbabilityVolumeResults.VOL_DEATH: cls.DEATH,
            ProbabilityVolumeResults.VOL_LAPSED: cls.LAPSED,

            ProbabilityVolumeResults.MV_ACTIVE_DEATH: (cls.ACTIVE, cls.DEATH),
            ProbabilityVolumeResults.MV_ACTIVE_DIS1: (cls.ACTIVE, cls.DIS1),
            ProbabilityVolumeResults.MV_ACT_DIS2: (cls.ACTIVE, cls.DIS2),
            ProbabilityVolumeResults.MV_ACT_LAPSED: (cls.ACTIVE, cls.LAPSED),

            ProbabilityVolumeResults.MV_DIS1_DEATH: (cls.DIS1, cls.DEATH),
            ProbabilityVolumeResults.MV_DIS1_DIS2: (cls.DIS1, cls.DIS2),
            ProbabilityVolumeResults.MV_DIS1_ACT: (cls.DIS1, cls.ACTIVE),

            ProbabilityVolumeResults.MV_DIS2_DEATH: (cls.DIS2, cls.DEATH),
            ProbabilityVolumeResults.MV_DIS2_DIS1: (cls.DIS2, cls.DIS1),
            ProbabilityVolumeResults.MV_DIS2_ACT: (cls.DIS2, cls.ACTIVE)
        }

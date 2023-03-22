""" Abstract declaration of state models. """

from enum import IntEnum
from abc import abstractclassmethod, ABCMeta

from pyprotolinc.results import ProbabilityVolumeResults


class AbstractStateModelMeta(ABCMeta, type(IntEnum)):
    """ Meta class that combines ABC and the IntEnum."""
    pass


class AbstractStateModel(IntEnum, metaclass=AbstractStateModelMeta):
    """ The base class for state models. """

    @abstractclassmethod
    def describe(cls) -> str:
        return cls.__doc__

    @abstractclassmethod
    def to_std_outputs(cls) -> dict[ProbabilityVolumeResults, "AbstractStateModel"]:
        pass


import logging

from pyprotolinc.models.model_disability_multistate import MultiStateDisabilityModel
from pyprotolinc.models.model_disability_multistate import MultiStateDisabilityStates
from pyprotolinc.models import register_state_model
from pyprotolinc.models.model_annuity_runoff import AnnuityRunoffModel
from pyprotolinc.models.model_annuity_runoff import AnnuityRunoffStates
from pyprotolinc.models.model_mortality import MortalityStates

from pyprotolinc.models.model_multistate_generic import GenericMultiStateModel


logger = logging.getLogger(__name__)

# the models known
_MODELS = {}


def get_model_by_name(name):
    return _MODELS[name]


def register_model(cls):
    if _MODELS.get(cls.MODEL_NAME) is None:
        _MODELS[cls.MODEL_NAME] = cls
        logger.debug("Registered model %s", cls.MODEL_NAME)


register_state_model(MultiStateDisabilityStates)
register_model(MultiStateDisabilityModel)

register_state_model(AnnuityRunoffStates)
register_model(AnnuityRunoffModel)

register_state_model(MortalityStates)

register_model(GenericMultiStateModel)

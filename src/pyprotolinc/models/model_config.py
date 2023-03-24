
import logging

from pyprotolinc.models import Model
from pyprotolinc.models.model_multistate_generic import GenericMultiStateModel


logger = logging.getLogger(__name__)

# the models known
_MODELS: dict[str, type[Model]] = {}


def get_model_by_name(name: str) -> type[Model]:
    return _MODELS[name]


def register_model(cls: type[Model]) -> None:
    if _MODELS.get(cls.MODEL_NAME) is None:
        _MODELS[cls.MODEL_NAME] = cls
        logger.debug("Registered model %s", cls.MODEL_NAME)


register_model(GenericMultiStateModel)

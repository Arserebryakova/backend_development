from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from repositories.predictions import PredictionRepository
from services.moderation import ModerationService


@lru_cache
def get_prediction_repository() -> PredictionRepository:
    return PredictionRepository()


def get_moderation_service(
    repository: Annotated[PredictionRepository, Depends(get_prediction_repository)],
) -> ModerationService:
    return ModerationService(repository)


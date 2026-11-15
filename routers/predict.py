from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import StrictBool

from dependencies import get_moderation_service
from schemas import ErrorResponse, PredictionRequest, ValidationErrorResponse
from services.moderation import ModerationService

router = APIRouter()


@router.post(
    "/predict",
    response_model=StrictBool,
    summary="Проверить объявление на нарушения",
    response_description="true — есть нарушение, false — нарушений нет",
    responses={
        400: {"model": ValidationErrorResponse, "description": "Некорректные данные"},
        500: {"model": ErrorResponse, "description": "Внутренняя ошибка сервиса"},
    },
)
def predict(
    advertisement: PredictionRequest,
    service: Annotated[ModerationService, Depends(get_moderation_service)],
) -> bool:
    """Нарушение: продавец не подтверждён и у объявления нет изображений."""
    return service.predict(advertisement)


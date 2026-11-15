from repositories.predictions import PredictionRepository
from schemas import PredictionRequest


class ModerationService:
    def __init__(self, repository: PredictionRepository) -> None:
        self._repository = repository

    def predict(self, advertisement: PredictionRequest) -> bool:
        """Return True when an advertisement has a violation."""
        has_violation = (
            not advertisement.is_verified_seller and advertisement.images_qty == 0
        )
        self._repository.save(advertisement.item_id, has_violation)
        return has_violation


from unittest.mock import Mock

import pytest

from repositories.predictions import PredictionRepository
from schemas import PredictionRequest
from services.moderation import ModerationService


@pytest.mark.parametrize(
    "is_verified,images_qty,expected",
    [(True, 0, False), (True, 2, False), (False, 0, True), (False, 2, False)],
)
def test_service_predicts_and_saves(valid_payload, is_verified, images_qty, expected):
    repository = Mock(spec=PredictionRepository)
    service = ModerationService(repository)
    valid_payload.update(is_verified_seller=is_verified, images_qty=images_qty)

    result = service.predict(PredictionRequest(**valid_payload))

    assert result is expected
    repository.save.assert_called_once_with(valid_payload["item_id"], expected)


def test_service_propagates_repository_failure(valid_payload):
    repository = Mock(spec=PredictionRepository)
    repository.save.side_effect = RuntimeError("storage unavailable")
    service = ModerationService(repository)

    with pytest.raises(RuntimeError, match="storage unavailable"):
        service.predict(PredictionRequest(**valid_payload))


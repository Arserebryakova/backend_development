import pytest
from fastapi.testclient import TestClient

from dependencies import get_prediction_repository
from main import app
from repositories.predictions import PredictionRepository


@pytest.fixture
def repository() -> PredictionRepository:
    return PredictionRepository()


@pytest.fixture
def client(repository: PredictionRepository):
    app.dependency_overrides[get_prediction_repository] = lambda: repository
    # Real HTTP clients receive 500 instead of the server-side exception.
    try:
        with TestClient(app, raise_server_exceptions=False) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def valid_payload() -> dict:
    return {
        "seller_id": 1,
        "is_verified_seller": False,
        "item_id": 10,
        "name": "Велосипед",
        "description": "Городской велосипед в хорошем состоянии",
        "category": 2,
        "images_qty": 1,
    }


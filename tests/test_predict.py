from unittest.mock import Mock

import pytest

from dependencies import get_moderation_service
from main import app
from services.moderation import ModerationService


@pytest.mark.parametrize(
    "is_verified,images_qty,expected",
    [
        (True, 0, False),
        (True, 1, False),
        (True, 10, False),
        (False, 0, True),
        (False, 1, False),
        (False, 10, False),
    ],
)
def test_predict(client, repository, valid_payload, is_verified, images_qty, expected):
    valid_payload.update(is_verified_seller=is_verified, images_qty=images_qty)

    response = client.post("/predict", json=valid_payload)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() is expected
    assert repository.get(valid_payload["item_id"]) is expected


@pytest.mark.parametrize(
    "field",
    [
        "seller_id", "is_verified_seller", "item_id", "name",
        "description", "category", "images_qty",
    ],
)
def test_predict_requires_every_field(client, valid_payload, field):
    valid_payload.pop(field)

    response = client.post("/predict", json=valid_payload)

    assert response.status_code == 400
    assert any(
        error["loc"] == ["body", field] and error["type"] == "missing"
        for error in response.json()["detail"]
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("seller_id", "1"), ("seller_id", True), ("seller_id", 1.5),
        ("item_id", "10"), ("item_id", False), ("item_id", 10.0),
        ("category", "2"), ("category", True), ("category", 2.5),
        ("images_qty", "1"), ("images_qty", True), ("images_qty", 1.0),
        ("is_verified_seller", "false"), ("is_verified_seller", 0),
        ("is_verified_seller", 1),
        ("name", 123), ("name", False), ("name", []),
        ("description", 123), ("description", True), ("description", {}),
    ],
)
def test_predict_rejects_wrong_types(client, valid_payload, field, value):
    valid_payload[field] = value

    response = client.post("/predict", json=valid_payload)

    assert response.status_code == 400
    assert any(error["loc"] == ["body", field] for error in response.json()["detail"])


@pytest.mark.parametrize(
    "field",
    [
        "seller_id", "is_verified_seller", "item_id", "name",
        "description", "category", "images_qty",
    ],
)
def test_predict_rejects_null(client, valid_payload, field):
    valid_payload[field] = None

    response = client.post("/predict", json=valid_payload)

    assert response.status_code == 400
    assert any(error["loc"] == ["body", field] for error in response.json()["detail"])


@pytest.mark.parametrize(
    "field,value",
    [
        ("seller_id", 0), ("seller_id", -1),
        ("item_id", 0), ("item_id", -1),
        ("category", 0), ("category", -1),
        ("images_qty", -1),
        ("name", ""), ("name", "  \t\n"),
        ("description", ""), ("description", "  \t\n"),
    ],
)
def test_predict_rejects_invalid_values(client, repository, valid_payload, field, value):
    valid_payload[field] = value

    response = client.post("/predict", json=valid_payload)

    assert response.status_code == 400
    assert any(error["loc"] == ["body", field] for error in response.json()["detail"])
    assert repository.get(10) is None


def test_predict_rejects_unknown_fields(client, valid_payload):
    valid_payload["unexpected"] = "value"

    response = client.post("/predict", json=valid_payload)

    assert response.status_code == 400
    assert response.json()["detail"][0]["type"] == "extra_forbidden"


@pytest.mark.parametrize("body", [None, [], "text", 42, True])
def test_predict_requires_json_object(client, body):
    response = client.post("/predict", json=body)

    assert response.status_code == 400
    assert isinstance(response.json()["detail"], list)


def test_predict_rejects_malformed_json(client):
    response = client.post(
        "/predict", content='{"seller_id":', headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 400
    assert response.json()["detail"][0]["type"] == "json_invalid"


@pytest.mark.parametrize("error", [RuntimeError("secret"), ValueError("secret")])
def test_predict_handles_business_logic_error(client, valid_payload, error, caplog):
    service = Mock(spec=ModerationService)
    service.predict.side_effect = error
    app.dependency_overrides[get_moderation_service] = lambda: service

    response = client.post("/predict", json=valid_payload)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "Unhandled error for POST /predict" in caplog.text


def test_predict_handles_repository_error(client, repository, valid_payload, monkeypatch):
    monkeypatch.setattr(repository, "save", Mock(side_effect=RuntimeError("storage failed")))

    response = client.post("/predict", json=valid_payload)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}


def test_predict_validates_service_result(client, valid_payload):
    service = Mock(spec=ModerationService)
    service.predict.return_value = "false"
    app.dependency_overrides[get_moderation_service] = lambda: service

    response = client.post("/predict", json=valid_payload)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}


def test_root(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_openapi_matches_predict_contract(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    operation = response.json()["paths"]["/predict"]["post"]
    assert set(operation["responses"]) == {"200", "400", "500"}
    success_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert success_schema["type"] == "boolean"


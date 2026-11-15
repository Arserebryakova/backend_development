class PredictionRepository:
    """Store the latest prediction for each item in this process's memory."""

    def __init__(self) -> None:
        self._predictions: dict[int, bool] = {}

    def save(self, item_id: int, has_violation: bool) -> None:
        self._predictions[item_id] = has_violation

    def get(self, item_id: int) -> bool | None:
        return self._predictions.get(item_id)


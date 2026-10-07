import json
from datetime import date
from decimal import Decimal

import pytest

from import_daily_metrics import import_daily_metrics


SAMPLE = {
    "campaign_id": 1,
    "metric_date": "2026-10-04",
    "impressions": 2000,
    "clicks": 100,
    "spend": "75.00",
    "currency_code": "USD",
}


class RecordingConnection:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params):
        self.calls.append(params)
        return self

    def fetchone(self):
        return self.calls[-1]


def test_invalid_record_is_quarantined_and_next_record_is_saved(tmp_path):
    invalid = {**SAMPLE, "metric_date": "2026-10-05", "spend": "-5.00"}
    last = {
        **SAMPLE, "metric_date": "2026-10-07", "impressions": 2200,
        "clicks": 110, "spend": "82.50",
    }
    source = tmp_path / "source.json"
    source.write_text(json.dumps([SAMPLE, invalid, last]), encoding="utf-8")
    rejected = tmp_path / "quarantine" / "rejected.json"
    connection = RecordingConnection()

    result = import_daily_metrics(connection, source, rejected)

    assert result == {"saved": 2, "rejected": 1}
    assert connection.calls == [
        (1, date(2026, 10, 4), 2000, 100, Decimal("75.00"), "USD"),
        (1, date(2026, 10, 7), 2200, 110, Decimal("82.50"), "USD"),
    ]
    errors = json.loads(rejected.read_text(encoding="utf-8"))
    assert len(errors) == 1
    assert errors[0]["record_number"] == 2
    assert errors[0]["raw_data"] == invalid
    assert errors[0]["errors"][0]["loc"] == ["spend"]
    assert errors[0]["errors"][0]["type"] == "greater_than_equal"
    assert errors[0]["errors"][0]["msg"]


def test_empty_source_returns_zero_counts(tmp_path):
    source = tmp_path / "source.json"
    source.write_text("[]", encoding="utf-8")
    rejected = tmp_path / "rejected.json"
    connection = RecordingConnection()

    result = import_daily_metrics(connection, source, rejected)

    assert result == {"saved": 0, "rejected": 0}
    assert connection.calls == []
    assert json.loads(rejected.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize("wrong_shape", [SAMPLE, None])
def test_source_must_be_a_list_of_records(tmp_path, wrong_shape):
    source = tmp_path / "source.json"
    source.write_text(json.dumps(wrong_shape), encoding="utf-8")
    connection = RecordingConnection()

    with pytest.raises(ValueError, match="danh sách record"):
        import_daily_metrics(connection, source, tmp_path / "rejected.json")

    assert connection.calls == []


def test_database_error_is_not_hidden_as_invalid_data(tmp_path):
    class FailingConnection:
        def execute(self, sql, params):
            raise RuntimeError("database unavailable")

    source = tmp_path / "source.json"
    source.write_text(json.dumps([SAMPLE]), encoding="utf-8")
    rejected = tmp_path / "rejected.json"

    with pytest.raises(RuntimeError, match="database unavailable"):
        import_daily_metrics(FailingConnection(), source, rejected)

    assert not rejected.exists()

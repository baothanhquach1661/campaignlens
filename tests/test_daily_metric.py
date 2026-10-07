from datetime import date
from decimal import Decimal

import pytest
from daily_metric import DailyMetric
from pydantic import ValidationError

SAMPLE = {
    "campaign_id": 1,
    "metric_date": "2026-10-05",
    "impressions": 1600,
    "clicks": 80,
    "spend": "60.00",
    "currency_code": "USD",
}


def test_valid_metric_is_parsed():
    metric = DailyMetric.model_validate(SAMPLE)

    assert metric.campaign_id == 1
    assert metric.metric_date == date(2026, 10, 5)
    assert metric.impressions == 1600
    assert metric.clicks == 80
    assert metric.spend == Decimal("60.00")
    assert metric.currency_code == "USD"


def test_zero_metrics_are_allowed():
    data = {**SAMPLE, "impressions": 0, "clicks": 0, "spend": "0.00"}

    metric = DailyMetric.model_validate(data)

    assert metric.impressions == 0
    assert metric.clicks == 0
    assert metric.spend == Decimal("0.00")


@pytest.mark.parametrize(
    "field, value",
    [
        ("campaign_id", 0),
        ("impressions", -1),
        ("clicks", -1),
        ("clicks", 1.5),
        ("spend", "-5.00"),
        ("spend", "60.001"),
        ("spend", "1000000000000.00"),
        ("currency_code", "US"),
    ],
)
def test_invalid_values_are_rejected(field, value):
    data = {**SAMPLE, field: value}

    with pytest.raises(ValidationError) as error:
        DailyMetric.model_validate(data)

    assert any(item["loc"] == (field,) for item in error.value.errors())


def test_missing_clicks_are_rejected():
    data = SAMPLE.copy()
    del data["clicks"]

    with pytest.raises(ValidationError) as error:
        DailyMetric.model_validate(data)

    assert any(item["loc"] == ("clicks",) for item in error.value.errors())


def test_unexpected_field_is_rejected():
    data = {**SAMPLE, "click_count": 80}

    with pytest.raises(ValidationError) as error:
        DailyMetric.model_validate(data)

    assert any(item["loc"] == ("click_count",) for item in error.value.errors())

import os
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from sync_daily_metric import upsert_daily_metric

SAMPLE = {
    "campaign_id": 1,
    "metric_date": "2026-10-06",
    "impressions": 1800,
    "clicks": 90,
    "spend": "67.50",
    "currency_code": "USD",
}


class RecordingConnection:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params):
        self.calls.append((sql, params))
        return self

    def fetchone(self):
        return self.calls[-1][1]


@pytest.mark.parametrize(
    "invalid_data",
    [
        {"spend": "-5.00"},
        {"click_count": 90},
    ],
)
def test_invalid_metric_never_runs_sql(invalid_data):
    connection = RecordingConnection()

    with pytest.raises(ValidationError):
        upsert_daily_metric(connection, {**SAMPLE, **invalid_data})

    assert connection.calls == []


def test_valid_metric_sends_typed_values_as_parameters():
    connection = RecordingConnection()

    result = upsert_daily_metric(connection, SAMPLE)

    assert len(connection.calls) == 1
    assert connection.calls[0][1] == (
        1,
        date(2026, 10, 6),
        1800,
        90,
        Decimal("67.50"),
        "USD",
    )
    assert result == connection.calls[0][1]


def test_rerun_updates_one_row_in_postgres_and_rolls_back():
    dotenv = pytest.importorskip("dotenv")
    dotenv.load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    password = os.getenv("CAMPAIGNLENS_DB_PASSWORD")
    if not password:
        pytest.skip("Cần file .env để kiểm tra PostgreSQL")

    import psycopg

    connection = psycopg.connect(
        host="127.0.0.1",
        port=5433,
        dbname="adflow",
        user="adflow",
        password=password,
        autocommit=False,
        connect_timeout=3,
    )
    try:
        upsert_daily_metric(connection, SAMPLE)
        corrected = {**SAMPLE, "impressions": 1900, "clicks": 95, "spend": "71.25"}
        upsert_daily_metric(connection, corrected)

        rows = connection.execute(
            """SELECT impressions, clicks, spend
               FROM public.campaign_daily_metrics
               WHERE campaign_id = %s AND metric_date = %s""",
            (1, date(2026, 10, 6)),
        ).fetchall()
        assert rows == [(1900, 95, Decimal("71.25"))]
    finally:
        connection.rollback()
        connection.close()

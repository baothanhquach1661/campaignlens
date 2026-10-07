import os
from pathlib import Path

from daily_metric import DailyMetric

UPSERT_SQL = """
    INSERT INTO public.campaign_daily_metrics
        (campaign_id, metric_date, impressions, clicks, spend, currency_code)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (campaign_id, metric_date)
    DO UPDATE SET
        impressions = EXCLUDED.impressions,
        clicks = EXCLUDED.clicks,
        spend = EXCLUDED.spend,
        currency_code = EXCLUDED.currency_code
    RETURNING campaign_id, metric_date, impressions, clicks, spend, currency_code
"""


def upsert_daily_metric(connection, raw_metric):
    metric = DailyMetric.model_validate(raw_metric)
    return connection.execute(
        UPSERT_SQL,
        (
            metric.campaign_id,
            metric.metric_date,
            metric.impressions,
            metric.clicks,
            metric.spend,
            metric.currency_code,
        ),
    ).fetchone()


if __name__ == "__main__":
    import psycopg
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).with_name(".env"))
    password = os.getenv("CAMPAIGNLENS_DB_PASSWORD")
    if not password:
        raise SystemExit("Thêm CAMPAIGNLENS_DB_PASSWORD vào file .env")

    sample = {
        "campaign_id": 1,
        "metric_date": "2026-10-06",
        "impressions": 1800,
        "clicks": 90,
        "spend": "67.50",
        "currency_code": "USD",
    }
    with psycopg.connect(
        host="127.0.0.1",
        port=5433,
        dbname="adflow",
        user="adflow",
        password=password,
        connect_timeout=3,
    ) as connection:
        result = upsert_daily_metric(connection, sample)
    print(result)

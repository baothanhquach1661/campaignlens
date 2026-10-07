import json
import os
from pathlib import Path

from pydantic import ValidationError

from sync_daily_metric import upsert_daily_metric


def import_daily_metrics(connection, source_path, rejected_path):
    records = json.loads(Path(source_path).read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("File JSON phải chứa một danh sách record: [...]")

    saved = 0
    rejected = []

    for record_number, raw_metric in enumerate(records, start=1):
        try:
            upsert_daily_metric(connection, raw_metric)
        except ValidationError as error:
            rejected.append({
                "record_number": record_number,
                "raw_data": raw_metric,
                "errors": [
                    {
                        "loc": list(item["loc"]),
                        "msg": item["msg"],
                        "type": item["type"],
                    }
                    for item in error.errors()
                ],
            })
        else:
            saved += 1

    output = Path(rejected_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(rejected, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"saved": saved, "rejected": len(rejected)}


if __name__ == "__main__":
    import psycopg
    from dotenv import load_dotenv

    root = Path(__file__).resolve().parent
    load_dotenv(root / ".env")
    password = os.getenv("CAMPAIGNLENS_DB_PASSWORD")
    if not password:
        raise SystemExit("Thêm CAMPAIGNLENS_DB_PASSWORD vào file .env")

    rejected_path = root / "quarantine" / "daily_metrics_rejected.json"
    with psycopg.connect(
        host="127.0.0.1", port=5433, dbname="adflow", user="adflow",
        password=password, connect_timeout=3,
    ) as connection:
        result = import_daily_metrics(
            connection, root / "data" / "mock_daily_metrics.json", rejected_path
        )

    print(
        f"Đã xử lý {result['saved']} record hợp lệ; "
        f"cách ly {result['rejected']} record."
    )
    print(f"File cách ly: {rejected_path}")

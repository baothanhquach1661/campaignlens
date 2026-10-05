import os
from html import escape

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

load_dotenv()
app = FastAPI(title="CampaignLens")


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    password = os.getenv("CAMPAIGNLENS_DB_PASSWORD")
    if not password:
        return HTMLResponse(
            "<h1>CampaignLens</h1><p>Thêm CAMPAIGNLENS_DB_PASSWORD vào file .env.</p>",
            status_code=503,
        )

    with psycopg.connect(
        host="127.0.0.1",
        port=5433,
        dbname="adflow",
        user="adflow",
        password=password,
        connect_timeout=3,
    ) as connection:
        clients = connection.execute(
            "SELECT client_code, client_name FROM public.clients ORDER BY client_id"
        ).fetchall()

    rows = "\n".join(
        f"<tr><td>{escape(code)}</td><td>{escape(name)}</td></tr>"
        for code, name in clients
    )

    return HTMLResponse(f"""<!doctype html>
<html lang="vi">
<head><meta charset="utf-8"><title>CampaignLens</title></head>
<body style="font-family:system-ui;background:#f3f6fb;color:#16233b">
  <main style="max-width:720px;margin:64px auto;padding:32px;background:white;border-radius:12px">
    <h1>CampaignLens</h1>
    <p>Khách hàng trong PostgreSQL: <strong>{len(clients)}</strong></p>
    <table style="width:100%;text-align:left;border-spacing:0 12px">
      <thead><tr><th>Mã khách</th><th>Tên khách hàng</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </main>
</body>
</html>""")

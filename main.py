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
        f'<tr><td style="padding:14px 12px;border-bottom:1px solid #eef0f3">{escape(code)}</td>'
        f'<td style="padding:14px 12px;border-bottom:1px solid #eef0f3">{escape(name)}</td></tr>'
        for code, name in clients
    )

    return HTMLResponse(f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Clients | CampaignLens</title>
</head>
<body style="margin:0;font-family:system-ui;background:#f6f7f9;color:#142238">
  <div style="display:flex;min-height:100vh">
    <aside style="width:230px;flex-shrink:0;background:white;border-right:1px solid #e5e8ec;padding:28px 20px;box-sizing:border-box">
      <strong style="display:block;font-size:22px;margin-bottom:44px">CampaignLens</strong>
      <nav aria-label="Điều hướng chính">
        <a href="/" aria-current="page" style="display:block;padding:12px 14px;border-radius:8px;background:#edf3ff;color:#174baf;font-weight:650;text-decoration:none">Clients</a>
      </nav>
    </aside>
    <main style="flex:1;min-width:0;padding:48px 5vw">
      <header style="margin-bottom:28px">
        <h1 style="font-size:30px;margin:0 0 8px">Clients</h1>
        <p style="color:#6b7280;margin:0">Khách hàng của agency</p>
      </header>
      <section style="max-width:920px;background:white;border:1px solid #e5e8ec;border-radius:12px;padding:24px">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:18px">
          <h2 style="font-size:18px;margin:0">Danh sách khách hàng</h2>
          <span style="font-size:14px;color:#5f6b7a">{len(clients)} khách hàng</span>
        </div>
        <div style="overflow-x:auto">
          <table style="width:100%;border-collapse:collapse;text-align:left">
            <thead><tr>
              <th scope="col" style="padding:12px;border-bottom:1px solid #e5e8ec">Mã khách</th>
              <th scope="col" style="padding:12px;border-bottom:1px solid #e5e8ec">Tên khách hàng</th>
            </tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
      </section>
    </main>
  </div>
</body>
</html>""")

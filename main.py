import os
from html import escape
from urllib.parse import quote_plus

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
            """
            SELECT c.client_code, c.client_name, COUNT(a.ad_account_id) AS account_count
            FROM public.clients AS c
            LEFT JOIN public.ad_accounts AS a ON a.client_id = c.client_id
            GROUP BY c.client_id, c.client_code, c.client_name
            ORDER BY c.client_id
            """
        ).fetchall()

    rows = "\n".join(
        f'<tr><td style="padding:14px 12px;border-bottom:1px solid #eef0f3">'
        f'<a href="/accounts?client_code={quote_plus(code)}" style="color:#174baf">{escape(code)}</a></td>'
        f'<td style="padding:14px 12px;border-bottom:1px solid #eef0f3">{escape(name)}</td>'
        f'<td style="padding:14px 12px;border-bottom:1px solid #eef0f3">{count}</td></tr>'
        for code, name, count in clients
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
              <th scope="col" style="padding:12px;border-bottom:1px solid #e5e8ec">Tài khoản quảng cáo</th>
            </tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
      </section>
    </main>
  </div>
</body>
</html>""")


@app.get("/accounts", response_class=HTMLResponse)
def show_accounts(client_code: str) -> HTMLResponse:
    password = os.getenv("CAMPAIGNLENS_DB_PASSWORD")
    if not password:
        return HTMLResponse("<h1>Thiếu cấu hình database</h1>", status_code=503)

    with psycopg.connect(
        host="127.0.0.1",
        port=5433,
        dbname="adflow",
        user="adflow",
        password=password,
        connect_timeout=3,
    ) as connection:
        records = connection.execute(
            """
            SELECT c.client_name, a.platform, a.external_account_id
            FROM public.clients AS c
            LEFT JOIN public.ad_accounts AS a ON a.client_id = c.client_id
            WHERE c.client_code = %s
            ORDER BY a.platform, a.external_account_id
            """,
            (client_code,),
        ).fetchall()

        campaigns = connection.execute(
            """
            SELECT a.platform, a.external_account_id,
                   g.external_campaign_id, g.campaign_name
            FROM public.campaigns AS g
            JOIN public.ad_accounts AS a ON a.ad_account_id = g.ad_account_id
            JOIN public.clients AS c ON c.client_id = a.client_id
            WHERE c.client_code = %s
            ORDER BY a.platform, a.external_account_id, g.campaign_name
            """,
            (client_code,),
        ).fetchall()

    if not records:
        return HTMLResponse("<h1>Không tìm thấy khách hàng</h1>", status_code=404)

    client_name = records[0][0]
    accounts = [
        (platform, external_id)
        for _, platform, external_id in records
        if platform is not None
    ]

    account_rows = (
        "\n".join(
            f'<tr><td style="padding:14px 12px;border-bottom:1px solid #eef0f3">{escape(platform)}</td>'
            f'<td style="padding:14px 12px;border-bottom:1px solid #eef0f3">{escape(external_id)}</td></tr>'
            for platform, external_id in accounts
        )
        or '<tr><td colspan="2" style="padding:14px 12px">Chưa có tài khoản quảng cáo.</td></tr>'
    )

    campaign_rows = (
        "\n".join(
            f'<tr><td style="padding:14px 12px;border-bottom:1px solid #eef0f3">{escape(platform)}</td>'
            f'<td style="padding:14px 12px;border-bottom:1px solid #eef0f3">{escape(external_account_id)}</td>'
            f'<td style="padding:14px 12px;border-bottom:1px solid #eef0f3">{escape(external_campaign_id)}</td>'
            f'<td style="padding:14px 12px;border-bottom:1px solid #eef0f3">{escape(campaign_name)}</td></tr>'
            for platform, external_account_id, external_campaign_id, campaign_name in campaigns
        )
        or '<tr><td colspan="4" style="padding:14px 12px">Chưa có chiến dịch.</td></tr>'
    )

    return HTMLResponse(f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(client_name)} | CampaignLens</title>
</head>
<body style="margin:0;font-family:system-ui;background:#f6f7f9;color:#142238">
  <div style="display:flex;min-height:100vh">
    <aside style="width:230px;flex-shrink:0;background:white;border-right:1px solid #e5e8ec;padding:28px 20px;box-sizing:border-box">
      <strong style="display:block;font-size:22px;margin-bottom:44px">CampaignLens</strong>
      <nav aria-label="Điều hướng chính">
        <a href="/" style="display:block;padding:12px 14px;border-radius:8px;color:#174baf;font-weight:650;text-decoration:none">Clients</a>
      </nav>
    </aside>
    <main style="flex:1;min-width:0;padding:48px 5vw">
      <a href="/" style="color:#174baf">← Quay lại Clients</a>
      <header style="margin:24px 0 28px">
        <h1 style="font-size:30px;margin:0 0 8px">{escape(client_name)}</h1>
        <p style="color:#6b7280;margin:0">Mã khách: {escape(client_code)}</p>
      </header>
      <section style="max-width:920px;background:white;border:1px solid #e5e8ec;border-radius:12px;padding:24px">
        <h2 style="font-size:18px;margin:0 0 18px">Tài khoản quảng cáo ({len(accounts)})</h2>
        <div style="overflow-x:auto">
          <table style="width:100%;border-collapse:collapse;text-align:left">
            <thead><tr>
              <th scope="col" style="padding:12px;border-bottom:1px solid #e5e8ec">Nền tảng</th>
              <th scope="col" style="padding:12px;border-bottom:1px solid #e5e8ec">Mã tài khoản trên nền tảng</th>
            </tr></thead>
            <tbody>{account_rows}</tbody>
          </table>
        </div>
      </section>
      <section style="max-width:920px;background:white;border:1px solid #e5e8ec;border-radius:12px;padding:24px;margin-top:20px">
        <h2 style="font-size:18px;margin:0 0 18px">Chiến dịch ({len(campaigns)})</h2>
        <div style="overflow-x:auto">
          <table style="width:100%;border-collapse:collapse;text-align:left">
            <thead><tr>
              <th scope="col" style="padding:12px;border-bottom:1px solid #e5e8ec">Nền tảng</th>
              <th scope="col" style="padding:12px;border-bottom:1px solid #e5e8ec">Tài khoản</th>
              <th scope="col" style="padding:12px;border-bottom:1px solid #e5e8ec">Mã chiến dịch</th>
              <th scope="col" style="padding:12px;border-bottom:1px solid #e5e8ec">Tên chiến dịch</th>
            </tr></thead>
            <tbody>{campaign_rows}</tbody>
          </table>
        </div>
      </section>
    </main>
  </div>
</body>
</html>""")

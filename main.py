import os
from collections import Counter
from decimal import Decimal
from html import escape
from pathlib import Path
from urllib.parse import quote_plus

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

load_dotenv(Path(__file__).with_name(".env"))
app = FastAPI(title="CampaignLens")


# Cả ba trang dùng chung màu sắc, khoảng cách và kiểu bảng.
STYLES = """
:root {
  --bg: #f5f7fb; --surface: #ffffff; --text: #192639;
  --muted: #637086; --border: #e5eaf2; --blue: #315bea;
  --soft-blue: #edf2ff;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
       font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
       font-size: 14px; line-height: 1.5; }
a { color: inherit; text-decoration: none; }
a:hover { color: var(--blue); }
svg { width: 18px; height: 18px; flex-shrink: 0; vertical-align: middle; }
.shell { display: flex; min-height: 100vh; }
.sidebar { width: 244px; flex-shrink: 0; background: var(--surface);
           border-right: 1px solid var(--border); padding: 30px 20px;
           display: flex; flex-direction: column; gap: 32px; }
.brand { display: flex; align-items: center; gap: 11px; padding: 0 6px; }
.logo { width: 36px; height: 36px; border-radius: 11px; color: white;
        background: var(--blue); display: grid; place-items: center; }
.brand strong { display: block; font-size: 18px; letter-spacing: -.5px; }
.brand small { display: block; font-size: 11px; color: var(--muted); }
.workspace { display: flex; align-items: center; gap: 10px;
             padding: 12px; border: 1px solid var(--border); border-radius: 10px; }
.workspace strong { display: block; font-size: 13px; }
.workspace small { display: block; color: var(--muted); font-size: 12px; }
.avatar { width: 36px; height: 36px; flex-shrink: 0; border-radius: 10px;
          background: var(--soft-blue); color: var(--blue); display: grid;
          place-items: center; font-size: 12px; font-weight: 700; }
.nav-label { padding: 0 12px; margin: 0 0 10px; font-size: 11px;
             font-weight: 650; letter-spacing: 1px; color: var(--muted); }
.nav-link { display: flex; align-items: center; gap: 11px; padding: 12px;
            border-radius: 9px; color: var(--muted); margin-bottom: 4px; }
.nav-link:hover { background: #f7f9fd; }
.nav-link.active { background: var(--soft-blue); color: var(--blue); font-weight: 650; }
.sidebar-foot { margin-top: auto; padding: 12px; font-size: 12px; color: var(--muted); }
.main { flex: 1; min-width: 0; }
.topbar { min-height: 74px; display: flex; align-items: center;
          justify-content: space-between; gap: 16px; padding: 18px 40px;
          background: var(--surface); border-bottom: 1px solid var(--border); }
.breadcrumb { display: flex; align-items: center; flex-wrap: wrap; gap: 10px;
              color: var(--muted); font-size: 13px; }
.breadcrumb strong { color: var(--text); font-weight: 550; }
.demo { display: inline-flex; align-items: center; gap: 7px;
        color: var(--muted); font-size: 12px; white-space: nowrap; }
.demo::before { content: ""; width: 6px; height: 6px;
                border-radius: 50%; background: var(--blue); }
.content { max-width: 1440px; margin: 0 auto; padding: 36px 40px 48px; }
.page-head { display: flex; align-items: center; justify-content: space-between;
             flex-wrap: wrap; gap: 18px; margin-bottom: 26px; }
h1 { font-size: 29px; line-height: 1.25; letter-spacing: -.8px; margin: 0 0 8px; }
.subtitle { margin: 0; color: var(--muted); }
.action { display: inline-flex; align-items: center; justify-content: center;
          gap: 9px; min-height: 42px; padding: 10px 15px; border-radius: 9px;
          font-size: 13px; font-weight: 600; background: var(--surface);
          border: 1px solid var(--border); white-space: nowrap; }
.action:hover { background: var(--soft-blue); }
.action.primary { background: var(--blue); border-color: var(--blue); color: white;
                  box-shadow: 0 3px 8px #315bea20; }
.action.primary:hover { background: #244bce; }
.tabs { display: flex; gap: 24px; margin: 0 0 26px; border-bottom: 1px solid var(--border); }
.tab { display: inline-flex; gap: 8px; align-items: center; padding: 0 0 13px;
       color: var(--muted); border-bottom: 2px solid transparent; font-weight: 550; }
.tab.active { border-bottom-color: var(--blue); color: var(--blue); }
.stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
         gap: 16px; margin-bottom: 26px; }
.stats.three { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.stat { background: var(--surface); border: 1px solid var(--border);
        border-radius: 12px; padding: 20px; box-shadow: 0 2px 4px #19263903; }
.stat-top { display: flex; align-items: center; justify-content: space-between;
            gap: 8px; color: var(--muted); font-size: 13px; }
.stat-icon { display: grid; place-items: center; width: 30px; height: 30px;
             color: var(--blue); background: var(--soft-blue); border-radius: 8px; }
.stat-value { display: block; margin: 14px 0 5px; font-size: 27px;
              line-height: 1.2; letter-spacing: -.7px; font-weight: 650;
              font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.stat-note { color: var(--muted); font-size: 12px; }
.stat.highlight { background: var(--soft-blue); border-color: #dce5ff; }
.panel { background: var(--surface); border: 1px solid var(--border);
         border-radius: 12px; margin-bottom: 22px; overflow: hidden; }
.panel-head { display: flex; align-items: center; justify-content: space-between;
              gap: 16px; padding: 23px 24px 19px; }
h2 { margin: 0 0 4px; font-size: 16px; font-weight: 650; }
.panel-head p { margin: 0; font-size: 12px; color: var(--muted); }
.count { padding: 4px 10px; border-radius: 6px; background: #f3f5f9;
         color: var(--muted); font-size: 12px; white-space: nowrap; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; text-align: left; white-space: nowrap; }
th { padding: 12px 24px; background: #fafbfe; border-block: 1px solid var(--border);
     font-size: 12px; font-weight: 550; color: var(--muted); }
td { padding: 17px 24px; border-bottom: 1px solid #eef1f6; font-size: 13px; }
tbody tr:last-child td { border-bottom: 0; }
tbody tr:hover { background: #fbfcff; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.name { font-weight: 600; }
.client-cell { display: flex; align-items: center; gap: 12px; }
.code { color: var(--muted); font-size: 12px; font-family: ui-monospace, monospace; }
.platform { display: inline-flex; align-items: center; gap: 8px; }
.platform-mark { display: grid; place-items: center; width: 27px; height: 27px;
                 border: 1px solid var(--border); border-radius: 7px;
                 color: var(--blue); font-size: 14px; font-weight: 650; }
.row-link { display: inline-flex; align-items: center; gap: 7px;
            color: var(--blue); font-size: 12px; font-weight: 600; }
.rate { padding: 4px 8px; border-radius: 6px; background: var(--soft-blue); color: #244bce; }
.empty { padding: 38px 24px; text-align: center; color: var(--muted); white-space: normal; }
.help { display: flex; align-items: flex-start; gap: 10px; color: var(--muted);
        font-size: 12px; padding: 0 4px; }
.help p { margin: 0; }
@media (max-width: 1200px) {
  .sidebar { width: 218px; padding-inline: 16px; }
  .topbar { padding-inline: 28px; }
  .content { padding: 30px 28px; }
  .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 760px) {
  .shell { display: block; }
  .sidebar { width: 100%; padding: 18px 20px 8px; gap: 16px;
             border-right: 0; border-bottom: 1px solid var(--border); }
  .workspace, .nav-label, .sidebar-foot, .brand small { display: none; }
  .sidebar nav { display: flex; flex-wrap: wrap; gap: 4px; }
  .nav-link { font-size: 12px; padding: 10px; }
  .topbar { min-height: 58px; padding: 14px 20px; }
  .content { padding: 26px 20px; }
  h1 { font-size: 25px; }
  .stats, .stats.three { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
  .stat { padding: 16px; }
  .stat-value { font-size: 23px; }
  .stat-top { align-items: flex-start; }
  .panel-head { padding: 18px; }
  th, td { padding-inline: 18px; }
}
@media (max-width: 420px) {
  .stats, .stats.three { grid-template-columns: 1fr; }
  .tabs { gap: 16px; font-size: 12px; }
  .demo { display: none; }
}
"""


def icon(name: str) -> str:
    paths = {
        "lens": '<circle cx="10" cy="10" r="6"/><path d="m15 15 5 5M7 11l3-3 3 2"/>',
        "clients": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M22 21v-2a4 4 0 0 0-3-3.87"/><circle cx="9" cy="7" r="4"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
        "accounts": '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="M3 9h18M7 14h4M7 17h6"/>',
        "report": '<path d="M3 3v18h18M8 16v-5M13 16V7M18 16v-8"/>',
        "right": '<path d="M5 12h14m-6-6 6 6-6 6"/>',
        "left": '<path d="M19 12H5m6-6-6 6 6 6"/>',
        "eye": '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
        "click": '<path d="m4 3 7 18 2-7 7-2L4 3ZM15 15l5 5"/>',
        "spend": '<rect x="3" y="5" width="18" height="15" rx="3"/><path d="M3 9h18M15 14h3"/>',
        "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7h.01"/>',
    }
    return (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true">{paths[name]}</svg>'
    )


def connect_to_database():
    return psycopg.connect(
        host="127.0.0.1",
        port=5433,
        dbname="adflow",
        user="adflow",
        password=os.environ["CAMPAIGNLENS_DB_PASSWORD"],
        connect_timeout=3,
    )


# Hàm này luôn trả về HTML đầy đủ, dùng chung cho cả ba trang.
def render_page(
    title,
    subtitle,
    content,
    *,
    active="clients",
    client_code="",
    client_name="",
    actions="",
    status_code=200,
) -> HTMLResponse:
    nav_items = [("clients", "/", "Khách hàng", "clients")]
    breadcrumb = '<a href="/">Workspace</a><span>/</span>'
    if client_code:
        query = quote_plus(client_code)
        nav_items += [
            (
                "accounts",
                f"/accounts?client_code={query}",
                "Tài khoản & chiến dịch",
                "accounts",
            ),
            (
                "performance",
                f"/performance?client_code={query}",
                "Báo cáo hiệu quả",
                "report",
            ),
        ]
        if active != "accounts":
            breadcrumb += (
                f'<a href="/accounts?client_code={query}">{escape(client_name or client_code)}</a>'
                "<span>/</span>"
            )
    breadcrumb += f"<strong>{escape(title)}</strong>"
    navigation = ""
    for key, href, label, symbol in nav_items:
        selected = ' aria-current="page"' if key == active else ""
        css_class = "nav-link active" if key == active else "nav-link"
        navigation += (
            f'<a class="{css_class}" href="{href}"{selected}>{icon(symbol)}{label}</a>'
        )

    return HTMLResponse(
        f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} | CampaignLens</title>
  <style>{STYLES}</style>
</head>
<body>
<div class="shell">
  <aside class="sidebar">
    <a class="brand" href="/">
      <span class="logo">{icon("lens")}</span>
      <span><strong>CampaignLens</strong><small>MARKETING ANALYTICS</small></span>
    </a>
    <div class="workspace">
      <span class="avatar" aria-hidden="true">CL</span>
      <span><strong>Agency workspace</strong><small>Quản lý khách hàng</small></span>
    </div>
    <nav aria-label="Điều hướng chính">
      <p class="nav-label">WORKSPACE</p>{navigation}
    </nav>
    <div class="sidebar-foot">CampaignLens · Bản demo</div>
  </aside>
  <main class="main">
    <div class="topbar">
      <nav class="breadcrumb" aria-label="Đường dẫn">{breadcrumb}</nav>
      <span class="demo">Dữ liệu mô phỏng</span>
    </div>
    <div class="content">
      <header class="page-head">
        <div><h1>{escape(title)}</h1><p class="subtitle">{escape(subtitle)}</p></div>
        {actions}
      </header>
      {content}
    </div>
  </main>
</div>
</body>
</html>""",
        status_code=status_code,
    )


def configuration_error() -> HTMLResponse:
    return render_page(
        "Thiếu cấu hình database",
        "Thêm CAMPAIGNLENS_DB_PASSWORD vào file .env.",
        "",
        status_code=503,
    )


def client_tabs(client_code: str, active: str) -> str:
    query = quote_plus(client_code)
    links = [
        ("accounts", "Tài khoản & chiến dịch", "accounts"),
        ("performance", "Hiệu quả chiến dịch", "report"),
    ]
    tabs = '<nav class="tabs" aria-label="Trang khách hàng">'
    for key, label, symbol in links:
        css_class = "tab active" if key == active else "tab"
        selected = ' aria-current="page"' if key == active else ""
        tabs += (
            f'<a class="{css_class}" href="/{key}?client_code={query}"{selected}>'
            f"{icon(symbol)}{label}</a>"
        )
    return tabs + "</nav>"


def stat(label: str, value: str, note: str, symbol: str, *, highlight=False) -> str:
    return (
        f'<div class="stat{" highlight" if highlight else ""}">'
        f'<div class="stat-top"><span>{escape(label)}</span>'
        f'<span class="stat-icon">{icon(symbol)}</span></div>'
        f'<strong class="stat-value">{escape(value)}</strong>'
        f'<span class="stat-note">{escape(note)}</span></div>'
    )


def platform_badge(platform: str) -> str:
    label, mark = {
        "google_ads": ("Google Ads", "G"),
        "meta_ads": ("Meta Ads", "∞"),
    }.get(platform, (platform, "•"))
    return (
        f'<span class="platform"><span class="platform-mark" aria-hidden="true">{mark}</span>'
        f"{escape(label)}</span>"
    )


def panel(title: str, subtitle: str, headers: str, rows: str, count: int) -> str:
    return f"""<section class="panel">
      <div class="panel-head"><div><h2>{escape(title)}</h2><p>{escape(subtitle)}</p></div>
        <span class="count">{count} dòng</span></div>
      <div class="table-wrap"><table>
        <thead><tr>{headers}</tr></thead><tbody>{rows}</tbody>
      </table></div>
    </section>"""


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    if not os.getenv("CAMPAIGNLENS_DB_PASSWORD"):
        return configuration_error()

    with connect_to_database() as connection:
        clients = connection.execute("""
            SELECT c.client_code, c.client_name, COUNT(a.ad_account_id) AS account_count
            FROM public.clients AS c
            LEFT JOIN public.ad_accounts AS a ON a.client_id = c.client_id
            GROUP BY c.client_id, c.client_code, c.client_name
            ORDER BY c.client_id
        """).fetchall()

    rows = ""
    for code, name, count in clients:
        href = f"/accounts?client_code={quote_plus(code)}"
        initials = "".join(word[0] for word in name.split()[:2]).upper()
        rows += f"""<tr>
          <td><a class="client-cell" href="{href}">
            <span class="avatar" aria-hidden="true">{escape(initials)}</span>
            <span class="name">{escape(name)}</span></a></td>
          <td><span class="code">{escape(code)}</span></td>
          <td class="num">{count}</td>
          <td class="num"><a class="row-link" href="{href}">Xem chi tiết {icon("right")}</a></td>
        </tr>"""
    rows = rows or '<tr><td class="empty" colspan="4">Chưa có khách hàng.</td></tr>'
    content = '<section class="stats three" aria-label="Tổng quan khách hàng">'
    content += stat("Khách hàng", f"{len(clients):,}", "Trong workspace", "clients")
    content += stat(
        "Tài khoản quảng cáo",
        f"{sum(c[2] for c in clients):,}",
        "Của tất cả khách hàng",
        "accounts",
    )
    content += stat(
        "Khách có tài khoản",
        f"{sum(c[2] > 0 for c in clients):,}",
        "Có tài khoản quảng cáo",
        "report",
    )
    content += "</section>" + panel(
        "Danh sách khách hàng",
        "Chọn khách hàng để xem tài khoản và báo cáo.",
        '<th scope="col">Khách hàng</th><th scope="col">Mã khách</th>'
        '<th scope="col" class="num">Tài khoản</th><th scope="col" class="num">Chi tiết</th>',
        rows,
        len(clients),
    )
    return render_page(
        "Khách hàng",
        "Theo dõi tài khoản và hiệu quả quảng cáo của từng khách hàng.",
        content,
    )


@app.get("/accounts", response_class=HTMLResponse)
def show_accounts(client_code: str) -> HTMLResponse:
    if not os.getenv("CAMPAIGNLENS_DB_PASSWORD"):
        return configuration_error()

    with connect_to_database() as connection:
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
        return render_page(
            "Không tìm thấy khách hàng",
            "Kiểm tra lại mã khách hàng.",
            "",
            status_code=404,
        )

    client_name = records[0][0]
    accounts = [
        (platform, external_id)
        for _, platform, external_id in records
        if platform is not None
    ]
    campaign_counts = Counter((p, account) for p, account, _, _ in campaigns)
    account_rows = (
        "".join(
            f'<tr><td>{platform_badge(platform)}</td><td><span class="code">{escape(external_id)}</span></td>'
            f'<td class="num">{campaign_counts[(platform, external_id)]}</td></tr>'
            for platform, external_id in accounts
        )
        or '<tr><td class="empty" colspan="3">Chưa có tài khoản quảng cáo.</td></tr>'
    )
    campaign_rows = (
        "".join(
            f'<tr><td class="name">{escape(name)}</td><td class="code">{escape(campaign_id)}</td>'
            f'<td>{platform_badge(platform)}</td><td class="code">{escape(account_id)}</td></tr>'
            for platform, account_id, campaign_id, name in campaigns
        )
        or '<tr><td class="empty" colspan="4">Chưa có chiến dịch.</td></tr>'
    )

    content = client_tabs(client_code, "accounts")
    content += '<section class="stats three" aria-label="Tổng quan khách hàng">'
    content += stat(
        "Tài khoản quảng cáo", f"{len(accounts):,}", "Thuộc khách hàng này", "accounts"
    )
    content += stat(
        "Chiến dịch", f"{len(campaigns):,}", "Trong các tài khoản quảng cáo", "report"
    )
    content += stat(
        "Nền tảng",
        f"{len({p for p, _ in accounts}):,}",
        "Có tài khoản quảng cáo",
        "clients",
    )
    content += "</section>"
    content += panel(
        "Tài khoản quảng cáo",
        "Mã tài khoản trên từng nền tảng.",
        '<th scope="col">Nền tảng</th><th scope="col">Mã tài khoản</th>'
        '<th scope="col" class="num">Chiến dịch</th>',
        account_rows,
        len(accounts),
    )
    content += panel(
        "Chiến dịch",
        "Các chiến dịch thuộc khách hàng này.",
        '<th scope="col">Tên chiến dịch</th><th scope="col">Mã chiến dịch</th>'
        '<th scope="col">Nền tảng</th><th scope="col">Tài khoản</th>',
        campaign_rows,
        len(campaigns),
    )
    actions = (
        f'<a class="action primary" href="/performance?client_code={quote_plus(client_code)}">'
        f"{icon('report')} Xem báo cáo CTR / CPC {icon('right')}</a>"
    )
    return render_page(
        client_name,
        f"Mã khách: {client_code}",
        content,
        active="accounts",
        client_code=client_code,
        client_name=client_name,
        actions=actions,
    )


@app.get("/performance", response_class=HTMLResponse)
def show_performance(client_code: str) -> HTMLResponse:
    if not os.getenv("CAMPAIGNLENS_DB_PASSWORD"):
        return configuration_error()

    with connect_to_database() as connection:
        client = connection.execute(
            "SELECT client_name FROM public.clients WHERE client_code = %s",
            (client_code,),
        ).fetchone()
        if client is None:
            return render_page(
                "Không tìm thấy khách hàng",
                "Kiểm tra lại mã khách hàng.",
                "",
                status_code=404,
            )
        records = connection.execute(
            """
            SELECT g.campaign_name, a.platform, m.metric_date,
                   m.impressions, m.clicks, m.spend, m.currency_code,
                   ROUND(100.0 * m.clicks / NULLIF(m.impressions, 0), 2) AS ctr_percent,
                   ROUND(m.spend / NULLIF(m.clicks, 0), 2) AS cpc
            FROM public.campaign_daily_metrics AS m
            JOIN public.campaigns AS g ON g.campaign_id = m.campaign_id
            JOIN public.ad_accounts AS a ON a.ad_account_id = g.ad_account_id
            JOIN public.clients AS c ON c.client_id = a.client_id
            WHERE c.client_code = %s
            ORDER BY m.metric_date DESC, g.campaign_name
        """,
            (client_code,),
        ).fetchall()

    impressions = sum(row[3] for row in records)
    clicks = sum(row[4] for row in records)
    ctr = f"{Decimal(100) * clicks / impressions:.2f}%" if impressions else "—"
    currencies = {row[6] for row in records}
    if len(currencies) == 1:
        spend = f"{sum(row[5] for row in records):,.2f} {next(iter(currencies))}"
        spend_note = "Tổng chi phí trong dữ liệu báo cáo"
    else:
        spend = "—" if not records else "Nhiều tiền tệ"
        spend_note = "Chưa có dữ liệu" if not records else "Xem chi phí từng dòng"
    if records:
        days = [row[2] for row in records]
        period = f"Dữ liệu từ {min(days):%d/%m/%Y} đến {max(days):%d/%m/%Y}"
    else:
        period = "Chưa có số liệu quảng cáo theo ngày."

    rows = ""
    for name, platform, day, views, hits, cost, currency, row_ctr, cpc in records:
        ctr_text = "—" if row_ctr is None else f"{row_ctr:.2f}%"
        cpc_text = "—" if cpc is None else f"{cpc:.2f} {currency}"
        rows += f"""<tr>
          <td class="name">{escape(name)}</td><td>{platform_badge(platform)}</td>
          <td>{day:%d/%m/%Y}</td><td class="num">{views:,}</td><td class="num">{hits:,}</td>
          <td class="num">{cost:,.2f} {escape(currency)}</td>
          <td class="num"><span class="rate">{ctr_text}</span></td>
          <td class="num">{escape(cpc_text)}</td>
        </tr>"""
    rows = (
        rows
        or '<tr><td class="empty" colspan="8">Chưa có số liệu theo ngày cho khách hàng này.</td></tr>'
    )
    content = client_tabs(client_code, "performance")
    content += '<section class="stats" aria-label="Tổng quan hiệu quả">'
    content += stat("Tổng chi phí", spend, spend_note, "spend")
    content += stat(
        "Lượt hiển thị",
        f"{impressions:,}",
        "Tổng số lần quảng cáo được hiển thị",
        "eye",
    )
    content += stat(
        "Lượt nhấp", f"{clicks:,}", "Tổng số lượt nhấp vào quảng cáo", "click"
    )
    content += stat(
        "CTR tổng hợp",
        ctr,
        "Tổng lượt nhấp / tổng lượt hiển thị",
        "report",
        highlight=True,
    )
    content += "</section>"
    content += panel(
        "Hiệu quả theo ngày",
        period,
        '<th scope="col">Chiến dịch</th><th scope="col">Nền tảng</th><th scope="col">Ngày</th>'
        '<th scope="col" class="num">Hiển thị</th><th scope="col" class="num">Nhấp</th>'
        '<th scope="col" class="num">Chi phí</th><th scope="col" class="num">CTR</th>'
        '<th scope="col" class="num">CPC</th>',
        rows,
        len(records),
    )
    content += (
        f'<div class="help">{icon("info")}<p>CTR: tỷ lệ nhấp = lượt nhấp / lượt hiển thị × 100. '
        "CPC: chi phí trung bình mỗi lượt nhấp = chi phí / lượt nhấp. "
        "Dấu — nghĩa là chưa đủ dữ liệu để tính.</p></div>"
    )
    actions = (
        f'<a class="action" href="/accounts?client_code={quote_plus(client_code)}">'
        f"{icon('left')} Tài khoản & chiến dịch</a>"
    )
    return render_page(
        "Báo cáo hiệu quả",
        f"{client[0]} · {client_code}",
        content,
        active="performance",
        client_code=client_code,
        client_name=client[0],
        actions=actions,
    )

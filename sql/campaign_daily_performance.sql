SELECT c.client_code, g.campaign_name, a.platform, m.metric_date,
       m.impressions, m.clicks, m.spend, m.currency_code,
       ROUND(100.0 * m.clicks / NULLIF(m.impressions, 0), 2) AS ctr_percent,
       ROUND(m.spend / NULLIF(m.clicks, 0), 2) AS cpc
FROM public.campaign_daily_metrics AS m
JOIN public.campaigns AS g ON g.campaign_id = m.campaign_id
JOIN public.ad_accounts AS a ON a.ad_account_id = g.ad_account_id
JOIN public.clients AS c ON c.client_id = a.client_id
WHERE c.client_code = 'NORTHSTAR'
ORDER BY m.metric_date DESC, g.campaign_name;
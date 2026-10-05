SELECT
    c.client_id,
    c.client_code,
    c.client_name,
    COUNT(a.ad_account_id) AS account_count
FROM public.clients AS c
LEFT JOIN public.ad_accounts AS a
    ON a.client_id = c.client_id
GROUP BY c.client_id, c.client_code, c.client_name
ORDER BY c.client_id;
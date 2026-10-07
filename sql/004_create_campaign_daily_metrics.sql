CREATE TABLE public.campaign_daily_metrics (
    campaign_id BIGINT NOT NULL REFERENCES public.campaigns(campaign_id),
    metric_date DATE NOT NULL,
    impressions BIGINT NOT NULL CHECK (impressions >= 0),
    clicks BIGINT NOT NULL CHECK (clicks >= 0),
    spend NUMERIC(14, 2) NOT NULL CHECK (spend >= 0),
    currency_code VARCHAR(3) NOT NULL,
    CONSTRAINT campaign_daily_metrics_pkey
        PRIMARY KEY (campaign_id, metric_date)
);
CREATE TABLE public.campaigns (
    campaign_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ad_account_id BIGINT NOT NULL REFERENCES public.ad_accounts(ad_account_id),
    external_campaign_id VARCHAR(80) NOT NULL,
    campaign_name VARCHAR(160) NOT NULL,
    CONSTRAINT campaigns_account_external_key
        UNIQUE (ad_account_id, external_campaign_id)
);  
CREATE TABLE public.ad_accounts (
    ad_account_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_id BIGINT NOT NULL REFERENCES public.clients(client_id),
    platform VARCHAR(20) NOT NULL,
    external_account_id VARCHAR(80) NOT NULL,
    CONSTRAINT ad_accounts_platform_external_key UNIQUE (platform, external_account_id)
);
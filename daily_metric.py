from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DailyMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    campaign_id: int = Field(strict=True, gt=0)
    metric_date: date
    impressions: int = Field(strict=True, ge=0)
    clicks: int = Field(strict=True, ge=0)
    spend: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    currency_code: str = Field(pattern=r"^[A-Z]{3}$")

from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class FinancialYearInput(BaseModel):
    year: int = Field(ge=1900, le=2200)
    kind: Literal["actual", "forecast"]
    revenue: Decimal | None = None
    ebitda: Decimal | None = None
    operating_result: Decimal | None = None
    net_result: Decimal | None = None
    depreciation: Decimal | None = None
    cash_flow: Decimal | None = None
    equity: Decimal | None = None
    gross_debt: Decimal | None = None
    gross_cash: Decimal | None = None
    factoring: Decimal | None = None
    total_assets: Decimal | None = None
    capex: Decimal | None = None
    debt_repayments: Decimal | None = None
    notes: str | None = Field(default=None, max_length=2000)


class FinancialYearRead(FinancialYearInput):
    id: int
    company_id: int
    model_config = ConfigDict(from_attributes=True)

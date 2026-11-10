from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, UniqueConstraint
from app.database import Base


class FinancialYear(Base):
    """One company-wide financial snapshot for an actual or forecast year."""
    __tablename__ = "financial_years"
    __table_args__ = (UniqueConstraint("company_id", "year", "kind", name="uq_financial_year_company_year_kind"),)

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    kind = Column(String(8), nullable=False)  # actual or forecast
    revenue = Column(Numeric(18, 2))
    ebitda = Column(Numeric(18, 2))  # EBE
    operating_result = Column(Numeric(18, 2))  # REX
    net_result = Column(Numeric(18, 2))
    depreciation = Column(Numeric(18, 2))
    cash_flow = Column(Numeric(18, 2))  # CAF, independently supplied
    equity = Column(Numeric(18, 2))
    gross_debt = Column(Numeric(18, 2))
    gross_cash = Column(Numeric(18, 2))
    factoring = Column(Numeric(18, 2))
    total_assets = Column(Numeric(18, 2))
    capex = Column(Numeric(18, 2))
    debt_repayments = Column(Numeric(18, 2))
    notes = Column(String(2000))

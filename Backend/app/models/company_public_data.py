from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class CompanyPublicData(Base):
    """Official public data about a company, produced by the data pipeline.

    Linked to `companies` through the SIREN (not a foreign key): the pipeline can
    enrich a SIREN before or after the consultant creates the company in the app.
    """
    __tablename__ = "company_public_data"

    id = Column(Integer, primary_key=True)
    siren = Column(String(9), nullable=False, unique=True, index=True)

    legal_name = Column(String, nullable=True)            # empty for sole traders (personal data)
    legal_form_code = Column(String(4), nullable=True)    # INSEE "catégorie juridique"
    naf_code = Column(String(6), nullable=True, index=True)
    naf_section = Column(String(1), nullable=True)
    headcount_code = Column(String(2), nullable=True)
    headcount_label = Column(String, nullable=True)
    company_category = Column(String(3), nullable=True)  # PME, ETI or GE
    creation_date = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=True)

    head_office_address = Column(String, nullable=True)   # empty for sole traders (personal data)
    postal_code = Column(String(5), nullable=True)
    city = Column(String, nullable=True)

    website = Column(String, nullable=True)
    website_description = Column(Text, nullable=True)

    sector_active_companies = Column(Integer, nullable=True)  # active companies with the same NAF code in France

    sources = Column(String, nullable=False)              # e.g. "file,api,sirene,scraping"
    collected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

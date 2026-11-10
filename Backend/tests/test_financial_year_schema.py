from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.financial_year import FinancialYearInput


@pytest.mark.parametrize("kind", ["actual", "forecast"])
def test_valid_financial_year(kind):
    data = FinancialYearInput(
        year=2026,
        kind=kind,
        revenue="2400000.50",
    )

    assert data.year == 2026
    assert data.kind == kind
    assert data.revenue == Decimal("2400000.50")
    assert data.notes is None


@pytest.mark.parametrize(
    "changes",
    [
        {"year": 1899},
        {"year": 2201},
        {"kind": "unknown"},
        {"notes": "x" * 2001},
    ],
)
def test_invalid_financial_data_is_rejected(changes):
    payload = {
        "year": 2026,
        "kind": "actual",
        **changes,
    }

    with pytest.raises(ValidationError):
        FinancialYearInput(**payload)


def test_zero_revenue_is_preserved():
    data = FinancialYearInput(
        year=2026,
        kind="actual",
        revenue="0",
    )

    assert data.revenue == Decimal("0")
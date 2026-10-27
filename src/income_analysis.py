"""Part 1 - Income statement analysis (vertical, horizontal, margins)."""
import numpy as np
import pandas as pd

from .models import CompanyData
from .schema import KINDS, LABELS
from .utils import safe_div

INCOME_ROWS = [
    "revenue", "cogs", "gross_profit", "sga", "other_opex", "ebit", "da", "ebitda",
    "interest_expense", "other_income", "pretax", "tax", "net_income",
]

MARGIN_META = {
    "gross_margin": "Gross Margin",
    "operating_margin": "Operating (EBIT) Margin",
    "ebitda_margin": "EBITDA Margin",
    "pretax_margin": "Pre-tax Margin",
    "net_margin": "Net Margin",
    "effective_tax_rate": "Effective Tax Rate",
}
LABELS.update(MARGIN_META)
KINDS.update({k: "pct" for k in MARGIN_META})


def income_statement(c: CompanyData) -> pd.DataFrame:
    """Full income statement (keys x years) with the calculated subtotals."""
    i = c.income
    rev, cogs = i.loc["revenue"], i.loc["cogs"]
    gross = rev - cogs
    ebit = gross - i.loc["sga"] - i.loc["other_opex"]
    ebitda = ebit + i.loc["da"]
    pretax = ebit - i.loc["interest_expense"] + i.loc["other_income"]
    net = pretax - i.loc["tax"]
    rows = {
        "revenue": rev, "cogs": cogs, "gross_profit": gross,
        "sga": i.loc["sga"], "other_opex": i.loc["other_opex"], "ebit": ebit,
        "da": i.loc["da"], "ebitda": ebitda,
        "interest_expense": i.loc["interest_expense"], "other_income": i.loc["other_income"],
        "pretax": pretax, "tax": i.loc["tax"], "net_income": net,
    }
    return pd.DataFrame(rows).T.loc[INCOME_ROWS]


def vertical_analysis(df: pd.DataFrame, base_row: str = "revenue") -> pd.DataFrame:
    """Every line as a fraction of the base row (revenue by default)."""
    base = df.loc[base_row]
    return df.div(base.where(base != 0), axis=1)


def growth(df: pd.DataFrame) -> pd.DataFrame:
    """Year-over-year change as a fraction. Uses |previous| so that the sign
    stays meaningful when the base is negative; NaN when the base is zero."""
    prev = df.shift(1, axis=1)
    return (df - prev) / prev.abs().where(prev.abs() > 0)


def cagr(df: pd.DataFrame) -> pd.Series:
    yrs = list(df.columns)
    n = yrs[-1] - yrs[0]
    if n <= 0:
        return pd.Series(np.nan, index=df.index)
    first, last = df.iloc[:, 0], df.iloc[:, -1]
    ok = (first > 0) & (last > 0)
    out = (last / first.where(ok)) ** (1 / n) - 1
    return out.where(ok)


def margins(c: CompanyData) -> pd.DataFrame:
    inc = income_statement(c)
    rev = inc.loc["revenue"]
    rows = {
        "gross_margin": safe_div(inc.loc["gross_profit"], rev),
        "operating_margin": safe_div(inc.loc["ebit"], rev),
        "ebitda_margin": safe_div(inc.loc["ebitda"], rev),
        "pretax_margin": safe_div(inc.loc["pretax"], rev),
        "net_margin": safe_div(inc.loc["net_income"], rev),
        "effective_tax_rate": safe_div(inc.loc["tax"], inc.loc["pretax"]),
    }
    return pd.DataFrame(rows).T

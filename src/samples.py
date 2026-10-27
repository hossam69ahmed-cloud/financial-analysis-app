"""Illustrative demo companies (fictional numbers) used for the template and quick tests."""
import pandas as pd

from .models import CompanyData
from .schema import BALANCE_INPUTS, INCOME_INPUTS


def _build(name, ticker, sector, years, p, tax_rate, re_open) -> CompanyData:
    n = len(years)
    inc = pd.DataFrame(index=[k for k, _ in INCOME_INPUTS], columns=years, dtype=float)
    for k in ["revenue", "cogs", "sga", "other_opex", "interest_expense", "other_income", "da", "dividends", "shares"]:
        inc.loc[k] = p[k]
    ebit = pd.Series(p["revenue"], index=years) - p["cogs"] - p["sga"] - p["other_opex"]
    pretax = ebit - p["interest_expense"] + p["other_income"]
    inc.loc["tax"] = (pretax * tax_rate).round(1)
    ni = pretax - inc.loc["tax"]

    bal = pd.DataFrame(index=[k for k, _ in BALANCE_INPUTS], columns=years, dtype=float)
    for k in ["st_investments", "receivables", "inventory", "other_current_assets", "ppe", "intangibles",
              "other_noncurrent_assets", "payables", "st_debt", "accrued_liabilities", "lt_debt",
              "other_noncurrent_liabilities", "share_capital"]:
        bal.loc[k] = p[k]
    # Retained earnings roll forward: RE(t) = RE(t-1) + NI - dividends; cash is the balancing item.
    re = [re_open]
    for t in range(1, n):
        re.append(round(re[-1] + ni.iloc[t] - p["dividends"][t], 1))
    bal.loc["retained_earnings"] = re
    noncash = (bal.loc[["st_investments", "receivables", "inventory", "other_current_assets", "ppe",
                        "intangibles", "other_noncurrent_assets"]].sum())
    liab_eq = (bal.loc[["payables", "st_debt", "accrued_liabilities", "lt_debt", "other_noncurrent_liabilities",
                        "share_capital", "retained_earnings"]].sum())
    bal.loc["cash"] = (liab_eq - noncash).round(1)
    return CompanyData(name, inc, bal, ticker=ticker, currency="EGP", unit="Millions", sector=sector)


def nile_foods(name="Nile Foods") -> CompanyData:
    p = dict(
        revenue=[1200, 1350, 1500, 1680], cogs=[780, 880, 975, 1085], sga=[180, 200, 220, 245],
        other_opex=[20, 22, 25, 27], interest_expense=[30, 32, 35, 33], other_income=[5, 4, 6, 8],
        da=[45, 50, 55, 60], dividends=[30, 35, 40, 45], shares=[100] * 4,
        st_investments=[20, 20, 25, 30], receivables=[150, 170, 190, 210], inventory=[200, 225, 250, 275],
        other_current_assets=[30, 32, 35, 38], ppe=[600, 640, 690, 730], intangibles=[80] * 4,
        other_noncurrent_assets=[20, 22, 25, 28], payables=[130, 145, 160, 175], st_debt=[90, 85, 80, 75],
        accrued_liabilities=[60, 66, 72, 80], lt_debt=[400, 380, 360, 330],
        other_noncurrent_liabilities=[30] * 4, share_capital=[300] * 4,
    )
    return _build(name, "NILF", "Consumer Staples", [2021, 2022, 2023, 2024], p, 0.225, 210)


def delta_tech() -> CompanyData:
    p = dict(
        revenue=[800, 1000, 1300, 1650], cogs=[320, 390, 500, 620], sga=[220, 270, 340, 420],
        other_opex=[60, 75, 95, 120], interest_expense=[10, 12, 15, 14], other_income=[3, 4, 8, 12],
        da=[35, 45, 60, 80], dividends=[0, 0, 20, 30], shares=[50, 50, 52, 52],
        st_investments=[60, 90, 140, 190], receivables=[110, 150, 200, 260], inventory=[60, 75, 95, 120],
        other_current_assets=[20, 28, 35, 45], ppe=[250, 330, 430, 540], intangibles=[150, 150, 200, 200],
        other_noncurrent_assets=[15, 20, 25, 30], payables=[70, 85, 110, 140], st_debt=[20, 30, 30, 25],
        accrued_liabilities=[50, 65, 85, 110], lt_debt=[120, 150, 160, 140],
        other_noncurrent_liabilities=[20, 25, 30, 35], share_capital=[350, 350, 380, 380],
    )
    return _build("Delta Tech", "DLTA", "Technology", [2021, 2022, 2023, 2024], p, 0.20, 180)


def example_company() -> CompanyData:
    """Pre-filled values for the downloadable template."""
    c = nile_foods("Example Company (replace with your company)")
    c.ticker = "EXMP"
    return c


def sample_companies() -> list[CompanyData]:
    return [nile_foods(), delta_tech()]

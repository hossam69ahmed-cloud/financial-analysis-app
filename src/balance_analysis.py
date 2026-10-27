"""Part 2 - Balance sheet analysis (vertical, horizontal, structure)."""
import pandas as pd

from .models import CompanyData
from .schema import BALANCE_INPUTS, KINDS, LABELS
from .utils import safe_div

BALANCE_ROWS = [
    "cash", "st_investments", "receivables", "inventory", "other_current_assets",
    "total_current_assets", "ppe", "intangibles", "other_noncurrent_assets", "total_assets",
    "payables", "st_debt", "accrued_liabilities", "total_current_liabilities",
    "lt_debt", "other_noncurrent_liabilities", "total_liabilities",
    "share_capital", "retained_earnings", "total_equity", "total_liab_equity",
]

STRUCTURE_META = {
    "working_capital": ("Working Capital", "amount"),
    "total_debt": ("Total Debt", "amount"),
    "net_debt": ("Net Debt (Debt - Cash & ST Inv.)", "amount"),
    "invested_capital": ("Invested Capital", "amount"),
    "debt_to_equity": ("Debt to Equity", "x"),
    "debt_ratio": ("Total Liabilities / Total Assets", "pct"),
    "equity_ratio": ("Equity / Total Assets", "pct"),
    "current_assets_share": ("Current Assets / Total Assets", "pct"),
}
LABELS.update({k: v[0] for k, v in STRUCTURE_META.items()})
KINDS.update({k: v[1] for k, v in STRUCTURE_META.items()})


def balance_sheet(c: CompanyData) -> pd.DataFrame:
    """Full balance sheet (keys x years) with subtotals."""
    b = c.balance
    g = lambda k: b.loc[k]  # noqa: E731
    tca = g("cash") + g("st_investments") + g("receivables") + g("inventory") + g("other_current_assets")
    ta = tca + g("ppe") + g("intangibles") + g("other_noncurrent_assets")
    tcl = g("payables") + g("st_debt") + g("accrued_liabilities")
    tl = tcl + g("lt_debt") + g("other_noncurrent_liabilities")
    te = g("share_capital") + g("retained_earnings")
    rows = {k: g(k) for k, _ in BALANCE_INPUTS}
    rows.update(
        total_current_assets=tca, total_assets=ta,
        total_current_liabilities=tcl, total_liabilities=tl,
        total_equity=te, total_liab_equity=tl + te,
    )
    return pd.DataFrame(rows).T.loc[BALANCE_ROWS]


def balance_check(c: CompanyData) -> pd.Series:
    """Assets - (Liabilities + Equity) per year; should be ~0."""
    bs = balance_sheet(c)
    return bs.loc["total_assets"] - bs.loc["total_liab_equity"]


def structure_metrics(c: CompanyData) -> pd.DataFrame:
    bs = balance_sheet(c)
    debt = bs.loc["st_debt"] + bs.loc["lt_debt"]
    cash = bs.loc["cash"] + bs.loc["st_investments"]
    te, ta = bs.loc["total_equity"], bs.loc["total_assets"]
    rows = {
        "working_capital": bs.loc["total_current_assets"] - bs.loc["total_current_liabilities"],
        "total_debt": debt,
        "net_debt": debt - cash,
        "invested_capital": debt + te - cash,
        "debt_to_equity": safe_div(debt, te),
        "debt_ratio": safe_div(bs.loc["total_liabilities"], ta),
        "equity_ratio": safe_div(te, ta),
        "current_assets_share": safe_div(bs.loc["total_current_assets"], ta),
    }
    return pd.DataFrame(rows).T.loc[list(STRUCTURE_META)]

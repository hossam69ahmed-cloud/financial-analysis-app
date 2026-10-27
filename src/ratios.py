"""Part 4 - Financial ratios (core set; market ratios come with part 5)."""
import pandas as pd

from .balance_analysis import balance_sheet
from .income_analysis import income_statement, margins
from .models import CompanyData
from .schema import KINDS, LABELS
from .utils import safe_div

# key: (group, label, display kind, higher_is_better)  None = not directional
RATIO_META = {
    # Liquidity
    "current_ratio": ("Liquidity", "Current Ratio", "x", True),
    "quick_ratio": ("Liquidity", "Quick Ratio", "x", True),
    "cash_ratio": ("Liquidity", "Cash Ratio", "x", True),
    # Profitability
    "gross_margin": ("Profitability", "Gross Margin", "pct", True),
    "operating_margin": ("Profitability", "Operating (EBIT) Margin", "pct", True),
    "ebitda_margin": ("Profitability", "EBITDA Margin", "pct", True),
    "net_margin": ("Profitability", "Net Margin", "pct", True),
    "roa": ("Profitability", "Return on Assets (ROA)", "pct", True),
    "roe": ("Profitability", "Return on Equity (ROE)", "pct", True),
    "roic": ("Profitability", "Return on Invested Capital (ROIC)", "pct", True),
    # Leverage
    "debt_to_equity": ("Leverage", "Debt to Equity", "x", False),
    "debt_ratio": ("Leverage", "Total Liabilities / Total Assets", "pct", False),
    "equity_multiplier": ("Leverage", "Equity Multiplier", "x", None),
    "interest_coverage": ("Leverage", "Interest Coverage (EBIT / Interest)", "x", True),
    "net_debt_to_ebitda": ("Leverage", "Net Debt / EBITDA", "x", False),
    # Efficiency
    "asset_turnover": ("Efficiency", "Total Asset Turnover", "x", True),
    "fixed_asset_turnover": ("Efficiency", "Fixed Asset Turnover", "x", True),
    "inventory_turnover": ("Efficiency", "Inventory Turnover", "x", True),
    "receivables_turnover": ("Efficiency", "Receivables Turnover", "x", True),
    "payables_turnover": ("Efficiency", "Payables Turnover", "x", None),
    "dio": ("Efficiency", "Days Inventory Outstanding (DIO)", "days", False),
    "dso": ("Efficiency", "Days Sales Outstanding (DSO)", "days", False),
    "dpo": ("Efficiency", "Days Payables Outstanding (DPO)", "days", None),
    "ccc": ("Efficiency", "Cash Conversion Cycle (days)", "days", False),
    # Per share
    "eps": ("Per Share & Dividends", "Earnings per Share (EPS)", "num2", True),
    "bvps": ("Per Share & Dividends", "Book Value per Share", "num2", True),
    "dps": ("Per Share & Dividends", "Dividend per Share", "num2", True),
    "payout_ratio": ("Per Share & Dividends", "Dividend Payout Ratio", "pct", None),
}
GROUP_ORDER = ["Liquidity", "Profitability", "Leverage", "Efficiency", "Per Share & Dividends"]

LABELS.update({k: v[1] for k, v in RATIO_META.items()})
KINDS.update({k: v[2] for k, v in RATIO_META.items()})


def compute_ratios(c: CompanyData) -> pd.DataFrame:
    """All ratios (keys x years). Balance-sheet items use year-end balances."""
    inc, bs, mar = income_statement(c), balance_sheet(c), margins(c)
    rev, cogs, ebit, ebitda = inc.loc["revenue"], inc.loc["cogs"], inc.loc["ebit"], inc.loc["ebitda"]
    ni, interest = inc.loc["net_income"], inc.loc["interest_expense"]
    ta, te, tl = bs.loc["total_assets"], bs.loc["total_equity"], bs.loc["total_liabilities"]
    tca, tcl = bs.loc["total_current_assets"], bs.loc["total_current_liabilities"]
    cash = bs.loc["cash"] + bs.loc["st_investments"]
    debt = bs.loc["st_debt"] + bs.loc["lt_debt"]
    invested = debt + te - cash
    tax_rate = safe_div(inc.loc["tax"], inc.loc["pretax"]).clip(0, 1).fillna(0)
    shares = c.income.loc["shares"]
    dividends = c.income.loc["dividends"]

    inv_turn = safe_div(cogs, bs.loc["inventory"])
    rec_turn = safe_div(rev, bs.loc["receivables"])
    pay_turn = safe_div(cogs, bs.loc["payables"])
    dio = safe_div(bs.loc["inventory"], cogs) * 365
    dso = safe_div(bs.loc["receivables"], rev) * 365
    dpo = safe_div(bs.loc["payables"], cogs) * 365

    r = {
        "current_ratio": safe_div(tca, tcl),
        "quick_ratio": safe_div(bs.loc["cash"] + bs.loc["st_investments"] + bs.loc["receivables"], tcl),
        "cash_ratio": safe_div(cash, tcl),
        "gross_margin": mar.loc["gross_margin"],
        "operating_margin": mar.loc["operating_margin"],
        "ebitda_margin": mar.loc["ebitda_margin"],
        "net_margin": mar.loc["net_margin"],
        "roa": safe_div(ni, ta),
        "roe": safe_div(ni, te),
        "roic": safe_div(ebit * (1 - tax_rate), invested),
        "debt_to_equity": safe_div(debt, te),
        "debt_ratio": safe_div(tl, ta),
        "equity_multiplier": safe_div(ta, te),
        "interest_coverage": safe_div(ebit, interest),
        "net_debt_to_ebitda": safe_div(debt - cash, ebitda),
        "asset_turnover": safe_div(rev, ta),
        "fixed_asset_turnover": safe_div(rev, bs.loc["ppe"]),
        "inventory_turnover": inv_turn,
        "receivables_turnover": rec_turn,
        "payables_turnover": pay_turn,
        "dio": dio, "dso": dso, "dpo": dpo, "ccc": dio + dso - dpo,
        "eps": safe_div(ni, shares),
        "bvps": safe_div(te, shares),
        "dps": safe_div(dividends, shares),
        "payout_ratio": safe_div(dividends, ni),
    }
    return pd.DataFrame(r).T.loc[list(RATIO_META)]

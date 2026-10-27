"""Side-by-side comparison of several companies."""
import numpy as np
import pandas as pd

from .balance_analysis import balance_sheet
from .income_analysis import growth, income_statement
from .models import CompanyData
from .ratios import RATIO_META, compute_ratios
from .schema import KINDS, LABELS

LABELS.update({"revenue_growth": "Revenue Growth", "net_income_growth": "Net Income Growth"})
KINDS.update({"revenue_growth": "pct", "net_income_growth": "pct"})

METRIC_GROUPS = {
    "Scale": ["revenue", "ebitda", "net_income", "total_assets", "total_equity"],
    "Growth": ["revenue_growth", "net_income_growth"],
    "Profitability": ["gross_margin", "operating_margin", "ebitda_margin", "net_margin", "roa", "roe", "roic"],
    "Liquidity": ["current_ratio", "quick_ratio", "cash_ratio"],
    "Leverage": ["debt_to_equity", "debt_ratio", "interest_coverage", "net_debt_to_ebitda"],
    "Efficiency": ["asset_turnover", "dso", "dio", "dpo", "ccc"],
}
ALL_METRICS = [k for keys in METRIC_GROUPS.values() for k in keys]
GROUP_OF = {k: g for g, keys in METRIC_GROUPS.items() for k in keys}

HIGHER_BETTER = {k: v[3] for k, v in RATIO_META.items()}
HIGHER_BETTER.update({k: True for k in ["revenue", "ebitda", "net_income", "total_assets", "total_equity",
                                         "revenue_growth", "net_income_growth"]})


def metric_frame(c: CompanyData) -> pd.DataFrame:
    """All comparable metrics of one company (keys x years)."""
    inc, bs = income_statement(c), balance_sheet(c)
    g = growth(inc)
    base = pd.DataFrame({
        "revenue": inc.loc["revenue"], "ebitda": inc.loc["ebitda"], "net_income": inc.loc["net_income"],
        "total_assets": bs.loc["total_assets"], "total_equity": bs.loc["total_equity"],
        "revenue_growth": g.loc["revenue"], "net_income_growth": g.loc["net_income"],
    }).T
    return pd.concat([base, compute_ratios(c)])


def common_years(companies: dict[str, CompanyData]) -> list[int]:
    sets = [set(c.years) for c in companies.values()]
    return sorted(set.intersection(*sets)) if sets else []


def all_years(companies: dict[str, CompanyData]) -> list[int]:
    return sorted({y for c in companies.values() for y in c.years})


def comparison_table(companies: dict[str, CompanyData], year: int):
    """Returns (table, best) - table: metric x company for one year,
    best: Series with the name of the best company per metric ('' if n/a)."""
    frames = {n: metric_frame(c) for n, c in companies.items()}
    data = {
        n: [f.loc[k, year] if year in f.columns else np.nan for k in ALL_METRICS]
        for n, f in frames.items()
    }
    table = pd.DataFrame(data, index=ALL_METRICS).astype(float)
    best = {}
    for k, row in table.iterrows():
        hb = HIGHER_BETTER.get(k)
        best[k] = "" if hb is None or row.notna().sum() < 2 else (row.idxmax() if hb else row.idxmin())
    return table, pd.Series(best)


def metric_trend(companies: dict[str, CompanyData], key: str) -> pd.DataFrame:
    """years x company for one metric."""
    out = pd.concat({n: metric_frame(c).loc[key] for n, c in companies.items()}, axis=1)
    return out.sort_index()

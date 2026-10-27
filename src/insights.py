"""Short auto-generated observations used in the reports."""
import pandas as pd

from .balance_analysis import balance_check
from .income_analysis import cagr, income_statement, margins
from .models import CompanyData
from .ratios import compute_ratios
from .utils import fmt_value


def key_takeaways(c: CompanyData) -> list[str]:
    inc, mar, rat = income_statement(c), margins(c), compute_ratios(c)
    y0, y1 = c.years[0], c.years[-1]
    out: list[str] = []

    if y1 > y0:
        cg = cagr(inc).loc["revenue"]
        if pd.notna(cg):
            out.append(
                f"Revenue moved from {fmt_value(inc.loc['revenue', y0])} in {y0} to "
                f"{fmt_value(inc.loc['revenue', y1])} in {y1} (CAGR {cg:.1%})."
            )
        for key, name in [("gross_margin", "Gross margin"), ("net_margin", "Net margin")]:
            a, b = mar.loc[key, y0], mar.loc[key, y1]
            if pd.notna(a) and pd.notna(b):
                d = (b - a) * 100
                word = "expanded" if d > 0.5 else "contracted" if d < -0.5 else "was broadly stable"
                out.append(f"{name} {word}: {a:.1%} in {y0} vs {b:.1%} in {y1} ({d:+.1f} pp).")

    cr = rat.loc["current_ratio", y1]
    if pd.notna(cr):
        tone = ("below 1.0x - possible short-term liquidity pressure" if cr < 1
                else "comfortable" if cr >= 2 else "adequate")
        out.append(f"Current ratio in {y1} is {cr:.2f}x ({tone}).")
    de = rat.loc["debt_to_equity", y1]
    if pd.notna(de):
        out.append(f"Debt to equity in {y1} is {de:.2f}x.")
    ic = rat.loc["interest_coverage", y1]
    if pd.notna(ic):
        tone = "thin (below 3x)" if ic < 3 else "healthy"
        out.append(f"Interest coverage in {y1} is {ic:.1f}x ({tone}).")

    bad = balance_check(c).abs()
    bad = bad[bad > 0.5]
    if len(bad):
        out.append("Warning: the balance sheet does not balance in " + ", ".join(map(str, bad.index)) + ".")
    return out

import re

import pandas as pd

from .schema import kind_of, label


def safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
    """a / b, returning NaN (never inf) when b is zero."""
    return a / b.where(b != 0)


def fmt_value(v, kind: str = "amount") -> str:
    if v is None or pd.isna(v):
        return "-"
    if kind == "pct":
        return f"{v * 100:.1f}%"
    if kind == "x":
        return f"{v:.2f}x"
    if kind == "days":
        return f"{v:,.0f}"
    if kind == "num2":
        return f"{v:,.2f}"
    if v == 0:
        return "-"
    return f"({abs(v):,.0f})" if v < 0 else f"{v:,.0f}"


def format_frame(df: pd.DataFrame, kind: str | None = None) -> pd.DataFrame:
    """Return a string DataFrame (labels as index) ready for display."""
    rows = [[fmt_value(v, kind or kind_of(k)) for v in row] for k, row in df.iterrows()]
    return pd.DataFrame(
        rows,
        index=[label(k) for k in df.index],
        columns=[str(c) for c in df.columns],
    )


def slug(name: str) -> str:
    return re.sub(r"[^\w\-]+", "_", name.strip()).strip("_") or "company"

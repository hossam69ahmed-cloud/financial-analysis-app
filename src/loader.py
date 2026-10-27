"""Reads company data from an Excel workbook (template format) or from editable tables."""
import re
from pathlib import Path

import numpy as np
import pandas as pd

from .balance_analysis import balance_check
from .models import CompanyData
from .schema import BALANCE_INPUTS, INCOME_INPUTS


def _norm(x) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    return re.sub(r"\s+", " ", str(x)).strip().lower()


def _year_of(header) -> int | None:
    m = re.search(r"(?:19|20)\d{2}", str(header))
    return int(m.group()) if m else None


def _find_sheet(names: list[str], candidates: list[str]) -> str | None:
    lookup = {re.sub(r"[\s_\-]", "", n).lower(): n for n in names}
    for cand in candidates:
        if cand in lookup:
            return lookup[cand]
    return None


def _read_statement(xl: pd.ExcelFile, sheet: str, inputs, warnings: list[str]) -> pd.DataFrame:
    raw = xl.parse(sheet, header=0)
    first = raw.columns[0]
    year_cols = {col: _year_of(col) for col in raw.columns[1:] if _year_of(col)}
    if not year_cols:
        raise ValueError(f"Sheet '{sheet}': no year columns found in the header row (e.g. 2023).")
    lookup = {}
    for key, lab in inputs:
        lookup[_norm(lab)] = key
        lookup[_norm(key)] = key
    rows = {}
    for _, r in raw.iterrows():
        key = lookup.get(_norm(r[first]))
        if key and key not in rows:
            rows[key] = pd.to_numeric(pd.Series({y: r[col] for col, y in year_cols.items()}), errors="coerce")
    if not rows:
        raise ValueError(f"Sheet '{sheet}': none of the expected line items were found in column A.")
    df = pd.DataFrame(rows).T.reindex([k for k, _ in inputs])
    missing = [lab for k, lab in inputs if df.loc[k].isna().all()]
    if missing:
        warnings.append(f"Sheet '{sheet}': missing or empty items treated as 0: " + ", ".join(missing))
    return df.fillna(0.0)


def load_company_excel(file, filename: str | None = None) -> tuple[CompanyData, list[str]]:
    """file: path or file-like (e.g. Streamlit UploadedFile). Returns (company, warnings)."""
    warnings: list[str] = []
    xl = pd.ExcelFile(file)
    inc_sheet = _find_sheet(xl.sheet_names, ["incomestatement", "income", "is", "pl", "profitandloss"])
    bal_sheet = _find_sheet(xl.sheet_names, ["balancesheet", "balance", "bs"])
    if not inc_sheet or not bal_sheet:
        raise ValueError("The workbook must contain the sheets 'IncomeStatement' and 'BalanceSheet'.")

    info = {}
    info_sheet = _find_sheet(xl.sheet_names, ["info", "company", "companyinfo"])
    if info_sheet:
        raw = xl.parse(info_sheet, header=None)
        for _, r in raw.iterrows():
            if len(r) > 1 and _norm(r.iloc[0]) and not pd.isna(r.iloc[1]):
                info[_norm(r.iloc[0])] = str(r.iloc[1]).strip()

    name = info.get("company name") or (Path(filename).stem if filename else "Company")
    income = _read_statement(xl, inc_sheet, INCOME_INPUTS, warnings)
    balance = _read_statement(xl, bal_sheet, BALANCE_INPUTS, warnings)
    c = CompanyData(
        name=name, income=income, balance=balance,
        ticker=info.get("ticker", ""), currency=info.get("currency", "EGP"),
        unit=info.get("units", "Millions"), sector=info.get("sector", ""),
    )
    if set(income.columns) != set(balance.columns):
        warnings.append(f"Years differ between the sheets; using common years only: {c.years}")
    bad = balance_check(c).abs()
    bad = bad[bad > 0.5]
    if len(bad):
        warnings.append("The balance sheet does not balance in: " + ", ".join(map(str, bad.index)))
    return c, warnings


# ---- helpers for the in-app data editor (tables indexed by label, columns = year strings) ----

def frames_to_editor(c: CompanyData) -> tuple[pd.DataFrame, pd.DataFrame]:
    inc = c.income.rename(index=dict(INCOME_INPUTS), columns=str)
    bal = c.balance.rename(index=dict(BALANCE_INPUTS), columns=str)
    return inc, bal


def empty_editor_frames(first_year: int, n_years: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    years = [str(first_year + i) for i in range(n_years)]
    inc = pd.DataFrame(0.0, index=[lab for _, lab in INCOME_INPUTS], columns=years)
    bal = pd.DataFrame(0.0, index=[lab for _, lab in BALANCE_INPUTS], columns=years)
    return inc, bal


def company_from_editor(name, inc_df, bal_df, **meta) -> CompanyData:
    inc = inc_df.rename(index={lab: k for k, lab in INCOME_INPUTS}).apply(pd.to_numeric, errors="coerce")
    bal = bal_df.rename(index={lab: k for k, lab in BALANCE_INPUTS}).apply(pd.to_numeric, errors="coerce")
    return CompanyData(name=name.strip(), income=inc, balance=bal, **meta)

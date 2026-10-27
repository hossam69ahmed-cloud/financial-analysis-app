from dataclasses import dataclass

import pandas as pd

from .schema import BALANCE_INPUTS, INCOME_INPUTS


@dataclass
class CompanyData:
    """Input data of one company.

    income / balance: DataFrames indexed by line-item key (see schema.py),
    columns = fiscal years (int). Expenses are positive numbers.
    """

    name: str
    income: pd.DataFrame
    balance: pd.DataFrame
    ticker: str = ""
    currency: str = "EGP"
    unit: str = "Millions"
    sector: str = ""

    def __post_init__(self):
        inc = self.income.copy()
        bal = self.balance.copy()
        inc.columns = [int(c) for c in inc.columns]
        bal.columns = [int(c) for c in bal.columns]
        years = sorted(set(inc.columns) & set(bal.columns))
        if not years:
            raise ValueError("The income statement and balance sheet have no common years.")
        self.income = inc.reindex([k for k, _ in INCOME_INPUTS])[years].astype(float).fillna(0.0)
        self.balance = bal.reindex([k for k, _ in BALANCE_INPUTS])[years].astype(float).fillna(0.0)

    @property
    def years(self) -> list[int]:
        return list(self.income.columns)

    @property
    def meta_line(self) -> str:
        return f"{self.currency}, {self.unit}"

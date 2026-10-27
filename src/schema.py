"""Line-item definitions shared by every module (single source of truth)."""

# (key, label) -- the label is what the user sees in Excel templates and tables.
INCOME_INPUTS = [
    ("revenue", "Revenue"),
    ("cogs", "Cost of Goods Sold"),
    ("sga", "Selling, General & Admin Expenses"),
    ("other_opex", "Other Operating Expenses"),
    ("interest_expense", "Interest Expense"),
    ("other_income", "Other Income / (Expense)"),
    ("tax", "Income Tax Expense"),
    ("da", "Depreciation & Amortization"),
    ("dividends", "Dividends Paid"),
    ("shares", "Shares Outstanding"),
]

BALANCE_INPUTS = [
    ("cash", "Cash & Cash Equivalents"),
    ("st_investments", "Short-term Investments"),
    ("receivables", "Accounts Receivable"),
    ("inventory", "Inventory"),
    ("other_current_assets", "Other Current Assets"),
    ("ppe", "Property, Plant & Equipment (net)"),
    ("intangibles", "Intangibles & Goodwill"),
    ("other_noncurrent_assets", "Other Non-current Assets"),
    ("payables", "Accounts Payable"),
    ("st_debt", "Short-term Debt"),
    ("accrued_liabilities", "Accrued & Other Current Liabilities"),
    ("lt_debt", "Long-term Debt"),
    ("other_noncurrent_liabilities", "Other Non-current Liabilities"),
    ("share_capital", "Share Capital"),
    ("retained_earnings", "Retained Earnings & Reserves"),
]

# Labels for calculated lines.
COMPUTED_LABELS = {
    "gross_profit": "Gross Profit",
    "ebit": "Operating Income (EBIT)",
    "ebitda": "EBITDA",
    "pretax": "Pre-tax Income",
    "net_income": "Net Income",
    "total_current_assets": "Total Current Assets",
    "total_assets": "Total Assets",
    "total_current_liabilities": "Total Current Liabilities",
    "total_liabilities": "Total Liabilities",
    "total_equity": "Total Equity",
    "total_liab_equity": "Total Liabilities & Equity",
    "balance_check": "Balance Check (Assets - L&E)",
}

LABELS = {**dict(INCOME_INPUTS), **dict(BALANCE_INPUTS), **COMPUTED_LABELS}

# Display kind per key: amount (default) | pct | x | days | num2
KINDS = {"shares": "amount"}

# Rows printed in bold in tables / reports.
BOLD_KEYS = {
    "gross_profit", "ebit", "ebitda", "pretax", "net_income",
    "total_current_assets", "total_assets", "total_current_liabilities",
    "total_liabilities", "total_equity", "total_liab_equity",
}

# Hints shown in the Excel template's Notes column.
NOTES = {
    "revenue": "Net sales / operating revenue",
    "cogs": "Enter expenses as POSITIVE numbers",
    "other_income": "Positive = income, negative = expense",
    "da": "Memo: already included in COGS / SG&A. Used for EBITDA",
    "dividends": "Memo: positive number. Used for the cash flow statement",
    "shares": "Memo: same unit as the other figures (e.g. millions)",
    "retained_earnings": "Retained earnings + other reserves",
    "st_debt": "Including current portion of long-term debt",
}


def label(key: str) -> str:
    return LABELS.get(key, key)


def kind_of(key: str) -> str:
    return KINDS.get(key, "amount")

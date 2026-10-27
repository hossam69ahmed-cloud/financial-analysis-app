"""Quick end-to-end check:  python tests/smoke_test.py"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.balance_analysis import balance_check
from src.compare import comparison_table
from src.loader import load_company_excel
from src.ratios import RATIO_META, compute_ratios
from src.reports import company_excel, company_pdf, comparison_excel, comparison_pdf
from src.samples import sample_companies
from src.template import build_workbook, template_bytes

cos = {c.name: c for c in sample_companies()}
for c in cos.values():
    assert (balance_check(c).abs() < 0.01).all(), "sample balance sheet must balance"
    back, warns = load_company_excel(io.BytesIO(build_workbook(c)), "x.xlsx")  # Excel round-trip
    assert not warns and back.name == c.name
    assert (back.income - c.income).abs().max().max() < 1e-9
    assert set(compute_ratios(c).index) == set(RATIO_META)
    assert company_excel(c)[:2] == b"PK" and company_pdf(c)[:4] == b"%PDF"

load_company_excel(io.BytesIO(template_bytes()), "template.xlsx")
table, best = comparison_table(cos, 2024)
assert comparison_excel(cos, 2024)[:2] == b"PK" and comparison_pdf(cos, 2024)[:4] == b"%PDF"
print("All checks passed.")

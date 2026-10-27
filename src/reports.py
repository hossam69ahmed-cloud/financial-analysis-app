"""Report export: Excel (.xlsx) and PDF, for one company or a comparison."""
import io
from datetime import date
from xml.sax.saxutils import escape

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import A4, landscape  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.utils import ImageReader  # noqa: E402
from reportlab.platypus import (CondPageBreak, Image, PageBreak, Paragraph,  # noqa: E402
                                SimpleDocTemplate, Spacer, Table, TableStyle)

from .balance_analysis import balance_sheet, structure_metrics  # noqa: E402
from .compare import ALL_METRICS, GROUP_OF, METRIC_GROUPS, comparison_table, metric_trend  # noqa: E402
from .income_analysis import cagr, growth, income_statement, margins, vertical_analysis  # noqa: E402
from .insights import key_takeaways  # noqa: E402
from .models import CompanyData  # noqa: E402
from .ratios import GROUP_ORDER, RATIO_META, compute_ratios  # noqa: E402
from .schema import BOLD_KEYS, kind_of, label  # noqa: E402
from .utils import fmt_value  # noqa: E402

NAVY_HEX = "1F3864"
NAVY = colors.HexColor("#1F3864")
LIGHT = colors.HexColor("#F2F5FA")
GRID = colors.HexColor("#C9D1E0")
FONT = "Arial"

XL_FMT = {
    "amount": '#,##0;(#,##0);"-"', "pct": '0.0%;(0.0%);"-"', "x": '0.00"x"',
    "days": "0", "num2": '#,##0.00;(#,##0.00);"-"',
}
TREND_DEFAULT = ["revenue", "net_income", "revenue_growth", "net_margin", "roe", "current_ratio", "debt_to_equity"]


# =========================================================== shared row builders
def _rows(df: pd.DataFrame, kind: str | None = None, cagr_s: pd.Series | None = None):
    """-> (header, [(key, display_kind, raw_values)], )"""
    header = ["Line item"] + [str(c) for c in df.columns] + (["CAGR"] if cagr_s is not None else [])
    body = []
    for k, row in df.iterrows():
        vals = list(row.values)
        kinds = [kind or kind_of(k)] * len(vals)
        if cagr_s is not None:
            vals.append(cagr_s.get(k))
            kinds.append("pct")
        body.append((k, vals, kinds))
    return header, body


# =========================================================== EXCEL
def _xl_title(ws, text, sub=None):
    ws["A1"] = text
    ws["A1"].font = Font(name=FONT, bold=True, size=14, color=NAVY_HEX)
    if sub:
        ws["A2"] = sub
        ws["A2"].font = Font(name=FONT, italic=True, color="7F7F7F")


def _xl_block(ws, r, title, header, body, group_rows=None, best_cols=None):
    ws.cell(r, 1, title).font = Font(name=FONT, bold=True, size=12, color=NAVY_HEX)
    r += 1
    for j, h in enumerate(header, start=1):
        c = ws.cell(r, j, h)
        c.font = Font(name=FONT, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=NAVY_HEX)
        c.alignment = Alignment(horizontal="left" if j == 1 else "right")
    r += 1
    for key, vals, kinds in body:
        is_group = key is None
        lab = vals[0] if is_group else label(key)
        ws.cell(r, 1, lab).font = Font(name=FONT, bold=is_group or key in BOLD_KEYS)
        if is_group:
            for j in range(1, len(header) + 1):
                ws.cell(r, j).fill = PatternFill("solid", fgColor="D9E2F3")
        else:
            for j, (v, kd) in enumerate(zip(vals, kinds), start=2):
                cell = ws.cell(r, j, None if pd.isna(v) else (v if isinstance(v, str) else float(v)))
                cell.number_format = XL_FMT.get(kd, XL_FMT["amount"])
                cell.font = Font(name=FONT, bold=key in BOLD_KEYS)
                cell.alignment = Alignment(horizontal="right")
        r += 1
    return r + 1


def _xl_widths(ws, first=42, other=14, n=12):
    ws.column_dimensions["A"].width = first
    for j in range(2, n + 2):
        ws.column_dimensions[chr(64 + j)].width = other


def _ratio_body(ratios: pd.DataFrame):
    body = []
    for grp in GROUP_ORDER:
        body.append((None, [grp], []))
        for k, (g, lab, kind, _) in RATIO_META.items():
            if g == grp:
                body.append((k, list(ratios.loc[k].values), [kind] * ratios.shape[1]))
    return body


def company_excel(c: CompanyData) -> bytes:
    inc, bs = income_statement(c), balance_sheet(c)
    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    _xl_title(ws, f"Financial Analysis - {c.name}",
              f"{c.meta_line} | years {c.years[0]}-{c.years[-1]} | generated {date.today():%Y-%m-%d}")
    r = 4
    ws.cell(r, 1, "Key takeaways").font = Font(name=FONT, bold=True, size=12, color=NAVY_HEX)
    for t in key_takeaways(c):
        r += 1
        ws.cell(r, 1, "- " + t).font = Font(name=FONT)
    ws.column_dimensions["A"].width = 120

    ws = wb.create_sheet("Income Statement")
    _xl_title(ws, f"{c.name} - Income Statement", c.meta_line)
    h, b = _rows(inc)
    r = _xl_block(ws, 4, "Income statement", h, b)
    h, b = _rows(vertical_analysis(inc), "pct")
    r = _xl_block(ws, r, "Vertical analysis (% of revenue)", h, b)
    h, b = _rows(growth(inc), "pct", cagr(inc))
    r = _xl_block(ws, r, "Horizontal analysis (year-over-year growth)", h, b)
    h, b = _rows(margins(c), "pct")
    _xl_block(ws, r, "Margins", h, b)
    _xl_widths(ws)

    ws = wb.create_sheet("Balance Sheet")
    _xl_title(ws, f"{c.name} - Balance Sheet", c.meta_line)
    h, b = _rows(bs)
    r = _xl_block(ws, 4, "Balance sheet", h, b)
    h, b = _rows(vertical_analysis(bs, "total_assets"), "pct")
    r = _xl_block(ws, r, "Vertical analysis (% of total assets)", h, b)
    h, b = _rows(growth(bs), "pct", cagr(bs))
    r = _xl_block(ws, r, "Horizontal analysis (year-over-year growth)", h, b)
    h, b = _rows(structure_metrics(c))
    _xl_block(ws, r, "Capital structure & working capital", h, b)
    _xl_widths(ws)

    ws = wb.create_sheet("Ratios")
    _xl_title(ws, f"{c.name} - Financial Ratios", "Balance-sheet based ratios use year-end balances")
    h, _ = _rows(compute_ratios(c))
    _xl_block(ws, 4, "Ratios", h, _ratio_body(compute_ratios(c)))
    _xl_widths(ws)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def comparison_excel(companies: dict[str, CompanyData], year: int, trend_keys=None) -> bytes:
    names = list(companies)
    table, best = comparison_table(companies, year)
    wb = Workbook()
    ws = wb.active
    ws.title = "Comparison"
    _xl_title(ws, f"Company Comparison - {year}",
              "Amounts are in each company's own currency/units. Green = best in row (where a direction applies).")
    header = ["Metric"] + names + ["Best"]
    body = []
    for grp, keys in METRIC_GROUPS.items():
        body.append((None, [grp], []))
        for k in keys:
            body.append((k, list(table.loc[k].values) + [best[k]], [kind_of(k)] * len(names) + ["amount"]))
    _xl_block(ws, 4, f"Comparison for {year}", header, body)
    # highlight the best company's cell in every row
    green = PatternFill("solid", fgColor="C6EFCE")
    for row in ws.iter_rows(min_row=6, max_row=ws.max_row):
        winner = row[len(names) + 1].value
        if winner in names:
            row[1 + names.index(winner)].fill = green
    _xl_widths(ws, n=len(names) + 2)
    ws.column_dimensions[chr(64 + len(names) + 2)].width = 22

    ws = wb.create_sheet("Trends")
    _xl_title(ws, "Trends by metric", "Each block shows one metric over time for every company")
    r = 4
    for k in (trend_keys or TREND_DEFAULT):
        t = metric_trend(companies, k)
        header = ["Year"] + names
        body = []
        for y, row in t.iterrows():
            body.append(("_" + str(y), list(row.values), [kind_of(k)] * len(names)))
        r = _xl_block_trend(ws, r, label(k), header, body)
    _xl_widths(ws, first=16, n=len(names) + 1)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _xl_block_trend(ws, r, title, header, body):
    ws.cell(r, 1, title).font = Font(name=FONT, bold=True, size=12, color=NAVY_HEX)
    r += 1
    for j, h in enumerate(header, start=1):
        c = ws.cell(r, j, h)
        c.font = Font(name=FONT, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=NAVY_HEX)
        c.alignment = Alignment(horizontal="left" if j == 1 else "right")
    r += 1
    for key, vals, kinds in body:
        ws.cell(r, 1, key[1:]).font = Font(name=FONT)
        for j, (v, kd) in enumerate(zip(vals, kinds), start=2):
            cell = ws.cell(r, j, None if pd.isna(v) else float(v))
            cell.number_format = XL_FMT.get(kd, XL_FMT["amount"])
            cell.font = Font(name=FONT)
        r += 1
    return r + 1


# =========================================================== PDF
PAGE = landscape(A4)
MARGIN = 30
WIDTH = PAGE[0] - 2 * MARGIN


def _styles():
    ss = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=20, textColor=NAVY, alignment=0),
        "sub": ParagraphStyle("s", parent=ss["Normal"], fontSize=9, textColor=colors.grey),
        "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=13, textColor=NAVY,
                             spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("b", parent=ss["Normal"], fontSize=9.5, leading=13),
        "note": ParagraphStyle("n", parent=ss["Normal"], fontSize=7.5, textColor=colors.grey, leading=10),
    }


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(MARGIN, 14, "Financial Analyzer")
    canvas.drawRightString(PAGE[0] - MARGIN, 14, f"Page {doc.page}")
    canvas.restoreState()


def _pdf_table(header, body, group_rows=()):
    """body: list of (key, display_strings) ; key may be None for a group header row."""
    data = [header]
    bold = []
    for i, (key, cells) in enumerate(body, start=1):
        data.append(cells)
        if key is not None and key in BOLD_KEYS:
            bold.append(i)
    ncols = len(header) - 1
    first = 215
    w = min(88, (WIDTH - first) / max(ncols, 1))
    t = Table(data, colWidths=[first] + [w] * ncols, repeatRows=1, hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, GRID),
        ("TOPPADDING", (0, 0), (-1, -1), 1.8), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
    ]
    style += [("FONTNAME", (0, r), (-1, r), "Helvetica-Bold") for r in bold]
    for r in group_rows:
        style += [("BACKGROUND", (0, r), (-1, r), colors.HexColor("#D9E2F3")),
                  ("FONTNAME", (0, r), (-1, r), "Helvetica-Bold")]
    t.setStyle(TableStyle(style))
    return t


def _table_from_frame(df, kind=None, cagr_s=None):
    header, rows = _rows(df, kind, cagr_s)
    body = [(k, [label(k)] + [fmt_value(v, kd) for v, kd in zip(vals, kinds)]) for k, vals, kinds in rows]
    return _pdf_table(header, body)


def _block(title, table, st):
    """Heading + table; starts a new page only if the table would not fit in the space that is left."""
    rows = len(table._cellvalues)
    return [CondPageBreak(min(rows * 12 + 40, 400)), Paragraph(title, st["h2"]), table]


def _png(fig) -> io.BytesIO:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=170, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _image(buf: io.BytesIO, width: float) -> Image:
    iw, ih = ImageReader(buf).getSize()
    buf.seek(0)
    return Image(buf, width=width, height=width * ih / iw)


def _company_chart(c: CompanyData) -> io.BytesIO:
    inc, mar = income_statement(c), margins(c)
    yrs = [str(y) for y in inc.columns]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.4))
    x = range(len(yrs))
    a1.bar([i - 0.2 for i in x], inc.loc["revenue"], 0.4, label="Revenue", color="#1F3864")
    a1.bar([i + 0.2 for i in x], inc.loc["net_income"], 0.4, label="Net income", color="#8FAADC")
    a1.set_xticks(list(x), yrs)
    a1.set_title(f"Revenue & net income ({c.meta_line})", fontsize=10)
    a1.legend(fontsize=8)
    for key, name, col in [("gross_margin", "Gross", "#1F3864"), ("operating_margin", "Operating", "#2E75B6"),
                           ("net_margin", "Net", "#C55A11")]:
        a2.plot(yrs, mar.loc[key] * 100, marker="o", label=name, color=col)
    a2.set_title("Margins (%)", fontsize=10)
    a2.legend(fontsize=8)
    for a in (a1, a2):
        a.spines[["top", "right"]].set_visible(False)
        a.tick_params(labelsize=8)
    fig.tight_layout()
    return _png(fig)


def company_pdf(c: CompanyData) -> bytes:
    st = _styles()
    inc, bs = income_statement(c), balance_sheet(c)
    story = [
        Paragraph(escape(f"Financial Analysis Report - {c.name}"), st["title"]),
        Paragraph(escape(f"{c.meta_line}  |  Fiscal years {c.years[0]}-{c.years[-1]}  |  "
                         f"Sector: {c.sector or 'n/a'}  |  Generated {date.today():%d %b %Y}"), st["sub"]),
        Spacer(1, 8), Paragraph("Key takeaways", st["h2"]),
    ]
    story += [Paragraph("&bull; " + escape(t), st["body"]) for t in key_takeaways(c)]
    story += [Spacer(1, 6), _image(_company_chart(c), WIDTH), PageBreak()]

    story += _block("1. Income statement", _table_from_frame(inc), st)
    story += _block("Vertical analysis (% of revenue)", _table_from_frame(vertical_analysis(inc), "pct"), st)
    story += _block("Horizontal analysis (year-over-year growth)", _table_from_frame(growth(inc), "pct", cagr(inc)), st)
    story += _block("Margins", _table_from_frame(margins(c), "pct"), st)
    story += _block("2. Balance sheet", _table_from_frame(bs), st)
    story += _block("Vertical analysis (% of total assets)",
                    _table_from_frame(vertical_analysis(bs, "total_assets"), "pct"), st)
    story += _block("Capital structure & working capital", _table_from_frame(structure_metrics(c)), st)

    ratios = compute_ratios(c)
    header = ["Ratio"] + [str(y) for y in ratios.columns]
    body, groups = [], []
    for grp in GROUP_ORDER:
        body.append((None, [grp] + [""] * ratios.shape[1]))
        groups.append(len(body))
        for k, (g, lab, kind, _) in RATIO_META.items():
            if g == grp:
                body.append((k, [lab] + [fmt_value(v, kind) for v in ratios.loc[k]]))
    story += _block("3. Financial ratios", _pdf_table(header, body, groups), st)
    story += [Spacer(1, 8),
              Paragraph("Notes: expenses are entered as positive numbers; EBITDA = EBIT + depreciation & amortization; "
                        "balance-sheet ratios use year-end balances; ROIC = EBIT x (1 - effective tax rate) / "
                        "(debt + equity - cash & short-term investments). Figures come from the data provided by the user.",
                        st["note"])]

    buf = io.BytesIO()
    SimpleDocTemplate(buf, pagesize=PAGE, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=28, bottomMargin=28,
                      title=f"Financial Analysis - {c.name}").build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()


def _comparison_chart(table: pd.DataFrame, names: list[str]) -> io.BytesIO:
    keys = ["gross_margin", "operating_margin", "net_margin", "roa", "roe"]
    fig, ax = plt.subplots(figsize=(11, 3.4))
    n = len(names)
    bw = 0.8 / n
    palette = ["#1F3864", "#C55A11", "#2E75B6", "#70AD47", "#7F7F7F", "#BF9000"]
    for i, name in enumerate(names):
        vals = [table.loc[k, name] * 100 for k in keys]
        ax.bar([j + (i - (n - 1) / 2) * bw for j in range(len(keys))], vals, bw, label=name, color=palette[i % 6])
    ax.set_xticks(range(len(keys)), [label(k) for k in keys])
    ax.set_title("Profitability comparison (%)", fontsize=10)
    ax.legend(fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    return _png(fig)


def comparison_pdf(companies: dict[str, CompanyData], year: int, trend_keys=None) -> bytes:
    st = _styles()
    names = list(companies)
    table, best = comparison_table(companies, year)
    story = [
        Paragraph("Company Comparison Report", st["title"]),
        Paragraph(escape(f"Companies: {', '.join(names)}  |  Year: {year}  |  Generated {date.today():%d %b %Y}"), st["sub"]),
        Paragraph("Amounts are shown in each company's own currency and units. 'Best' marks the strongest company "
                  "per metric where a direction applies (e.g. higher margin, lower debt).", st["note"]),
        Spacer(1, 6), _image(_comparison_chart(table, names), WIDTH), Paragraph(f"Metrics for {year}", st["h2"]),
    ]
    header = ["Metric"] + names + ["Best"]
    body, groups = [], []
    for grp, keys in METRIC_GROUPS.items():
        body.append((None, [grp] + [""] * (len(names) + 1)))
        groups.append(len(body))
        for k in keys:
            body.append((k, [label(k)] + [fmt_value(v, kind_of(k)) for v in table.loc[k]] + [best[k]]))
    story.append(_pdf_table(header, body, groups))
    story.append(PageBreak())
    story.append(Paragraph("Trends", st["h2"]))
    for k in (trend_keys or TREND_DEFAULT):
        t = metric_trend(companies, k)
        rows = [[str(y)] + [fmt_value(v, kind_of(k)) for v in row] for y, row in t.iterrows()]
        story += [Paragraph(label(k), st["body"]), _pdf_table(["Year"] + names, [(None, r) for r in rows]), Spacer(1, 6)]

    buf = io.BytesIO()
    SimpleDocTemplate(buf, pagesize=PAGE, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=28, bottomMargin=28,
                      title="Company Comparison").build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()

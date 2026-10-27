"""Financial Analyzer - Streamlit app.

Run:  streamlit run app.py
"""
import pandas as pd
import streamlit as st

from src import storage
from src.balance_analysis import balance_check, balance_sheet, structure_metrics
from src.compare import ALL_METRICS, METRIC_GROUPS, all_years, comparison_table, metric_trend
from src.income_analysis import cagr, growth, income_statement, margins, vertical_analysis
from src.insights import key_takeaways
from src.loader import (company_from_editor, empty_editor_frames, frames_to_editor,
                        load_company_excel)
from src.ratios import GROUP_ORDER, RATIO_META, compute_ratios
from src.reports import company_excel, company_pdf, comparison_excel, comparison_pdf
from src.samples import sample_companies
from src.schema import kind_of, label
from src.template import build_workbook, template_bytes
from src.utils import fmt_value, format_frame, slug

st.set_page_config(page_title="Financial analysis Tech-Builder", layout="wide")

# Custom CSS to align everything to the Left (English LTR layout)
st.markdown(
    """
    <style>
    h1, h2, h3, h4, p, label, .stMarkdown {
        text-align: left !important;
        direction: ltr;
    }
    div.row-widget.stRadio > div {
        flex-direction: column;
        justify-content: flex-start;
        text-align: left;
    }
    div.row-widget.stRadio > div[role='radiogroup'] {
        justify-content: flex-start;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------ state
if "companies" not in st.session_state:
    st.session_state.companies = storage.load_all()
if "editor_seed" not in st.session_state:
    st.session_state.editor_seed = None
companies: dict = st.session_state.companies


def add_company(c):
    companies[c.name] = c
    storage.save_company(c)


def remove_company(name):
    companies.pop(name, None)
    storage.delete_company(name)


def show(df: pd.DataFrame, kind: str | None = None):
    st.dataframe(format_frame(df, kind))


# ------------------------------------------------------------------ Sidebar Main Menu
st.sidebar.markdown("<p style='font-size: 15px; font-weight: bold;'>Financial analysis Tech-Builder</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("<h3>Main Menu</h3>", unsafe_allow_html=True)

nav_titles = ["Companies Management", "Company Analysis", "Compare Companies", "Reports"]

page = st.sidebar.radio(
    "Main Menu",
    nav_titles,
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"<p style='color: gray;'>Saved Companies: {len(companies)}</p>", unsafe_allow_html=True)


# ================================================================== PAGE 1: companies
def page_companies():
    st.markdown("<h2>Companies Management</h2>", unsafe_allow_html=True)
    st.markdown("<p>Add company data via Excel upload, manual entry, or sample data, and manage saved companies.</p>", unsafe_allow_html=True)

    tab_titles = ["Excel Upload", "Manual Entry", "Saved Companies", "Delete Company"]
    
    tab_selection = st.radio("Sections", tab_titles, horizontal=True)
    st.markdown("---")

    if tab_selection == tab_titles[0]:
        st.download_button(
            "⬇️ Download Empty Template",
            data=template_bytes(),
            file_name="company_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.caption("Fill blue cells only. Expenses must be positive numbers. Company name from Info sheet.")
        files = st.file_uploader("Upload files", type=["xlsx", "xlsm"], accept_multiple_files=True)
        if files and st.button("Import Files", type="primary"):
            for f in files:
                try:
                    c, warns = load_company_excel(f, filename=f.name)
                except Exception as e:  # noqa: BLE001
                    st.error(f"{f.name}: {e}")
                    continue
                add_company(c)
                st.success(f"Imported «{c.name}» ({c.years[0]}–{c.years[-1]})")
                for w in warns:
                    st.warning(f"{f.name}: {w}")
        if st.button("Add Sample Companies"):
            for c in sample_companies():
                add_company(c)
            st.success("Added Nile Foods and Delta Tech.")

    elif tab_selection == tab_titles[1]:
        existing = ["— New Company —"] + list(companies)
        pick = st.selectbox("Start from", existing)
        with st.form("meta_form"):
            c1, c2, c3 = st.columns(3)
            default = companies.get(pick) if pick in companies else None
            name = c1.text_input("Company Name", value=default.name if default else "")
            ticker = c2.text_input("Ticker", value=default.ticker if default else "")
            sector = c3.text_input("Sector", value=default.sector if default else "")
            c4, c5, c6, c7 = st.columns(4)
            currency = c4.text_input("Currency", value=default.currency if default else "EGP")
            unit = c5.text_input("Unit", value=default.unit if default else "Millions")
            first_year = c6.number_input("First Year", 1990, 2100, value=default.years[0] if default else 2022)
            n_years = c7.number_input("Number of Years", 2, 10, value=len(default.years) if default else 3)
            if st.form_submit_button("Prepare Tables"):
                if default is not None:
                    inc, bal = frames_to_editor(default)
                else:
                    inc, bal = empty_editor_frames(int(first_year), int(n_years))
                seed = st.session_state.editor_seed or {"nonce": 0}
                st.session_state.editor_seed = {
                    "nonce": seed["nonce"] + 1, "inc": inc, "bal": bal,
                    "meta": dict(name=name, ticker=ticker, sector=sector, currency=currency, unit=unit),
                }

        seed = st.session_state.editor_seed
        if seed:
            st.subheader("Income Statement")
            inc_df = st.data_editor(seed["inc"], key=f"inc_{seed['nonce']}", num_rows="fixed")
            st.subheader("Balance Sheet")
            bal_df = st.data_editor(seed["bal"], key=f"bal_{seed['nonce']}", num_rows="fixed")
            st.caption("Expenses in positive numbers. Totals are calculated automatically.")
            if st.button("💾 Save Company", type="primary"):
                meta = seed["meta"]
                if not meta["name"].strip():
                    st.error("Please enter the company name first.")
                else:
                    try:
                        c = company_from_editor(meta["name"], inc_df, bal_df, ticker=meta["ticker"],
                                                sector=meta["sector"], currency=meta["currency"], unit=meta["unit"])
                        add_company(c)
                        st.success(f"Saved «{c.name}».")
                        bad = balance_check(c).abs()
                        if (bad > 0.5).any():
                            st.warning("Balance sheet is unbalanced in years: " + ", ".join(map(str, bad[bad > 0.5].index)))
                    except Exception as e:  # noqa: BLE001
                        st.error(str(e))

    elif tab_selection == tab_titles[2]:
        if not companies:
            st.info("No companies saved yet.")
        else:
            rows = [{"Company": c.name, "Ticker": c.ticker, "Sector": c.sector,
                     "Years": f"{c.years[0]}–{c.years[-1]}", "Currency / Unit": c.meta_line}
                    for c in companies.values()]
            st.dataframe(pd.DataFrame(rows), hide_index=True)
            exp = st.selectbox("Export Company Excel", list(companies), key="export_comp_select")
            st.download_button(
                "⬇️ Download", data=build_workbook(companies[exp]), file_name=f"{slug(exp)}_input.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    else:
        st.subheader("Delete Company Data")
        if not companies:
            st.info("No companies available to delete.")
        else:
            target_company = st.selectbox("Select Company to Delete", list(companies), key="delete_comp_select")
            st.warning(f"Are you sure you want to delete all data for «{target_company}»? This action cannot be undone.")
            if st.button("🗑️ Confirm Delete Company", type="primary"):
                remove_company(target_company)
                st.success(f"Company «{target_company}» has been deleted successfully.")
                st.rerun()


# ================================================================== PAGE 2: analysis
def page_analysis():
    st.header("Company Analysis")
    if not companies:
        st.info("Please add a company first from the 'Companies Management' section.")
        return
    name = st.selectbox("Company", list(companies))
    c = companies[name]
    st.caption(f"{c.meta_line} | {c.years[0]}–{c.years[-1]}" + (f" | {c.sector}" if c.sector else ""))

    for t in key_takeaways(c):
        st.markdown(f"- {t}")

    sub_tabs = ["Income Statement", "Balance Sheet", "Financial Ratios"]
    sub_sel = st.radio("Sections", sub_tabs, horizontal=True)
    st.markdown("---")

    inc, bs = income_statement(c), balance_sheet(c)

    if sub_sel == sub_tabs[0]:
        st.subheader("Income Statement")
        show(inc)
        chart = pd.DataFrame({"Revenue": inc.loc["revenue"], "Net Income": inc.loc["net_income"]}).rename(index=str)
        st.bar_chart(chart)
        st.subheader("Vertical Analysis (% of Revenue)")
        show(vertical_analysis(inc), "pct")
        st.subheader("Horizontal Analysis (YoY Growth) & CAGR")
        g = growth(inc).assign(CAGR=cagr(inc))
        show(g, "pct")
        st.subheader("Profit Margins")
        m = margins(c)
        show(m, "pct")
        st.line_chart((m.loc[["gross_margin", "operating_margin", "net_margin"]] * 100)
                      .rename(index=label).T.rename(index=str))

    elif sub_sel == sub_tabs[1]:
        st.subheader("Balance Sheet")
        show(bs)
        diff = balance_check(c)
        if (diff.abs() > 0.5).any():
            st.warning("Balance sheet unbalanced in: " + ", ".join(map(str, diff[diff.abs() > 0.5].index)))
        else:
            st.success("Balance sheet is balanced across all years ✔")
        st.subheader("Vertical Analysis (% of Total Assets)")
        show(vertical_analysis(bs, "total_assets"), "pct")
        st.subheader("Horizontal Analysis (YoY Growth)")
        show(growth(bs).assign(CAGR=cagr(bs)), "pct")
        st.subheader("Capital Structure & Working Capital")
        show(structure_metrics(c))

    else:
        ratios = compute_ratios(c)
        for grp in GROUP_ORDER:
            st.subheader(grp)
            keys = [k for k, v in RATIO_META.items() if v[0] == grp]
            rows = [[fmt_value(v, RATIO_META[k][2]) for v in ratios.loc[k]] for k in keys]
            st.dataframe(pd.DataFrame(rows, index=[RATIO_META[k][1] for k in keys],
                                      columns=[str(y) for y in ratios.columns]))
        st.caption("Balance sheet ratios are calculated on year-end balances.")


# ================================================================== PAGE 3: compare
def page_compare():
    st.header("Compare Companies")
    if len(companies) < 2:
        st.info("Please add at least two companies to make comparisons.")
        return
    names = st.multiselect("Select Companies", list(companies), default=list(companies)[:2])
    if len(names) < 2:
        st.warning("Please select at least two companies.")
        return
    sel = {n: companies[n] for n in names}
    years = sorted(all_years(sel), reverse=True)
    year = st.selectbox("Year", years)

    table, best = comparison_table(sel, year)
    rows, index = [], []
    for grp, keys in METRIC_GROUPS.items():
        rows.append([""] * (len(names) + 1))
        index.append(f"— {grp} —")
        for k in keys:
            rows.append([fmt_value(v, kind_of(k)) for v in table.loc[k]] + [best[k]])
            index.append(label(k))
    st.dataframe(pd.DataFrame(rows, index=index, columns=names + ["Best"]), height=700)
    st.caption("Amounts are in each company's currency and unit.")

    st.subheader("Metric Trend Over Years")
    metric = st.selectbox("Metric", ALL_METRICS, format_func=label)
    trend = metric_trend(sel, metric)
    st.line_chart(trend.rename(index=str))
    st.dataframe(pd.DataFrame([[fmt_value(v, kind_of(metric)) for v in r] for _, r in trend.iterrows()],
                              index=[str(y) for y in trend.index], columns=names))


# ================================================================== PAGE 4: reports
def page_reports():
    st.header("Reports")
    if not companies:
        st.info("Please add a company first.")
        return
    mode = st.radio("Report Type", ["Single Company", "Company Comparison"], horizontal=True)
    xlsx_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    if mode == "Single Company":
        name = st.selectbox("Company", list(companies))
        sig = ("single", name)
        if st.button("Generate Report", type="primary"):
            with st.spinner("Generating..."):
                c = companies[name]
                st.session_state.report = {"sig": sig, "xlsx": company_excel(c), "pdf": company_pdf(c),
                                           "base": f"{slug(name)}_analysis"}
    else:
        names = st.multiselect("Companies", list(companies), default=list(companies)[:2])
        sel = {n: companies[n] for n in names}
        years = sorted(all_years(sel), reverse=True) if sel else []
        year = st.selectbox("Comparison Year", years) if years else None
        sig = ("compare", tuple(names), year)
        if st.button("Generate Report", type="primary"):
            if len(names) < 2:
                st.warning("Please select at least two companies.")
            else:
                with st.spinner("Generating..."):
                    st.session_state.report = {"sig": sig, "xlsx": comparison_excel(sel, year),
                                               "pdf": comparison_pdf(sel, year),
                                               "base": f"comparison_{year}"}

    rep = st.session_state.get("report")
    if rep and rep["sig"] == sig:
        st.success("Report is ready:")
        c1, c2 = st.columns(2)
        c1.download_button("⬇️ Download Excel", rep["xlsx"], file_name=f"{rep['base']}.xlsx", mime=xlsx_mime)
        c2.download_button("⬇️ Download PDF", rep["pdf"], file_name=f"{rep['base']}.pdf", mime="application/pdf")


# Pages Routing Dictionary
pages_dict = {
    "Companies Management": page_companies,
    "Company Analysis": page_analysis,
    "Compare Companies": page_compare,
    "Reports": page_reports,
}

if page in pages_dict:
    pages_dict[page]()
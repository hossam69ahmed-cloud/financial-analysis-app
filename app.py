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

st.set_page_config(page_title="المحلل المالي | Financial Analyzer", layout="wide")

# ------------------------------------------------------------------ sidebar & lang
# اختيار اللغة في الشريط الجانبي
lang_option = st.sidebar.selectbox("Language / اللغة", ["العربية", "English"])
lang_code = "ar" if lang_option == "العربية" else "en"

# تعديل اتجاه التابات والمحتوى (RTL للعربي و LTR للإنجليزي)
if lang_code == "ar":
    st.markdown(
        """<style>
        [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
        h1, h2, h3, h4, h5, h6, label, .stTabs [data-baseweb="tab"] {direction: rtl; text-align: right;}
        .stTabs [data-baseweb="tab-list"] {direction: rtl;}
        </style>""",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """<style>
        [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
        h1, h2, h3, h4, h5, h6, label, .stTabs [data-baseweb="tab"] {direction: ltr; text-align: left;}
        .stTabs [data-baseweb="tab-list"] {direction: ltr;}
        </style>""",
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


# ------------------------------------------------------------------ sidebar menu
st.sidebar.title("المحلل المالي" if lang_code == "ar" else "Financial Analyzer")

nav_options = {
    "ar": ["إدارة الشركات", "تحليل شركة", "مقارنة شركات", "التقارير"],
    "en": ["Companies Management", "Company Analysis", "Compare Companies", "Reports"]
}

page_selection = st.sidebar.radio(
    "القائمة" if lang_code == "ar" else "Menu",
    nav_options[lang_code],
)

saved_txt = f"عدد الشركات المحفوظة: {len(companies)}" if lang_code == "ar" else f"Saved Companies: {len(companies)}"
st.sidebar.caption(saved_txt)


# ================================================================== PAGE 1: companies
def page_companies():
    title = "إدارة الشركات" if lang_code == "ar" else "Companies Management"
    desc = "أضف بيانات الشركة بإحدى الطرق: رفع ملف Excel، أو إدخال يدوي داخل البرنامج، أو بيانات تجريبية." if lang_code == "ar" else "Add company data via Excel upload, manual entry, or sample data."
    st.header(title)
    st.write(desc)

    tab_titles = ["رفع ملف Excel", "إدخال / تعديل يدوي", "الشركات المحفوظة"] if lang_code == "ar" else ["Excel Upload", "Manual Entry / Edit", "Saved Companies"]
    tab_up, tab_manual, tab_list = st.tabs(tab_titles)

    # ---- upload
    with tab_up:
        btn_dl = "تحميل قالب Excel فارغ (بقيم توضيحية)" if lang_code == "ar" else "Download Empty Excel Template"
        st.download_button(
            btn_dl,
            data=template_bytes(),
            file_name="company_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        cap_txt = "املأ الخلايا الزرقاء فقط. المصروفات تُدخل بأرقام موجبة. اسم الشركة من ورقة Info." if lang_code == "ar" else "Fill blue cells only. Enter expenses as positive numbers. Company name is in Info sheet."
        st.caption(cap_txt)
        
        up_lbl = "ارفع ملف أو أكثر" if lang_code == "ar" else "Upload one or more files"
        files = st.file_uploader(up_lbl, type=["xlsx", "xlsm"], accept_multiple_files=True)
        
        btn_imp = "استيراد الملفات" if lang_code == "ar" else "Import Files"
        if files and st.button(btn_imp, type="primary"):
            for f in files:
                try:
                    c, warns = load_company_excel(f, filename=f.name)
                except Exception as e:  # noqa: BLE001
                    st.error(f"{f.name}: {e}")
                    continue
                add_company(c)
                succ_msg = f"تم استيراد «{c.name}» ({c.years[0]}–{c.years[-1]})" if lang_code == "ar" else f"Imported '{c.name}' ({c.years[0]}–{c.years[-1]})"
                st.success(succ_msg)
                for w in warns:
                    st.warning(f"{f.name}: {w}")
                    
        btn_sample = "إضافة شركتين تجريبيتين (للتجربة السريعة)" if lang_code == "ar" else "Add Sample Companies (Quick Test)"
        if st.button(btn_sample):
            for c in sample_companies():
                add_company(c)
            succ_sample = "تمت إضافة Nile Foods و Delta Tech (أرقام وهمية)." if lang_code == "ar" else "Added Nile Foods and Delta Tech (dummy data)."
            st.success(succ_sample)

    # ---- manual entry
    with tab_manual:
        new_comp_str = "— شركة جديدة —" if lang_code == "ar" else "— New Company —"
        existing = [new_comp_str] + list(companies)
        start_lbl = "ابدأ من" if lang_code == "ar" else "Start from"
        pick = st.selectbox(start_lbl, existing)
        
        with st.form("meta_form"):
            c1, c2, c3 = st.columns(3)
            default = companies.get(pick) if pick in companies else None
            
            lbl_name = "اسم الشركة" if lang_code == "ar" else "Company Name"
            lbl_ticker = "الرمز (Ticker)" if lang_code == "ar" else "Ticker Symbol"
            lbl_sector = "القطاع" if lang_code == "ar" else "Sector"
            name = c1.text_input(lbl_name, value=default.name if default else "")
            ticker = c2.text_input(lbl_ticker, value=default.ticker if default else "")
            sector = c3.text_input(lbl_sector, value=default.sector if default else "")
            
            c4, c5, c6, c7 = st.columns(4)
            lbl_curr = "العملة" if lang_code == "ar" else "Currency"
            lbl_unit = "الوحدة" if lang_code == "ar" else "Unit"
            lbl_fyear = "أول سنة" if lang_code == "ar" else "First Year"
            lbl_nyears = "عدد السنوات" if lang_code == "ar" else "Number of Years"
            
            currency = c4.text_input(lbl_curr, value=default.currency if default else "EGP")
            unit = c5.text_input(lbl_unit, value=default.unit if default else "Millions")
            first_year = c6.number_input(lbl_fyear, 1990, 2100, value=default.years[0] if default else 2022)
            n_years = c7.number_input(lbl_nyears, 2, 10, value=len(default.years) if default else 3)
            
            btn_prep = "تجهيز الجداول" if lang_code == "ar" else "Prepare Tables"
            if st.form_submit_button(btn_prep):
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
            st.subheader("قائمة الدخل" if lang_code == "ar" else "Income Statement")
            inc_df = st.data_editor(seed["inc"], key=f"inc_{seed['nonce']}", num_rows="fixed")
            st.subheader("الميزانية العمومية" if lang_code == "ar" else "Balance Sheet")
            bal_df = st.data_editor(seed["bal"], key=f"bal_{seed['nonce']}", num_rows="fixed")
            st.caption("المصروفات بأرقام موجبة. الإجماليات تُحسب تلقائياً." if lang_code == "ar" else "Expenses as positive numbers. Totals are calculated automatically.")
            
            btn_save = "حفظ الشركة" if lang_code == "ar" else "Save Company"
            if st.button(btn_save, type="primary"):
                meta = seed["meta"]
                if not meta["name"].strip():
                    err_name = "اكتب اسم الشركة أولاً (في النموذج أعلاه ثم اضغط «تجهيز الجداول»)." if lang_code == "ar" else "Please enter the company name first."
                    st.error(err_name)
                else:
                    try:
                        c = company_from_editor(meta["name"], inc_df, bal_df, ticker=meta["ticker"],
                                                sector=meta["sector"], currency=meta["currency"], unit=meta["unit"])
                        add_company(c)
                        st.success(f"تم حفظ «{c.name}»." if lang_code == "ar" else f"Saved '{c.name}'.")
                        bad = balance_check(c).abs()
                        if (bad > 0.5).any():
                            unbal_msg = "الميزانية غير متوازنة في السنوات: " if lang_code == "ar" else "Balance sheet unbalanced in years: "
                            st.warning(unbal_msg + ", ".join(map(str, bad[bad > 0.5].index)))
                    except Exception as e:  # noqa: BLE001
                        st.error(str(e))

    # ---- list
    with tab_list:
        if not companies:
            st.info("لا توجد شركات بعد." if lang_code == "ar" else "No companies saved yet.")
        else:
            if lang_code == "ar":
                rows = [{"الشركة": c.name, "الرمز": c.ticker, "القطاع": c.sector,
                         "السنوات": f"{c.years[0]}–{c.years[-1]}", "العملة / الوحدة": c.meta_line}
                        for c in companies.values()]
            else:
                rows = [{"Company": c.name, "Ticker": c.ticker, "Sector": c.sector,
                         "Years": f"{c.years[0]}–{c.years[-1]}", "Currency / Unit": c.meta_line}
                        for c in companies.values()]
            st.dataframe(pd.DataFrame(rows), hide_index=True)
            
            col1, col2 = st.columns(2)
            lbl_del = "حذف شركة" if lang_code == "ar" else "Delete Company"
            victim = col1.selectbox(lbl_del, list(companies))
            btn_del_act = "حذف" if lang_code == "ar" else "Delete"
            if col1.button(btn_del_act):
                remove_company(victim)
                st.rerun()
                
            lbl_exp = "تصدير بيانات الشركة كملف إدخال Excel" if lang_code == "ar" else "Export company data as Excel input"
            exp = col2.selectbox(lbl_exp, list(companies))
            btn_exp_act = "تحميل" if lang_code == "ar" else "Download"
            col2.download_button(
                btn_exp_act, data=build_workbook(companies[exp]), file_name=f"{slug(exp)}_input.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


# ================================================================== PAGE 2: analysis
def page_analysis():
    st.header("تحليل شركة" if lang_code == "ar" else "Company Analysis")
    if not companies:
        st.info("أضف شركة أولاً من صفحة «إدارة الشركات»." if lang_code == "ar" else "Please add a company first from Companies Management.")
        return
    lbl_comp = "الشركة" if lang_code == "ar" else "Company"
    name = st.selectbox(lbl_comp, list(companies))
    c = companies[name]
    st.caption(f"{c.meta_line} | {c.years[0]}–{c.years[-1]}" + (f" | {c.sector}" if c.sector else ""))

    for t_item in key_takeaways(c):
        st.markdown(f"- {t_item}")

    tab_an_titles = ["قائمة الدخل", "الميزانية العمومية", "النسب المالية"] if lang_code == "ar" else ["Income Statement", "Balance Sheet", "Financial Ratios"]
    t_inc, t_bal, t_rat = st.tabs(tab_an_titles)
    inc, bs = income_statement(c), balance_sheet(c)

    with t_inc:
        st.subheader("قائمة الدخل" if lang_code == "ar" else "Income Statement")
        show(inc)
        chart = pd.DataFrame({"Revenue": inc.loc["revenue"], "Net Income": inc.loc["net_income"]}).rename(index=str)
        st.bar_chart(chart)
        
        st.subheader("التحليل الرأسي (% من الإيرادات)" if lang_code == "ar" else "Vertical Analysis (% of Revenue)")
        show(vertical_analysis(inc), "pct")
        
        st.subheader("التحليل الأفقي (النمو السنوي) و CAGR" if lang_code == "ar" else "Horizontal Analysis (YoY Growth) & CAGR")
        g = growth(inc).assign(CAGR=cagr(inc))
        show(g, "pct")
        
        st.subheader("هوامش الربح" if lang_code == "ar" else "Profit Margins")
        m = margins(c)
        show(m, "pct")
        st.line_chart((m.loc[["gross_margin", "operating_margin", "net_margin"]] * 100)
                      .rename(index=label).T.rename(index=str))

    with t_bal:
        st.subheader("الميزانية العمومية" if lang_code == "ar" else "Balance Sheet")
        show(bs)
        diff = balance_check(c)
        if (diff.abs() > 0.5).any():
            unbal_lbl = "الميزانية غير متوازنة في: " if lang_code == "ar" else "Balance sheet unbalanced in: "
            st.warning(unbal_lbl + ", ".join(map(str, diff[diff.abs() > 0.5].index)))
        else:
            bal_ok = "الميزانية متوازنة في كل السنوات" if lang_code == "ar" else "Balance sheet is balanced for all years"
            st.success(bal_ok)
            
        st.subheader("التحليل الرأسي (% من إجمالي الأصول)" if lang_code == "ar" else "Vertical Analysis (% of Total Assets)")
        show(vertical_analysis(bs, "total_assets"), "pct")
        
        st.subheader("التحليل الأفقي (النمو السنوي)" if lang_code == "ar" else "Horizontal Analysis (YoY Growth)")
        show(growth(bs).assign(CAGR=cagr(bs)), "pct")
        
        st.subheader("هيكل التمويل ورأس المال العامل" if lang_code == "ar" else "Capital Structure & Working Capital")
        show(structure_metrics(c))

    with t_rat:
        ratios = compute_ratios(c)
        for grp in GROUP_ORDER:
            st.subheader(grp)
            keys = [k for k, v in RATIO_META.items() if v[0] == grp]
            rows = [[fmt_value(v, RATIO_META[k][2]) for v in ratios.loc[k]] for k in keys]
            st.dataframe(pd.DataFrame(rows, index=[RATIO_META[k][1] for k in keys],
                                      columns=[str(y) for y in ratios.columns]))
        st.caption("نسب الميزانية محسوبة على أرصدة نهاية السنة." if lang_code == "ar" else "Balance sheet ratios calculated on year-end balances.")


# ================================================================== PAGE 3: compare
def page_compare():
    st.header("مقارنة شركات" if lang_code == "ar" else "Compare Companies")
    if len(companies) < 2:
        st.info("أضف شركتين على الأقل لإجراء المقارنة." if lang_code == "ar" else "Add at least two companies to compare.")
        return
    lbl_sel = "اختر الشركات" if lang_code == "ar" else "Select Companies"
    names = st.multiselect(lbl_sel, list(companies), default=list(companies)[:2])
    if len(names) < 2:
        st.warning("اختر شركتين على الأقل." if lang_code == "ar" else "Select at least two companies.")
        return
    sel = {n: companies[n] for n in names}
    years = sorted(all_years(sel), reverse=True)
    lbl_yr = "السنة" if lang_code == "ar" else "Year"
    year = st.selectbox(lbl_yr, years)

    table, best = comparison_table(sel, year)
    rows, index = [], []
    for grp, keys in METRIC_GROUPS.items():
        rows.append([""] * (len(names) + 1))
        index.append(f"— {grp} —")
        for k in keys:
            rows.append([fmt_value(v, kind_of(k)) for v in table.loc[k]] + [best[k]])
            index.append(label(k))
            
    best_col_title = "الأفضل" if lang_code == "ar" else "Best"
    st.dataframe(pd.DataFrame(rows, index=index, columns=names + [best_col_title]), height=700)
    st.caption("المبالغ بعملة ووحدة كل شركة. «الأفضل» يظهر للمؤشرات التي لها اتجاه واضح." if lang_code == "ar" else "Amounts in original company currency/unit. 'Best' indicates clearer metric trends.")

    st.subheader("تطور مؤشر عبر السنوات" if lang_code == "ar" else "Metric Evolution Over Years")
    lbl_met = "المؤشر" if lang_code == "ar" else "Metric"
    metric = st.selectbox(lbl_met, ALL_METRICS, format_func=label)
    trend = metric_trend(sel, metric)
    st.line_chart(trend.rename(index=str))
    st.dataframe(pd.DataFrame([[fmt_value(v, kind_of(metric)) for v in r] for _, r in trend.iterrows()],
                              index=[str(y) for y in trend.index], columns=names))


# ================================================================== PAGE 4: reports
def page_reports():
    st.header("التقارير" if lang_code == "ar" else "Reports")
    if not companies:
        st.info("أضف شركة أولاً." if lang_code == "ar" else "Please add a company first.")
        return
    
    rep_types = ["شركة واحدة", "مقارنة بين شركات"] if lang_code == "ar" else ["Single Company", "Companies Comparison"]
    mode = st.radio("نوع التقرير" if lang_code == "ar" else "Report Type", rep_types, horizontal=True)
    xlsx_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    if mode in ["شركة واحدة", "Single Company"]:
        lbl_c = "الشركة" if lang_code == "ar" else "Company"
        name = st.selectbox(lbl_c, list(companies))
        sig = ("single", name)
        btn_gen = "إنشاء التقرير" if lang_code == "ar" else "Generate Report"
        if st.button(btn_gen, type="primary"):
            spin_txt = "جاري الإنشاء..." if lang_code == "ar" else "Generating..."
            with st.spinner(spin_txt):
                c = companies[name]
                st.session_state.report = {"sig": sig, "xlsx": company_excel(c), "pdf": company_pdf(c),
                                           "base": f"{slug(name)}_analysis"}
    else:
        lbl_cs = "الشركات" if lang_code == "ar" else "Companies"
        names = st.multiselect(lbl_cs, list(companies), default=list(companies)[:2])
        sel = {n: companies[n] for n in names}
        years = sorted(all_years(sel), reverse=True) if sel else []
        lbl_cy = "سنة المقارنة" if lang_code == "ar" else "Comparison Year"
        year = st.selectbox(lbl_cy, years) if years else None
        sig = ("compare", tuple(names), year)
        btn_gen = "إنشاء التقرير" if lang_code == "ar" else "Generate Report"
        if st.button(btn_gen, type="primary"):
            if len(names) < 2:
                st.warning("اختر شركتين على الأقل." if lang_code == "ar" else "Select at least two companies.")
            else:
                spin_txt = "جاري الإنشاء..." if lang_code == "ar" else "Generating..."
                with st.spinner(spin_txt):
                    st.session_state.report = {"sig": sig, "xlsx": comparison_excel(sel, year),
                                               "pdf": comparison_pdf(sel, year),
                                               "base": f"comparison_{year}"}

    rep = st.session_state.get("report")
    if rep and rep["sig"] == sig:
        st.success("التقرير جاهز:" if lang_code == "ar" else "Report Ready:")
        c1, c2 = st.columns(2)
        dl_xl = "تحميل Excel" if lang_code == "ar" else "Download Excel"
        dl_pdf = "تحميل PDF" if lang_code == "ar" else "Download PDF"
        c1.download_button(dl_xl, rep["xlsx"], file_name=f"{rep['base']}.xlsx", mime=xlsx_mime)
        c2.download_button(dl_pdf, rep["pdf"], file_name=f"{rep['base']}.pdf", mime="application/pdf")


# Map pages execution according to language option
if lang_code == "ar":
    page_map = {
        "إدارة الشركات": page_companies,
        "تحليل شركة": page_analysis,
        "مقارنة شركات": page_compare,
        "التقارير": page_reports,
    }
else:
    page_map = {
        "Companies Management": page_companies,
        "Company Analysis": page_analysis,
        "Compare Companies": page_compare,
        "Reports": page_reports,
    }

page_map[page_selection]()
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

# حقن CSS لتوسيط كافة محتويات الصفحة وجعل قائمة اللغة صغيرة ومنسقة
st.markdown(
    """
    <style>
    /* توسيط كافة العناوين والنصوص والعناصر الرئيسية */
    h1, h2, h3, h4, p, label, .stMarkdown {
        text-align: center !important;
        direction: rtl;
    }
    /* توسيط أزرار الاختيار والقوائم الأفقية */
    div.row-widget.stRadio > div {
        flex-direction: row;
        justify-content: center;
        text-align: center;
    }
    div.row-widget.stRadio > div[role='radiogroup'] {
        justify-content: center;
    }
    /* تصغير صندوق اختيار اللغة وجعله أنيقاً */
    [data-testid="stSelectbox"] {
        max-width: 150px;
        margin-right: auto;
        margin-left: auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------ Top Header: Small Language Selector & Centered Title
c_l, c_t, c_r = st.columns([2, 6, 2])

with c_r:
    lang_option = st.selectbox("Language / اللغة", ["العربية", "English"], label_visibility="collapsed")
lang_code = "ar" if lang_option == "العربية" else "en"

with c_t:
    st.markdown("<h1>Financial analysis Tech-Builder</h1>", unsafe_allow_html=True)

st.markdown("---")

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


# ------------------------------------------------------------------ Top Centered Main Menu
nav_titles = (
    ["إدارة الشركات", "تحليل شركة", "مقارنة شركات", "التقارير"]
    if lang_code == "ar"
    else ["Companies Management", "Company Analysis", "Compare Companies", "Reports"]
)

st.markdown(f"<h3>{'القائمة الرئيسية' if lang_code == 'ar' else 'Main Menu'}</h3>", unsafe_allow_html=True)

m_c1, m_c2, m_c3 = st.columns([1, 6, 1])
with m_c2:
    page = st.radio(
        "Main Menu",
        nav_titles,
        horizontal=True,
        label_visibility="collapsed"
    )

st.markdown(f"<p style='text-align: center; color: gray;'>{'عدد الشركات المحفوظة' if lang_code == 'ar' else 'Saved Companies'}: {len(companies)}</p>", unsafe_allow_html=True)
st.markdown("---")


# ================================================================== PAGE 1: companies
def page_companies():
    st.markdown(f"<h2>{'إدارة الشركات' if lang_code == 'ar' else 'Companies Management'}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p>{'أضف بيانات الشركة بإحدى الطرق: رفع ملف Excel، أو إدخال يدوي داخل البرنامج، أو بيانات تجريبية.' if lang_code == 'ar' else 'Add company data via Excel upload, manual entry, or sample data.'}</p>", unsafe_allow_html=True)

    tab_titles = ["رفع ملف Excel", "إدخال / تعديل يدوي", "الشركات المحفوظة"] if lang_code == "ar" else ["Excel Upload", "Manual Entry", "Saved Companies"]
    
    t_c1, t_c2, t_c3 = st.columns([1, 6, 1])
    with t_c2:
        tab_selection = st.radio("Sections", tab_titles, horizontal=True, label_visibility="collapsed")
    st.markdown("---")

    if tab_selection == tab_titles[0]:
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            st.download_button(
                "⬇️ تحميل قالب Excel فارغ (بقيم توضيحية)" if lang_code == "ar" else "⬇️ Download Empty Template",
                data=template_bytes(),
                file_name="company_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        st.caption("املأ الخلايا الزرقاء فقط. المصروفات تُدخل بأرقام موجبة. اسم الشركة من ورقة Info." if lang_code == "ar" else "Fill blue cells only.")
        files = st.file_uploader("ارفع ملف أو أكثر" if lang_code == "ar" else "Upload files", type=["xlsx", "xlsm"], accept_multiple_files=True)
        if files and st.button("استيراد الملفات" if lang_code == "ar" else "Import Files", type="primary"):
            for f in files:
                try:
                    c, warns = load_company_excel(f, filename=f.name)
                except Exception as e:  # noqa: BLE001
                    st.error(f"{f.name}: {e}")
                    continue
                add_company(c)
                st.success(f"تم استيراد «{c.name}» ({c.years[0]}–{c.years[-1]})")
                for w in warns:
                    st.warning(f"{f.name}: {w}")
        if st.button("إضافة شركتين تجريبيتين (للتجربة السريعة)" if lang_code == "ar" else "Add Sample Companies"):
            for c in sample_companies():
                add_company(c)
            st.success("تمت إضافة Nile Foods و Delta Tech.")

    elif tab_selection == tab_titles[1]:
        existing = ["— شركة جديدة —" if lang_code == "ar" else "— New Company —"] + list(companies)
        pick = st.selectbox("ابدأ من" if lang_code == "ar" else "Start from", existing)
        with st.form("meta_form"):
            c1, c2, c3 = st.columns(3)
            default = companies.get(pick) if pick in companies else None
            name = c1.text_input("اسم الشركة" if lang_code == "ar" else "Company Name", value=default.name if default else "")
            ticker = c2.text_input("الرمز (Ticker)", value=default.ticker if default else "")
            sector = c3.text_input("القطاع" if lang_code == "ar" else "Sector", value=default.sector if default else "")
            c4, c5, c6, c7 = st.columns(4)
            currency = c4.text_input("العملة" if lang_code == "ar" else "Currency", value=default.currency if default else "EGP")
            unit = c5.text_input("الوحدة" if lang_code == "ar" else "Unit", value=default.unit if default else "Millions")
            first_year = c6.number_input("أول سنة" if lang_code == "ar" else "First Year", 1990, 2100, value=default.years[0] if default else 2022)
            n_years = c7.number_input("عدد السنوات" if lang_code == "ar" else "Number of Years", 2, 10, value=len(default.years) if default else 3)
            if st.form_submit_button("تجهيز الجداول" if lang_code == "ar" else "Prepare Tables"):
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
            st.caption("المصروفات بأرقام موجبة. الإجماليات تُحسب تلقائياً.")
            if st.button("💾 حفظ الشركة" if lang_code == "ar" else "Save Company", type="primary"):
                meta = seed["meta"]
                if not meta["name"].strip():
                    st.error("اكتب اسم الشركة أولاً.")
                else:
                    try:
                        c = company_from_editor(meta["name"], inc_df, bal_df, ticker=meta["ticker"],
                                                sector=meta["sector"], currency=meta["currency"], unit=meta["unit"])
                        add_company(c)
                        st.success(f"تم حفظ «{c.name}».")
                        bad = balance_check(c).abs()
                        if (bad > 0.5).any():
                            st.warning("الميزانية غير متوازنة في السنوات: " + ", ".join(map(str, bad[bad > 0.5].index)))
                    except Exception as e:  # noqa: BLE001
                        st.error(str(e))

    else:
        if not companies:
            st.info("لا توجد شركات بعد.")
        else:
            rows = [{"الشركة": c.name, "الرمز": c.ticker, "القطاع": c.sector,
                     "السنوات": f"{c.years[0]}–{c.years[-1]}", "العملة / الوحدة": c.meta_line}
                    for c in companies.values()]
            st.dataframe(pd.DataFrame(rows), hide_index=True)
            col1, col2 = st.columns(2)
            victim = col1.selectbox("حذف شركة", list(companies))
            if col1.button("🗑️ حذف"):
                remove_company(victim)
                st.rerun()
            exp = col2.selectbox("تصدير بيانات الشركة كملف إدخال Excel", list(companies))
            col2.download_button(
                "⬇️ تحميل", data=build_workbook(companies[exp]), file_name=f"{slug(exp)}_input.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


# ================================================================== PAGE 2: analysis
def page_analysis():
    st.header("تحليل شركة" if lang_code == "ar" else "Company Analysis")
    if not companies:
        st.info("أضف شركة أولاً من صفحة «إدارة الشركات».")
        return
    name = st.selectbox("الشركة", list(companies))
    c = companies[name]
    st.caption(f"{c.meta_line} | {c.years[0]}–{c.years[-1]}" + (f" | {c.sector}" if c.sector else ""))

    for t in key_takeaways(c):
        st.markdown(f"- {t}")

    sub_tabs = ["قائمة الدخل", "الميزانية العمومية", "النسب المالية"] if lang_code == "ar" else ["Income Statement", "Balance Sheet", "Financial Ratios"]
    sub_col1, sub_col2, sub_col3 = st.columns([1, 5, 1])
    with sub_col2:
        sub_sel = st.radio("الأقسام", sub_tabs, horizontal=True, label_visibility="collapsed")
    st.markdown("---")

    inc, bs = income_statement(c), balance_sheet(c)

    if sub_sel == sub_tabs[0]:
        st.subheader("قائمة الدخل")
        show(inc)
        chart = pd.DataFrame({"Revenue": inc.loc["revenue"], "Net Income": inc.loc["net_income"]}).rename(index=str)
        st.bar_chart(chart)
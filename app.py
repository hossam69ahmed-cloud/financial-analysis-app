import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="برنامج التحليل المالي", layout="wide")

st.title("📊 نظام التحليل المالي وإعداد التقارير")
st.write("قم برفع ملف Excel يحتوي على الميزانية وقائمة الدخل، أو استخدم البيانات الافتراضية أدناه.")

# --- 1. قسم رفع البيانات ---
st.sidebar.header("📁 إدخال البيانات")
uploaded_file = st.sidebar.file_uploader("يرجى رفع ملف Excel (.xlsx)", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df_income = pd.read_excel(uploaded_file, sheet_name="Income Statement")
        df_balance = pd.read_excel(uploaded_file, sheet_name="Balance Sheet")
        st.sidebar.success("تم رفع الملف بنجاح!")
    except Exception as e:
        st.sidebar.error("يرجى التأكد من احتواء الملف على شيت باسم 'Income Statement' و 'Balance Sheet'")
else:
    st.info("💡 يتم استخدام بيانات توضيحية حالياً. يمكنك رفع ملفك الخاص من الشريط الجانبي.")
    df_income = pd.DataFrame({
        "البند": ["المبيعات", "تكلفة المبيعات", "مجمل الربح", "المصاريف التشغيلية", "صافي الربح"],
        "2023": [100000, 60000, 40000, 15000, 25000],
        "2024": [130000, 75000, 55000, 18000, 37000]
    })
    
    df_balance = pd.DataFrame({
        "البند": ["الأصول المتداولة", "الأصول الثابتة", "إجمالي الأصول", "الالتزامات المتداولة", "الالتزامات طويلة الأجل", "حقوق الملكية"],
        "2023": [30000, 70000, 100000, 15000, 25000, 60000],
        "2024": [45000, 80000, 125000, 20000, 30000, 75000]
    })

# --- تبويبات عرض البيانات والتحليل ---
tab1, tab2, tab3 = st.tabs(["📑 القوائم المالية", "📊 تحليل النسب والمقارنة", "💵 قائمة التدفقات النقدية"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("قائمة الدخل (Income Statement)")
        st.dataframe(df_income, use_container_width=True)
    with col2:
        st.subheader("الميزانية العمومية (Balance Sheet)")
        st.dataframe(df_balance, use_container_width=True)

with tab2:
    st.subheader("📈 تحليل ومقارنة النسب المالية عبر الفترات")
    years = [col for col in df_income.columns if col != "البند"]
    
    ratios_list = []
    for y in years:
        sales = df_income.loc[df_income["البند"] == "المبيعات", y].values[0]
        net_income = df_income.loc[df_income["البند"] == "صافي الربح", y].values[0]
        curr_assets = df_balance.loc[df_balance["البند"] == "الأصول المتداولة", y].values[0]
        total_assets = df_balance.loc[df_balance["البند"] == "إجمالي الأصول", y].values[0]
        curr_liab = df_balance.loc[df_balance["البند"] == "الالتزامات المتداولة", y].values[0]
        equity = df_balance.loc[df_balance["البند"] == "حقوق الملكية", y].values[0]
        
        ratios_list.append({
            "السنة": y,
            "هامش صافي الربح (%)": round((net_income / sales) * 100, 2),
            "نسبة السيولة الحالية": round(curr_assets / curr_liab, 2),
            "العائد على حقوق الملكية ROE (%)": round((net_income / equity) * 100, 2),
            "العائد على الأصول ROA (%)": round((net_income / total_assets) * 100, 2)
        })
    
    df_ratios = pd.DataFrame(ratios_list)
    st.table(df_ratios)

    st.subheader("📉 رسم بياني للمقارنة بين الفترات")
    selected_ratio = st.selectbox("اختر النسبة المالية للعرض:", [c for c in df_ratios.columns if c != "السنة"])
    fig = px.line(df_ratios, x="السنة", y=selected_ratio, markers=True, title=f"تطور {selected_ratio}")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("💡 قائمة التدفقات النقدية التقديرية (Cash Flow Statement)")
    if len(years) >= 2:
        y1, y2 = years[0], years[1]
        net_inc_y2 = df_income.loc[df_income["البند"] == "صافي الربح", y2].values[0]
        delta_curr_assets = df_balance.loc[df_balance["البند"] == "الأصول المتداولة", y2].values[0] - df_balance.loc[df_balance["البند"] == "الأصول المتداولة", y1].values[0]
        delta_curr_liab = df_balance.loc[df_balance["البند"] == "الالتزامات المتداولة", y2].values[0] - df_balance.loc[df_balance["البند"] == "الالتزامات المتداولة", y1].values[0]
        operating_cf = net_inc_y2 - delta_curr_assets + delta_curr_liab
        
        cf_data = {
            "نشاط التدفق": ["صافي دخل الفترة", "التغير في الأصول المتداولة", "التغير في الالتزامات المتداولة", "صافي التدفق النقدي التشغيلي"],
            "القيمة": [net_inc_y2, -delta_curr_assets, delta_curr_liab, operating_cf]
        }
        st.table(pd.DataFrame(cf_data))
    else:
        st.warning("تحتاج على الأقل لسنتين أو فترتين ماليتين لحساب التغير في التدفقات النقدية.")
    
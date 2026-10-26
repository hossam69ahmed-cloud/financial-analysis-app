import sqlite3
import pandas as pd
import streamlit as st

# إعداد الصفحة
st.set_page_config(
    page_title="نظام التحليل المالي وإدارة الشركات",
    page_icon="📊",
    layout="wide",
)

# --- إعداد قاعدة البيانات المحلية SQLite ---


def init_db():
  conn = sqlite3.connect("company_data.db")
  cursor = conn.cursor()

  # جدول المستخدمين والصلاحيات
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT,
            company TEXT,
            branch TEXT
        )
    """)

  # جدول الشركات والفروع
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies_branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            branch_name TEXT
        )
    """)

  # جدول حفظ البيانات المالية (الشركة، الفرع، الشهر، الحساب، القيمة)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            branch_name TEXT,
            month TEXT,
            account_name TEXT,
            amount REAL
        )
    """)

  # إضافة يوزر افتراضي رئيسي (Super Admin)
  cursor.execute("""
        INSERT OR IGNORE INTO users (username, password, role, company, branch)
        VALUES ('admin', '123456', 'Super Admin', 'الكل', 'الكل')
    """)

  conn.commit()
  conn.close()


init_db()

# --- إدارة حالة تسجيل الدخول ---
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.username = ""
  st.session_state.role = ""
  st.session_state.company = ""

# --- واجهة تسجيل الدخول ---
if not st.session_state.logged_in:
  st.title("🔐 تسجيل الدخول للنظام المتكامل")

  col1, col2 = st.columns(2)
  with col1:
    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور", type="password")

    if st.button("دخول"):
      conn = sqlite3.connect("company_data.db")
      cursor = conn.cursor()
      cursor.execute(
          "SELECT role, company FROM users WHERE username = ? AND password = ?",
          (username, password),
      )
      user = cursor.fetchone()
      conn.close()

      if user:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.role = user[0]
        st.session_state.company = user[1]
        st.success("تم تسجيل الدخول بنجاح!")
        st.rerun()
      else:
        st.error("اسم المستخدم أو كلمة المرور غير صحيحة")

  with col2:
    st.info(
        "💡 بيانات التجربة الافتراضية:\n- اسم المستخدم: **admin**\n- كلمة"
        " المرور: **123456**"
    )

else:
  # --- القائمة الجانبية ولوحة التحكم بعد تسجيل الدخول ---
  st.sidebar.title(f"مرحباً، {st.session_state.username}")
  st.sidebar.write(f"الصلاحية: **{st.session_state.role}**")
  st.sidebar.write(f"الشركة: **{st.session_state.company}**")

  menu = st.sidebar.radio(
      "القائمة الرئيسية",
      [
          "لوحة التحليل المالي",
          "إدارة الشركات والفروع",
          "رفع بيانات الشركات (Excel)",
      ],
  )

  if st.sidebar.button("تسجيل الخروج"):
    st.session_state.logged_in = False
    st.rerun()

  # --- شاشة إدارة الشركات والفروع ---
  if menu == "إدارة الشركات والفروع":
    st.title("🏢 إدارة الشركات والفروع")

    with st.form("add_company_form"):
      st.subheader("إضافة شركة أو فرع جديد")
      new_company = st.text_input("اسم الشركة")
      new_branch = st.text_input("اسم الفرع")
      submit_button = st.form_submit_button("حفظ وإضافة")

      if submit_button:
        if new_company and new_branch:
          conn = sqlite3.connect("company_data.db")
          cursor = conn.cursor()
          cursor.execute(
              "INSERT INTO companies_branches (company_name, branch_name) VALUES"
              " (?, ?)",
              (new_company, new_branch),
          )
          conn.commit()
          conn.close()
          st.success(
              f"تمت إضافة الشركة ({new_company}) والفرع ({new_branch}) بنجاح!"
          )
        else:
          st.warning("يرجى إدخال اسم الشركة واسم الفرع معاً.")

    st.subheader("📋 الشركات والفروع المسجلة بالنظام")
    conn = sqlite3.connect("company_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT company_name, branch_name FROM companies_branches")
    rows = cursor.fetchall()
    conn.close()

    if rows:
      for idx, row in enumerate(rows, 1):
        st.write(f"{idx}. الشركة: **{row[0]}** ــ الفرع: **{row[1]}**")
    else:
      st.info("لا توجد شركات مسجلة حتى الآن. يرجى إضافتها أولاً.")

  # --- شاشة رفع بيانات الـ Excel المخصصة (الحساب والقيمة + الشهر) ---
  elif menu == "رفع بيانات الشركات (Excel)":
    st.title("📁 رفع ملفات قائمة الدخل للشركات")

    conn = sqlite3.connect("company_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT company_name FROM companies_branches")
    companies = [row[0] for row in cursor.fetchall()]
    conn.close()

    if companies:
      col_a, col_b, col_c = st.columns(3)
      with col_a:
        selected_company = st.selectbox("اختر الشركة", companies)

      conn = sqlite3.connect("company_data.db")
      cursor = conn.cursor()
      cursor.execute(
          "SELECT branch_name FROM companies_branches WHERE company_name = ?",
          (selected_company,),
      )
      branches = [row[0] for row in cursor.fetchall()]
      conn.close()

      with col_b:
        selected_branch = st.selectbox("اختر الفرع", branches)

      with col_c:
        months_list = [
            "يناير",
            "فبراير",
            "مارس",
            "إبريل",
            "مايو",
            "يونيو",
            "يوليو",
            "أغسطس",
            "سبتمبر",
            "أكتوبر",
            "نوفمبر",
            "ديسمبر",
        ]
        selected_month = st.selectbox("اختر الشهر", months_list)

      st.markdown("---")
      st.subheader("📥 نموذج شيت قائمة الدخل القياسي")
      st.write(
          "يجب أن يحتوي ملف الـ Excel على العمودين التاليين بدقة: **الحساب,"
          " القيمة**"
      )

      # القالب القياسي لبنود قائمة الدخل المطلوبة
      template_df = pd.DataFrame({
          "الحساب": [
              "المبيعات",
              "تكلفة البضاعة المباعة",
              "المصاريف البيعية و التشغيلية",
              "المصاريف العمومية و الادارية",
              "الاهلاك",
              "الضرائب",
          ],
          "القيمة": [150000, 80000, 20000, 15000, 5000, 4000],
      })

      data_as_csv = template_df.to_csv(index=False).encode("utf-8-sig")

      st.download_button(
          label="تحميل نموذج شيت قائمة الدخل القياسي (CSV)",
          data=data_as_csv,
          file_name="income_statement_template.csv",
          mime="text/csv",
      )

      st.markdown("---")
      uploaded_file = st.file_uploader(
          "ارفع الشيت المعبأ (يجب أن يحتوي على عمود 'الحساب' و 'القيمة')",
          type=["xlsx", "xls", "csv"],
      )

      if uploaded_file is not None:
        try:
          if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
          else:
            df = pd.read_excel(uploaded_file)

          required_columns = ["الحساب", "القيمة"]

          if all(col in df.columns for col in required_columns):
            st.success(
                f"✅ تم التحقق بنجاح | الشركة: {selected_company} | الفرع:"
                f" {selected_branch} | الشهر: {selected_month}"
            )
            st.dataframe(df)

            if st.button("💾 حفظ بيانات الشهر في قاعدة البيانات"):
              conn = sqlite3.connect("company_data.db")
              cursor = conn.cursor()

              # حذف بيانات نفس الشهر القديمة لنفس الشركة والفرع لعدم التكرار
              cursor.execute(
                  """
                                DELETE FROM financial_data 
                                WHERE company_name = ? AND branch_name = ? AND month = ?
                            """,
                  (selected_company, selected_branch, selected_month),
              )

              # إدخال البنود الجديدة
              for _, row in df.iterrows():
                cursor.execute(
                    """
                                    INSERT INTO financial_data (company_name, branch_name, month, account_name, amount)
                                    VALUES (?, ?, ?, ?, ?)
                                """,
                    (
                        selected_company,
                        selected_branch,
                        selected_month,
                        row["الحساب"],
                        row["القيمة"],
                    ),
                )

              conn.commit()
              conn.close()
              st.success(
                  f"🎉 تم حفظ بيانات شهر ({selected_month}) بنجاح تام في قاعدة"
                  " البيانات!"
              )
          else:
            st.error(
                "❌ الأعمدة غير مطابقة! يجب أن يحتوي الشيت على الأعمدة الآتية:"
                f" {required_columns}"
            )
            st.info(
                "💡 نصيحة: حمل النموذج القياسي من الزر أعلاه واملأه بنفس الأسماء."
            )
        except Exception as e:
          st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
    else:
      st.warning(
          "يرجى الانتقال إلى صفحة 'إدارة الشركات والفروع' وإضافة شركة واحدة على"
          " الأقل أولاً."
      )

  # --- شاشة لوحة التحليل المالي وعرض التقارير الشهرية ---
  elif menu == "لوحة التحليل المالي":
    st.title("📊 لوحة تحكم التحليل المالي وقوائم الدخل")

    conn = sqlite3.connect("company_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT company_name FROM companies_branches")
    companies = [row[0] for row in cursor.fetchall()]
    conn.close()

    if companies:
      col_v1, col_v2, col_v3 = st.columns(3)
      with col_v1:
        view_company = st.selectbox(
            "اختر الشركة للعرض", companies, key="v_comp"
        )

      conn = sqlite3.connect("company_data.db")
      cursor = conn.cursor()
      cursor.execute(
          "SELECT branch_name FROM companies_branches WHERE company_name = ?",
          (view_company,),
      )
      branches = [row[0] for row in cursor.fetchall()]
      conn.close()

      with col_v2:
        view_branch = st.selectbox(
            "اختر الفرع للعرض", branches if branches else [""], key="v_branch"
        )

      with col_v3:
        months_list = [
            "يناير",
            "فبراير",
            "مارس",
            "إبريل",
            "مايو",
            "يونيو",
            "يوليو",
            "أغسطس",
            "سبتمبر",
            "أكتوبر",
            "نوفمبر",
            "ديسمبر",
        ]
        view_month = st.selectbox("اختر الشهر للعرض", months_list, key="v_month")

      st.markdown("---")

      # جلب البيانات من قاعدة البيانات للشهر والشركة والفرع المحددين
      conn = sqlite3.connect("company_data.db")
      cursor = conn.cursor()
      cursor.execute(
          """
                SELECT account_name as "الحساب", amount as "القيمة" 
                FROM financial_data 
                WHERE company_name = ? AND branch_name = ? AND month = ?
            """,
          (view_company, view_branch, view_month),
      )
      rows = cursor.fetchall()
      conn.close()

      if rows:
        st.subheader(
            f"📄 قائمة الدخل لشهر ({view_month}) - الشركة: {view_company}"
            f" (فرع: {view_branch})"
        )
        df_display = pd.DataFrame(rows, columns=["الحساب", "القيمة"])
        st.table(df_display)

        # حساب مؤشرات سريعة (مجمل الربح وصافي الربح بناءً على البنود)
        try:
          # تحويل البيانات إلى قاموس لتسهيل العمليات الحسابية
          fin_dict = dict(zip(df_display["الحساب"], df_display["القيمة"]))
          sales = fin_dict.get("المبيعات", 0)
          cogs = fin_dict.get("تكلفة البضاعة المباعة", 0)
          gp = sales - cogs  # مجمل الربح
          opex = fin_dict.get("المصاريف البيعية و التشغيلية", 0) + fin_dict.get(
              "المصاريف العمومية و الادارية", 0
          )
          depr = fin_dict.get("الاهلاك", 0)
          net_before_tax = gp - opex - depr
          taxes = fin_dict.get("الضرائب", 0)
          net_profit = net_before_tax - taxes

          st.markdown("---")
          st.subheader("💡 مؤشرات الأداء المالي التلقائية للشهر")
          mcol1, mcol2, mcol3 = st.columns(3)
          mcol1.metric("مجمل الربح (Gross Profit)", f"{gp:,.2f}")
          mcol2.metric("صافي الربح قبل الضرائب", f"{net_before_tax:,.2f}")
          mcol3.metric("صافي الربح النهائي (Net Profit)", f"{net_profit:,.2f}")
        except Exception:
          pass

        st.markdown("---")
        st.subheader("📈 تمثيل بياني لبنود الحسابات")
        st.bar_chart(df_display.set_index("الحساب"))
      else:
        st.info(
            f"ℹ️ لا توجد بيانات مسجلة لشهر ({view_month}) للشركة ({view_company})"
            f" - فرع ({view_branch})."
        )
    else:
      st.warning("لا توجد شركات مسجلة بالنظام لعرض تقاريرها.")

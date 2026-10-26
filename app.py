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

  # جدول حفظ البيانات المالية للشركات والفروع
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            branch_name TEXT,
            item TEXT,
            val_2023 REAL,
            val_2024 REAL
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

  # --- شاشة رفع بيانات الـ Excel للشركة والفرع مع الحفظ ---
  elif menu == "رفع بيانات الشركات (Excel)":
    st.title("📁 رفع ملفات التحليل المالي للشركات")

    conn = sqlite3.connect("company_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT company_name FROM companies_branches")
    companies = [row[0] for row in cursor.fetchall()]
    conn.close()

    if companies:
      selected_company = st.selectbox("اختر الشركة", companies)

      conn = sqlite3.connect("company_data.db")
      cursor = conn.cursor()
      cursor.execute(
          "SELECT branch_name FROM companies_branches WHERE company_name = ?",
          (selected_company,),
      )
      branches = [row[0] for row in cursor.fetchall()]
      conn.close()

      selected_branch = st.selectbox("اختر الفرع", branches)

      st.markdown("---")
      st.subheader("📥 نموذج شيت الـ Excel القياسي")
      st.write(
          "يجب أن يحتوي ملف الـ Excel المرفوع على الأعمدة التالية بدقة: **البند,"
          " 2023, 2024**"
      )

      template_df = pd.DataFrame({
          "البند": [
              "المبيعات",
              "تكلفة المبيعات",
              "مجمل الربح",
              "المصاريف التشغيلية",
              "صافي الربح",
          ],
          "2023": [100000, 60000, 40000, 15000, 25000],
          "2024": [130000, 75000, 55000, 18000, 37000],
      })

      data_as_csv = template_df.to_csv(index=False).encode("utf-8-sig")

      st.download_button(
          label="تحميل نموذج الشيت القياسي (CSV)",
          data=data_as_csv,
          file_name="financial_template.csv",
          mime="text/csv",
      )

      st.markdown("---")
      uploaded_file = st.file_uploader(
          "ارفع الشيت المعبأ (يجب أن يطابق الهيكل القياسي)",
          type=["xlsx", "xls", "csv"],
      )

      if uploaded_file is not None:
        try:
          if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
          else:
            df = pd.read_excel(uploaded_file)

          required_columns = ["البند", "2023", "2024"]

          if all(col in df.columns for col in required_columns):
            st.success(
                f"✅ تم التحقق من صحة الملف بنجاح للشركة: {selected_company} -"
                f" الفرع: {selected_branch}"
            )
            st.dataframe(df)

            if st.button("💾 حفظ البيانات في قاعدة البيانات"):
              conn = sqlite3.connect("company_data.db")
              cursor = conn.cursor()

              # حذف البيانات القديمة لنفس الشركة والفرع لعدم التكرار (اختياري)
              cursor.execute(
                  "DELETE FROM financial_data WHERE company_name = ? AND"
                  " branch_name = ?",
                  (selected_company, selected_branch),
              )

              # إدخال البيانات الجديدة السطر تلو الآخر
              for _, row in df.iterrows():
                cursor.execute(
                    """
                                    INSERT INTO financial_data (company_name, branch_name, item, val_2023, val_2024)
                                    VALUES (?, ?, ?, ?, ?)
                                """,
                    (
                        selected_company,
                        selected_branch,
                        row["البند"],
                        row["2023"],
                        row["2024"],
                    ),
                )

              conn.commit()
              conn.close()
              st.success(
                  "🎉 تم حفظ البيانات المالية في قاعدة البيانات بنجاح تام!"
              )
          else:
            st.error(
                "❌ الملف المرفوع لا يطابق الهيكل المطلوب! يجب أن تحتوي الأعمدة"
                f" على: {required_columns}"
            )
            st.info(
                "💡 نصيحة: قم بتحميل النموذج القياسي بالأعلى واستخدمه مباشرة."
            )
        except Exception as e:
          st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
    else:
      st.warning(
          "يرجى الانتقال إلى صفحة 'إدارة الشركات والفروع' وإضافة شركة واحدة على"
          " الأقل أولاً."
      )

  # --- شاشة لوحة التحليل المالي وعرض البيانات المخزنة ---
  elif menu == "لوحة التحليل المالي":
    st.title("📊 لوحة تحكم التحليل المالي والتقارير")

    # اختيار الشركة والفرع لعرض تقاريرها
    conn = sqlite3.connect("company_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT company_name FROM companies_branches")
    companies = [row[0] for row in cursor.fetchall()]
    conn.close()

    if companies:
      col_c1, col_c2 = st.columns(2)
      with col_c1:
        view_company = st.selectbox("اختر الشركة للعرض", companies, key="v_comp")

      conn = sqlite3.connect("company_data.db")
      cursor = conn.cursor()
      cursor.execute(
          "SELECT branch_name FROM companies_branches WHERE company_name = ?",
          (view_company,),
      )
      branches = [row[0] for row in cursor.fetchall()]
      conn.close()

      with col_c2:
        if branches:
          view_branch = st.selectbox(
              "اختر الفرع للعرض", branches, key="v_branch"
          )
        else:
          view_branch = ""

      st.markdown("---")
      # جلب البيانات من قاعدة البيانات للشركة والفرع المختارين
      conn = sqlite3.connect("company_data.db")
      cursor = conn.cursor()
      cursor.execute(
          """
                SELECT item as "البند", val_2023 as "2023", val_2024 as "2024" 
                FROM financial_data 
                WHERE company_name = ? AND branch_name = ?
            """,
          (view_company, view_branch),
      )
      rows = cursor.fetchall()
      conn.close()

      if rows:
        st.subheader(
            f"📄 القوائم المالية للشركة: {view_company} (فرع: {view_branch})"
        )
        df_display = pd.DataFrame(
            rows, columns=["البند", "2023", "2024"]
        )
        st.table(df_display)

        # رسوم بيانية سريعة أو مؤشرات
        st.markdown("---")
        st.subheader("📈 مقارنة أداء البنود بين عامي 2023 و 2024")
        st.bar_chart(df_display.set_index("البند"))
      else:
        st.info(
            f"ℹ️ لا توجد بيانات مرفوعة حتى الآن للشركة ({view_company}) - الفرع"
            f" ({view_branch}). انتقل إلى صفحة 'رفع بيانات الشركات (Excel)' لرفع"
            " ملفها."
        )
    else:
      st.warning("لا توجد شركات مسجلة بالنظام لعرض تقاريرها.")

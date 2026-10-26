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

  # جدول البيانات المالية الشاملة
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_data_detailed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            branch_name TEXT,
            month TEXT,
            main_account TEXT,
            sub_account TEXT,
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
  st.title("🔐 تسجيل الدخول للنظام المالي المتكامل")

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
  # --- القائمة الجانبية ولوحة التحكم ---
  st.sidebar.title(f"مرحباً، {st.session_state.username}")
  st.sidebar.write(f"الصلاحية: **{st.session_state.role}**")

  menu = st.sidebar.radio(
      "القائمة الرئيسية",
      [
          "📈 التقارير المالية والتحليل التلقائي",
          "🏢 إدارة الشركات والفروع",
          "📁 رفع شيت الحسابات الشامل (Excel)",
          "🗑️ حذف وإدارة البيانات",
      ],
  )

  if st.sidebar.button("تسجيل الخروج"):
    st.session_state.logged_in = False
    st.rerun()

  # --- شاشة إدارة الشركات والفروع ---
  if menu == "🏢 إدارة الشركات والفروع":
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
      st.info("لا توجد شركات مسجلة حتى الآن.")

  # --- شاشة رفع شيت الحسابات الشامل ---
  elif menu == "📁 رفع شيت الحسابات الشامل (Excel)":
    st.title("📁 رفع شيت الحسابات الشامل (يوزع تلقائياً على كل التقارير)")

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
      st.subheader("📥 نموذج الشيت القياسي الشامل")
      st.write(
          "ارفع شيت واحد يحتوي على كل حسابات الشركة (قائمة دخل + ميزانية + مصاريف)"
          " بالأعمدة الثلاثة:"
          " **الحساب الرئيسي، الحساب الفرعي، القيمة**"
      )

      template_df = pd.DataFrame({
          "الحساب الرئيسي": [
              "المبيعات",
              "تكلفة البضاعة المباعة",
              "مصاريف بيعية و تشغيلية",
              "مصاريف عمومية و ادارية",
              "الاهلاك",
              "الضرائب",
              "الأصول غير المتداولة",
              "الأصول المتداولة",
              "التزامات متداولة",
              "حقوق الملكية",
          ],
          "الحساب الفرعي": [
              "مبيعات محلية",
              "مشتريات مواد خام",
              "مرتبات المعارض",
              "إيجار الإدارة",
              "إهلاك الأصول",
              "ضريبة الدخل",
              "الآلات والمعدات",
              "النقدية بالبنك",
              "الموردون",
              "رأس المال",
          ],
          "القيمة": [
              150000,
              80000,
              20000,
              15000,
              5000,
              4000,
              300000,
              50000,
              30000,
              320000,
          ],
      })

      data_as_csv = template_df.to_csv(index=False).encode("utf-8-sig")

      st.download_button(
          label="تحميل نموذج الشيت الشامل القياسي (CSV)",
          data=data_as_csv,
          file_name="comprehensive_financial_template.csv",
          mime="text/csv",
      )

      st.markdown("---")
      uploaded_file = st.file_uploader(
          "ارفع الشيت الشامل (أعمدة: الحساب الرئيسي، الحساب الفرعي، القيمة)",
          type=["xlsx", "xls", "csv"],
      )

      if uploaded_file is not None:
        try:
          if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
          else:
            df = pd.read_excel(uploaded_file)

          required_columns = ["الحساب الرئيسي", "الحساب الفرعي", "القيمة"]

          if all(col in df.columns for col in required_columns):
            st.success(
                f"✅ تم التحقق بنجاح | الشركة: {selected_company} | الفرع:"
                f" {selected_branch} | الشهر: {selected_month}"
            )
            st.dataframe(df)

            if st.button("💾 حفظ الشيت الشامل في قاعدة البيانات"):
              conn = sqlite3.connect("company_data.db")
              cursor = conn.cursor()

              cursor.execute(
                  """
                                DELETE FROM financial_data_detailed 
                                WHERE company_name = ? AND branch_name = ? AND month = ?
                            """,
                  (selected_company, selected_branch, selected_month),
              )

              for _, row in df.iterrows():
                cursor.execute(
                    """
                                    INSERT INTO financial_data_detailed (company_name, branch_name, month, main_account, sub_account, amount)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """,
                    (
                        selected_company,
                        selected_branch,
                        selected_month,
                        row["الحساب الرئيسي"],
                        row["الحساب الفرعي"],
                        row["القيمة"],
                    ),
                )

              conn.commit()
              conn.close()
              st.success(
                  f"🎉 تم حفظ وترحيل بيانات شهر ({selected_month}) لكل التقارير"
                  " بنجاح!"
              )
          else:
            st.error(
                "❌ الأعمدة غير مطابقة! يجب أن يكون الشيت بالأعمدة الآتية:"
                f" {required_columns}"
            )
        except Exception as e:
          st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
    else:
      st.warning(
          "يرجى الانتقال إلى صفحة 'إدارة الشركات والفروع' وإضافة شركة واحدة على"
          " الأقل أولاً."
      )

  # --- شاشة حذف وإدارة البيانات ---
  elif menu == "🗑️ حذف وإدارة البيانات":
    st.title("🗑️ إدارة وحذف البيانات المالية المسجلة")
    st.write(
        "يمكنك من خلال هذه الصفحة حذف بيانات شهر معين لشركة وفرع محدد لإعادة"
        " رفعها أو تعديلها."
    )

    conn = sqlite3.connect("company_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT company_name FROM companies_branches")
    companies = [row[0] for row in cursor.fetchall()]
    conn.close()

    if companies:
      d_col1, d_col2, d_col3 = st.columns(3)
      with d_col1:
        del_company = st.selectbox(
            "اختر الشركة للحذف", companies, key="del_comp"
        )

      conn = sqlite3.connect("company_data.db")
      cursor = conn.cursor()
      cursor.execute(
          "SELECT branch_name FROM companies_branches WHERE company_name = ?",
          (del_company,),
      )
      branches = [row[0] for row in cursor.fetchall()]
      conn.close()

      with d_col2:
        del_branch = st.selectbox(
            "اختر الفرع", branches if branches else [""], key="del_branch"
        )

      with d_col3:
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
        del_month = st.selectbox("اختر الشهر المراد حذفه", months_list, key="del_month")

      st.markdown("---")

      # عرض البيانات الحالية لهذا الشهر قبل الحذف للتأكد
      conn = sqlite3.connect("company_data.db")
      cursor = conn.cursor()
      cursor.execute(
          """
                SELECT main_account as "الحساب الرئيسي", sub_account as "الحساب الفرعي", amount as "القيمة"
                FROM financial_data_detailed 
                WHERE company_name = ? AND branch_name = ? AND month = ?
            """,
          (del_company, del_branch, del_month),
      )
      current_data = cursor.fetchall()
      conn.close()

      if current_data:
        st.warning(
            f"⚠️ توجد بيانات مسجلة لشهر ({del_month}) للشركة ({del_company}) -"
            f" الفرع ({del_branch}). عدد البنود المسجلة: {len(current_data)}"
        )
        df_current = pd.DataFrame(
            current_data, columns=["الحساب الرئيسي", "الحساب الفرعي", "القيمة"]
        )
        st.dataframe(df_current, use_container_width=True)

        if st.button("🗑️ تأكيد وحذف بيانات هذا الشهر نهائياً"):
          conn = sqlite3.connect("company_data.db")
          cursor = conn.cursor()
          cursor.execute(
              """
                        DELETE FROM financial_data_detailed 
                        WHERE company_name = ? AND branch_name = ? AND month = ?
                    """,
              (del_company, del_branch, del_month),
          )
          conn.commit()
          conn.close()
          st.success(
              f"✅ تم حذف بيانات شهر ({del_month}) بنجاح تام من قاعدة البيانات!"
          )
          st.rerun()
      else:
        st.info(
            f"ℹ️ لا توجد بيانات مسجلة أساساً لشهر ({del_month}) لهذه الشركة والفرع."
        )
    else:
      st.warning("لا توجد شركات مسجلة بالنظام.")

  # --- شاشة التقارير المالية المتقدمة والتحليل التلقائي ---
  elif menu == "📈 التقارير المالية والتحليل التلقائي":
    st.title("📊 لوحة التقارير المالية الموزعة تلقائياً")

    conn = sqlite3.connect("company_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT company_name FROM companies_branches")
    companies = [row[0] for row in cursor.fetchall()]
    conn.close()

    if companies:
      col_f1, col_f2, col_f3 = st.columns(3)
      with col_f1:
        view_company = st.selectbox(
            "اختر الشركة", companies, key="rep_comp"
        )

      conn = sqlite3.connect("company_data.db")
      cursor = conn.cursor()
      cursor.execute(
          "SELECT branch_name FROM companies_branches WHERE company_name = ?",
          (view_company,),
      )
      branches = [row[0] for row in cursor.fetchall()]
      conn.close()

      with col_f2:
        view_branch = st.selectbox(
            "اختر الفرع", branches if branches else [""], key="rep_branch"
        )

      with col_f3:
        report_type = st.selectbox(
            "اختر نوع التقرير",
            [
                "تقرير قائمة الدخل",
                "تقرير الميزانية العمومية",
                "تقرير قائمة التدفقات النقدية",
                "تقرير تحليل المصاريف",
            ],
        )

      st.markdown("---")

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
      col_m1, col_m2 = st.columns(2)
      with col_m1:
        month_1 = st.selectbox("اختر الشهر الأول (الأساس)", months_list, index=0)
      with col_m2:
        month_2 = st.selectbox("اختر الشهر الثاني (المقارنة)", months_list, index=1)

      st.markdown("---")


      def get_month_data(m_name):
        conn = sqlite3.connect("company_data.db")
        cursor = conn.cursor()
        cursor.execute(
            """
                    SELECT main_account, sub_account, amount 
                    FROM financial_data_detailed 
                    WHERE company_name = ? AND branch_name = ? AND month = ?
                """,
            (view_company, view_branch, m_name),
        )
        res

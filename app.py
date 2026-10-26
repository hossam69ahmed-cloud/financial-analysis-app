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

  # جدول البيانات المالية (الشركة، الفرع، الشهر، القسم الرئيسي، الحساب الفرعي، القيمة)
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
          "📈 التقارير المالية والتحليل",
          "🏢 إدارة الشركات والفروع",
          "📁 رفع بيانات الشركات (Excel)",
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

  # --- شاشة رفع بيانات الـ Excel المتقدمة ---
  elif menu == "📁 رفع بيانات الشركات (Excel)":
    st.title("📁 رفع ملفات الحسابات المالية (رئيسي وفرعي)")

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
      st.subheader("📥 نموذج الشيت القياسي المطلوب")
      st.write(
          "يجب أن يحتوي ملف الـ Excel على الأعمدة الثلاثة التالية بدقة:"
          " **الحساب الرئيسي، الحساب الفرعي، القيمة**"
      )

      # قالب قياسي جاهز للتحميل
      template_df = pd.DataFrame({
          "الحساب الرئيسي": [
              "المبيعات",
              "المبيعات",
              "تكلفة البضاعة المباعة",
              "مصاريف بيعية و تشغيلية",
              "مصاريف عمومية و ادارية",
              "الاهلاك",
              "الضرائب",
          ],
          "الحساب الفرعي": [
              "مبيعات محليه",
              "مبيعات تصدير",
              "مشتريات مواد خام",
              "مرتبات رجال المعارض",
              "إيجار الإدارة",
              "إهلاك الأصول الثابتة",
              "ضريبة الدخل",
          ],
          "القيمة": [100000, 50000, 80000, 20000, 15000, 5000, 4000],
      })

      data_as_csv = template_df.to_csv(index=False).encode("utf-8-sig")

      st.download_button(
          label="تحميل نموذج الشيت القياسي (CSV)",
          data=data_as_csv,
          file_name="detailed_financial_template.csv",
          mime="text/csv",
      )

      st.markdown("---")
      uploaded_file = st.file_uploader(
          "ارفع الشيت المعبأ (أعمدة: الحساب الرئيسي، الحساب الفرعي، القيمة)",
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

            if st.button("💾 حفظ البيانات في قاعدة البيانات"):
              conn = sqlite3.connect("company_data.db")
              cursor = conn.cursor()

              # مسح بيانات نفس الشهر القديمة لنفس الشركة والفرع لعدم التكرار
              cursor.execute(
                  """
                                DELETE FROM financial_data_detailed 
                                WHERE company_name = ? AND branch_name = ? AND month = ?
                            """,
                  (selected_company, selected_branch, selected_month),
              )

              # إدخال السطور الجديدة
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
                  f"🎉 تم حفظ بيانات شهر ({selected_month}) بنجاح تام!"
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

  # --- شاشة التقارير المالية والتحليل الشامل ---
  elif menu == "📈 التقارير المالية والتحليل":
    st.title("📊 لوحة التقارير المالية المتقدمة")

    conn = sqlite3.connect("company_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT company_name FROM companies_branches")
    companies = [row[0] for row in cursor.fetchall()]
    conn.close()

    if companies:
      # فلاتر اختيار الشركة والفرع والتقرير المطلوب
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

      # اختيار الشهرين للمقارنة وحساب التغير
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
        month_1 = st.selectbox("اختر الشهر الأول (الأساس / القديم)", months_list, index=0)
      with col_m2:
        month_2 = st.selectbox("اختر الشهر الثاني (المقارنة / الحديث)", months_list, index=1)

      st.markdown("---")

      # دالة لجلب بيانات شهر معين
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
        res = cursor.fetchall()
        conn.close()
        return pd.DataFrame(res, columns=["الحساب الرئيسي", "الحساب الفرعي", "القيمة"])

      df1 = get_month_data(month_1)
      df2 = get_month_data(month_2)

      if not df1.empty or not df2.empty:
        st.subheader(f"📄 {report_type} | مقارنة بين ({month_1}) و ({month_2})")

        # معالجة التقارير بناءً على الاختيار
        if report_type == "تقرير قائمة الدخل":
          # تصفية بنود قائمة الدخل (المبيعات، التكلفة، المصاريف، الإهلاك، الضرائب)
          valid_main_accounts = [
              "المبيعات",
              "تكلفة البضاعة المباعة",
              "مصاريف بيعية و تشغيلية",
              "مصاريف عمومية و ادارية",
              "الاهلاك",
              "الضرائب",
          ]
          df1_filtered = df1[df1["الحساب الرئيسي"].isin(valid_main_accounts)] if not df1.empty else pd.DataFrame(columns=["الحساب الرئيسي", "الحساب الفرعي", "القيمة"])
          df2_filtered = df2[df2["الحساب الرئيسي"].isin(valid_main_accounts)] if not df2.empty else pd.DataFrame(columns=["الحساب الرئيسي", "الحساب الفرعي", "القيمة"])

          # دمج الشهرين لعرض مقارنة تفصيلية للحسابات الفرعية والرئيسية
          merged_df = pd.merge(
              df1_filtered,
              df2_filtered,
              on=["الحساب الرئيسي", "الحساب الفرعي"],
              how="outer",
              suffixes=(f" ({month_1})", f" ({month_2})"),
          ).fillna(0)

          col_val1 = f"القيمة ({month_1})"
          col_val2 = f"القيمة ({month_2})"

          merged_df["قيمة التغير"] = merged_df[col_val2] - merged_df[col_val1]
          merged_df["نسبة التغيير (%)"] = (
              (merged_df["قيمة التغير"] / merged_df[col_val1].replace(0, 1))
              * 100
          ).round(2)

          st.dataframe(merged_df, use_container_width=True)

          # حساب صافي الدخل والمؤشرات
          sales_1 = df1_filtered[df1_filtered["الحساب الرئيسي"] == "المبيعات"]["القيمة"].sum() if not df1_filtered.empty else 0
          sales_2 = df2_filtered[df2_filtered["الحساب الرئيسي"] == "المبيعات"]["القيمة"].sum() if not df2_filtered.empty else 0
          
          st.markdown("### 💡 ملخص مؤشرات قائمة الدخل")
          sc1, sc2 = st.columns(2)
          sc1.metric(f"إجمالي مبيعات {month_1}", f"{sales_1:,.2f}")
          sc2.metric(f"إجمالي مبيعات {month_2}", f"{sales_2:,.2f}", delta=f"{sales_2 - sales_1:,.2f}")

        elif report_type == "تقرير تحليل المصاريف":
          expense_accounts = [
              "مصاريف بيعية و تشغيلية",
              "مصاريف عمومية و ادارية",
              "الاهلاك",
          ]
          df1_exp = df1[df1["الحساب الرئيسي"].isin(expense_accounts)] if not df1.empty else pd.DataFrame()
          df2_exp = df2[df2["الحساب الرئيسي"].isin(expense_accounts)] if not df2.empty else pd.DataFrame()

          merged_exp = pd.merge(
              df1_exp,
              df2_exp,
              on=["الحساب الرئيسي", "الحساب الفرعي"],
              how="outer",
              suffixes=(f" ({month_1})", f" ({month_2})"),
          ).fillna(0)

          col_val1 = f"القيمة ({month_1})"
          col_val2 = f"القيمة ({month_2})"
          merged_exp["قيمة التغير"] = merged_exp[col_val2] - merged_exp[col_val1]
          merged_exp["نسبة التغيير (%)"] = (
              (merged_exp["قيمة التغير"] / merged_exp[col_val1].replace(0, 1))
              * 100
          ).round(2)

          st.subheader("📊 تحليل المصاريف التشغيلية والإدارية")
          st.dataframe(merged_exp, use_container_width=True)
          if not merged_exp.empty:
            st.bar_chart(merged_exp.set_index("الحساب الفرعي")[[col_val1, col_val2]])

        else:
          # لبقية التقارير (الميزانية العمومية / التدفقات النقدية إذا لم ترفع تفاصيلها بعد)
          merged_general = pd.merge(
              df1,
              df2,
              on=["الحساب الرئيسي", "الحساب الفرعي"],
              how="outer",
              suffixes=(f" ({month_1})", f" ({month_2})"),
          ).fillna(0)
          col_val1 = f"القيمة ({month_1})"
          col_val2 = f"القيمة ({month_2})"
          merged_general["قيمة التغير"] = merged_general[col_val2] - merged_general[col_val1]
          merged_general["نسبة التغيير (%)"] = (
              (merged_general["قيمة التغير"] / merged_general[col_val1].replace(0, 1))
              * 100
          ).round(2)

          st.info(f"عرض بيانات {report_type} بناءً على الحسابات المسجلة للشهرين:")
          st.dataframe(merged_general, use_container_width=True)

      else:
        st.warning(
            f"⚠️ لا توجد بيانات مسجلة للشهرين المختارين ({month_1}) أو"
            f" ({month_2}) لهذه الشركة والفرع."
        )
    else:
      st.warning("لا توجد شركات مسجلة بالنظام لعرض تقاريرها.")

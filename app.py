import sqlite3
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
  # إضافة يوزر افتراضي رئيسي (Super Admin) إذا لم يكن موجوداً
  cursor.execute("""
        OR IGNORE INTO users (username, password, role, company, branch)
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
  # --- لوحة التحكم بعد تسجيل الدخول ---
  st.sidebar.title(f"مرحباً، {st.session_state.username}")
  st.sidebar.write(f"الصلاحية: **{st.session_state.role}**")
  st.sidebar.write(f"الشركة: **{st.session_state.company}**")

  if st.sidebar.button("تسجيل الخروج"):
    st.session_state.logged_in = False
    st.rerun()

  st.title("📊 لوحة تحكم التحليل المالي والشركات المتعددة")
  st.write(
      "تم تفعيل نظام الصلاحيات وقاعدة البيانات بنجاح. سنقوم الآن بإضافة شاشات"
      " إدارة الشركات والفروع ورفع البيانات الخاصة بكل شركة."
  )

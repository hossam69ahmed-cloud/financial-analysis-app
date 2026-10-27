"""Translations module for Financial Analyzer."""

TRANSLATIONS = {
    "ar": {
        "title": "Financial analysis Tech-Builder",
        "main_menu": "القائمة الرئيسية",
        "saved_companies": "عدد الشركات المحفوظة",
        "menu_items": ["إدارة الشركات", "تحليل شركة", "مقارنة شركات", "التقارير"],
        
        # صفحة إدارة الشركات
        "companies_mgmt": "إدارة الشركات",
        "companies_desc": "أضف بيانات الشركة بإحدى الطرق: رفع ملف Excel، أو إدخال يدوي داخل البرنامج، أو بيانات تجريبية.",
        "tabs_companies": ["رفع ملف Excel", "إدخال / تعديل يدوي", "الشركات المحفوظة"],
        
        # تحليل الشركة
        "company_analysis": "تحليل شركة",
        "sub_tabs_analysis": ["قائمة الدخل", "الميزانية العمومية", "النسب المالية"],
        
        # مقارنة الشركات
        "compare_companies": "مقارنة شركات",
        
        # التقارير
        "reports": "التقارير",
    },
    "en": {
        "title": "Financial analysis Tech-Builder",
        "main_menu": "Main Menu",
        "saved_companies": "Saved Companies",
        "menu_items": ["Companies Management", "Company Analysis", "Compare Companies", "Reports"],
        
        # Companies Management
        "companies_mgmt": "Companies Management",
        "companies_desc": "Add company data via Excel upload, manual entry, or sample data.",
        "tabs_companies": ["Excel Upload", "Manual Entry", "Saved Companies"],
        
        # Company Analysis
        "company_analysis": "Company Analysis",
        "sub_tabs_analysis": ["Income Statement", "Balance Sheet", "Financial Ratios"],
        
        # Compare Companies
        "compare_companies": "Compare Companies",
        
        # Reports
        "reports": "Reports",
    }
}

def translate_takeaway(t: str, lang: str) -> str:
    if lang != "ar":
        return t
    
    import re
    # ترجمة إحصاءات الإيرادات
    m = re.search(r'Revenue moved from (.*?) in (\d+) to (.*?) in (\d+) \(CAGR (.*?)\)', t)
    if m:
        return f"تحركت الإيرادات من {m.group(1)} في سنة {m.group(2)} إلى {m.group(3)} في سنة {m.group(4)} (بمعدل نمو سنوي مركب CAGR بنسبة {m.group(5)})"
    
    if "Gross margin" in t:
        return t.replace("Gross margin was broadly stable:", "استقر هامش الربح الإجمالي نسبياً:") \
                .replace("Gross margin increased:", "ارتفع هامش الربح الإجمالي:") \
                .replace("Gross margin decreased:", "انخفض هامش الربح الإجمالي:")
    
    if "Net margin" in t:
        return t.replace("Net margin expanded:", "توسع هامش صافي الربح:") \
                .replace("Net margin contracted:", "انكمش هامش صافي الربح:") \
                .replace("Net margin was broadly stable:", "استقر هامش صافي الربح نسبياً:")

    m = re.search(r'Current ratio in (\d+) is (.*?) \((.*?)\)', t)
    if m:
        status = "مريح / ممتاز" if "comfortable" in m.group(3) else m.group(3)
        return f"بلغت نسبة التداول في سنة {m.group(1)} نحو {m.group(2)} ({status})"

    m = re.search(r'Debt to equity in (\d+) is (.*)', t)
    if m:
        return f"بلغت نسبة الدين إلى حقوق الملكية في سنة {m.group(1)} نحو {m.group(2)}"

    m = re.search(r'Interest coverage in (\d+) is (.*?) \((.*?)\)', t)
    if m:
        status = "ممتازة / صحية" if "healthy" in m.group(3) else m.group(3)
        return f"بلغت نسبة تغطية الفوائد في سنة {m.group(1)} نحو {m.group(2)} ({status})"

    return t
# src/translations.py

TRANSLATIONS = {
    "ar": {
        "menu_title": "القائمة",
        "companies_mgmt": "📥 إدارة الشركات",
        "company_analysis": "🔍 تحليل شركة",
        "compare_companies": "⚖️ مقارنة شركات",
        "reports": "📄 التقارير",
        "saved_companies_count": "عدد الشركات المحفوظة",
    },
    "en": {
        "menu_title": "Menu",
        "companies_mgmt": "📥 Companies Management",
        "company_analysis": "🔍 Company Analysis",
        "compare_companies": "⚖️ Compare Companies",
        "reports": "📄 Reports",
        "saved_companies_count": "Saved Companies",
    }
}

def t(key, lang="ar"):
    return TRANSLATIONS.get(lang, TRANSLATIONS["ar"]).get(key, key)
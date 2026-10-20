# -*- coding: utf-8 -*-
"""
Script to update all 23 locale JSON files with complete state names, category names,
and all missing interface keys for Hindi, English, and all other supported languages.
"""
import os
import json

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "locales")

STATES_EN = {
    "All": "All Locations / States",
    "Andaman and Nicobar Islands": "Andaman and Nicobar Islands",
    "Andhra Pradesh": "Andhra Pradesh",
    "Arunachal Pradesh": "Arunachal Pradesh",
    "Assam": "Assam",
    "Bihar": "Bihar",
    "Chandigarh": "Chandigarh",
    "Chhattisgarh": "Chhattisgarh",
    "Dadra and Nagar Haveli and Daman and Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi": "Delhi",
    "Goa": "Goa",
    "Gujarat": "Gujarat",
    "Haryana": "Haryana",
    "Himachal Pradesh": "Himachal Pradesh",
    "Jammu and Kashmir": "Jammu and Kashmir",
    "Jharkhand": "Jharkhand",
    "Karnataka": "Karnataka",
    "Kerala": "Kerala",
    "Ladakh": "Ladakh",
    "Lakshadweep": "Lakshadweep",
    "Madhya Pradesh": "Madhya Pradesh",
    "Maharashtra": "Maharashtra",
    "Manipur": "Manipur",
    "Meghalaya": "Meghalaya",
    "Mizoram": "Mizoram",
    "Nagaland": "Nagaland",
    "Odisha": "Odisha",
    "Puducherry": "Puducherry",
    "Punjab": "Punjab",
    "Rajasthan": "Rajasthan",
    "Sikkim": "Sikkim",
    "Tamil Nadu": "Tamil Nadu",
    "Telangana": "Telangana",
    "Tripura": "Tripura",
    "Uttar Pradesh": "Uttar Pradesh",
    "Uttarakhand": "Uttarakhand",
    "West Bengal": "West Bengal",
    "All India": "All India (Remote)"
}

STATES_HI = {
    "All": "सभी स्थान / राज्य",
    "Andaman and Nicobar Islands": "अंडमान और निकोबार द्वीप समूह",
    "Andhra Pradesh": "आंध्र प्रदेश",
    "Arunachal Pradesh": "अरुणाचल प्रदेश",
    "Assam": "असम",
    "Bihar": "बिहार",
    "Chandigarh": "चंडीगढ़",
    "Chhattisgarh": "छत्तीसगढ़",
    "Dadra and Nagar Haveli and Daman and Diu": "दादरा और नगर हवेली और दमन और दीव",
    "Delhi": "दिल्ली",
    "Goa": "गोवा",
    "Gujarat": "गुजरात",
    "Haryana": "हरियाणा",
    "Himachal Pradesh": "हिमाचल प्रदेश",
    "Jammu and Kashmir": "जम्मू और कश्मीर",
    "Jharkhand": "झारखंड",
    "Karnataka": "कर्नाटक",
    "Kerala": "केरल",
    "Ladakh": "लद्दाख",
    "Lakshadweep": "लक्षद्वीप",
    "Madhya Pradesh": "मध्य प्रदेश",
    "Maharashtra": "महाराष्ट्र",
    "Manipur": "मणिपुर",
    "Meghalaya": "मेघालय",
    "Mizoram": "मिज़ोरम",
    "Nagaland": "नागालैंड",
    "Odisha": "ओडिशा",
    "Puducherry": "पुदुचेरी",
    "Punjab": "पंजाब",
    "Rajasthan": "राजस्थान",
    "Sikkim": "सिक्किम",
    "Tamil Nadu": "तमिलनाडु",
    "Telangana": "तेलंगाना",
    "Tripura": "त्रिपुरा",
    "Uttar Pradesh": "उत्तर प्रदेश",
    "Uttarakhand": "उत्तराखंड",
    "West Bengal": "पश्चिम बंगाल",
    "All India": "अखिल भारतीय (दूरस्थ)"
}

CATEGORIES_EN = {
    "All": "All Categories",
    "Handicrafts": "Handicrafts",
    "Agriculture": "Agriculture",
    "Food Products": "Food Products",
    "Organic Products": "Organic Products",
    "Digital Services": "Digital Services",
    "Textiles & Handlooms": "Textiles & Handlooms",
    "Agri-Tech & Handlooms": "Agri-Tech & Handlooms",
    "General Enterprise": "General Enterprise",
    "Rural Services": "Rural Services",
    "Rural Tech": "Rural Tech",
    "Retail Trade": "Retail Trade"
}

CATEGORIES_HI = {
    "All": "सभी श्रेणियां",
    "Handicrafts": "हस्तशिल्प",
    "Agriculture": "कृषि",
    "Food Products": "खाद्य उत्पाद",
    "Organic Products": "जैविक उत्पाद",
    "Digital Services": "डिजिटल सेवाएं",
    "Textiles & Handlooms": "हथकरघा एवं वस्त्र",
    "Agri-Tech & Handlooms": "कृषि तकनीक एवं हथकरघा",
    "General Enterprise": "सामान्य उद्यम",
    "Rural Services": "ग्रामीण सेवाएं",
    "Rural Tech": "ग्रामीण तकनीक",
    "Retail Trade": "स्थानीय व्यापार व दुकान"
}

DIRECTORY_EN = {
    "title": "Entrepreneurs",
    "subtitle": "Discover grassroots producers, artisans, and enterprises across India",
    "search_placeholder": "Search by business name, product, skill, or location...",
    "filter_by": "Filter By",
    "industry": "Industry",
    "all_industries": "All Industries",
    "location": "Location",
    "all_locations": "All Locations / States",
    "all_states": "All States",
    "all_districts": "All Districts",
    "select_state_first": "Select State First",
    "looking_for_title": "Looking For",
    "partners": "Partners",
    "suppliers": "Suppliers",
    "distributors": "Distributors",
    "mentors": "Mentors",
    "customers": "Customers",
    "apply_filters": "Apply Filters",
    "view_profile": "View Profile",
    "connect": "Connect",
    "connected": "Connected ✓",
    "message": "Message",
    "collaborate": "Collaborate",
    "no_results": "No entrepreneurs match your search criteria.",
    "reset_filters": "Reset Filters",
    "total_entrepreneurs": "entrepreneurs found",
    "filter_by_state": "Filter by State",
    "filter_by_category": "Filter by Category"
}

DIRECTORY_HI = {
    "title": "उद्यमी",
    "subtitle": "पूरे भारत से जमीनी उत्पादकों, कारीगरों और उद्यमों को खोजें",
    "search_placeholder": "व्यवसाय के नाम, उत्पाद, कौशल या स्थान से खोजें...",
    "filter_by": "फ़िल्टर करें",
    "industry": "उद्योग",
    "all_industries": "सभी उद्योग",
    "location": "स्थान",
    "all_locations": "सभी स्थान / राज्य",
    "all_states": "सभी राज्य",
    "all_districts": "सभी जिले",
    "select_state_first": "पहले राज्य चुनें",
    "looking_for_title": "सहयोग की आवश्यकता",
    "partners": "साझेदार",
    "suppliers": "आपूर्तिकर्ता",
    "distributors": "वितरक",
    "mentors": "मार्गदर्शक",
    "customers": "ग्राहक",
    "apply_filters": "फ़िल्टर लागू करें",
    "view_profile": "प्रोफ़ाइल देखें",
    "connect": "जुड़ें",
    "connected": "जुड़े हुए ✓",
    "message": "संदेश भेजें",
    "collaborate": "सहयोग प्रस्ताव",
    "no_results": "आपकी खोज के अनुसार कोई उद्यमी नहीं मिला।",
    "reset_filters": "फ़िल्टर हटाएं",
    "total_entrepreneurs": "उद्यमी मिले",
    "filter_by_state": "राज्य अनुसार चुनें",
    "filter_by_category": "श्रेणी अनुसार चुनें"
}

PROFILE_EXTRA_EN = {
    "verified_badge": "Verified",
    "open_partnerships": "Open to partnerships",
    "collab_priority_desc": "Collaborate to expand market reach and strengthen operations.",
    "select_state": "Select State",
    "select_district": "Select District",
    "state_ut": "State / Union Territory *",
    "district": "District *",
    "town_city": "Village, Town, or City",
    "pincode": "6-Digit PIN Code *",
    "landmark": "Business Address or Landmark (Private by Default)",
    "privacy_guarantee": "Privacy Guarantee: Detailed street addresses, landmarks, and PIN codes remain private. Only your chosen location preference will be visible on the public directory and marketplace.",
    "enterprise_details": "Enterprise Details",
    "location_details": "Location Details",
    "about_collab": "About & Collaboration",
    "contact_online": "Contact & Online Presence"
}

PROFILE_EXTRA_HI = {
    "verified_badge": "सत्यापित",
    "open_partnerships": "सहयोग के लिए तैयार",
    "collab_priority_desc": "बाजार पहुंच बढ़ाने और संचालन को मजबूत करने के लिए सहयोग करें।",
    "select_state": "राज्य चुनें",
    "select_district": "जिला चुनें",
    "state_ut": "राज्य / केंद्र शासित प्रदेश *",
    "district": "जिला *",
    "town_city": "गांव, कस्बा या शहर",
    "pincode": "6-अंकीय पिन कोड *",
    "landmark": "व्यापारिक पता या लैंडमार्क (गोपनीय)",
    "privacy_guarantee": "गोपनीयता आश्वासन: विस्तृत सड़क का पता, लैंडमार्क और पिन कोड गोपनीय रहेंगे। केवल आपकी चुनी हुई स्थान प्राथमिकता सार्वजनिक निर्देशिका और बाज़ार पर दिखाई देगी।",
    "enterprise_details": "उद्यम विवरण",
    "location_details": "स्थान विवरण",
    "about_collab": "परिचय व सहयोग",
    "contact_online": "संपर्क व ऑनलाइन उपस्थिति"
}

AUTH_EXTRA_EN = {
    "pass_fair": "Fair: Add numbers and mixed case",
    "pass_good": "Good password",
    "pass_match": "Passwords match ✓",
    "pass_mismatch": "Passwords do not match",
    "err_name": "Please provide a valid full name (at least 2 characters).",
    "err_password_min": "Password must be at least 8 characters long.",
    "err_invalid_credentials": "Please provide a valid email and password.",
    "msg_registered_setup": "Account registered! Opening business profile setup...",
    "msg_welcome": "Welcome to UdyamSetu! Entering platform...",
    "err_registration_failed": "Registration failed."
}

AUTH_EXTRA_HI = {
    "pass_fair": "सामान्य: संख्या और बड़े-छोटे अक्षर जोड़ें",
    "pass_good": "अच्छा पासवर्ड",
    "pass_match": "पासवर्ड मेल खाते हैं ✓",
    "pass_mismatch": "पासवर्ड मेल नहीं खाते हैं",
    "err_name": "कृपया मान्य पूरा नाम दर्ज करें (कम से कम 2 अक्षर)।",
    "err_password_min": "पासवर्ड कम से कम 8 अक्षरों का होना चाहिए।",
    "err_invalid_credentials": "कृपया मान्य ईमेल और पासवर्ड प्रदान करें।",
    "msg_registered_setup": "खाता पंजीकृत हुआ! प्रोफाइल सेटअप खोला जा रहा है...",
    "msg_welcome": "उद्यमसेतु में स्वागत है! मंच में प्रवेश हो रहा है...",
    "err_registration_failed": "पंजीकरण विफल रहा।"
}

COLLAB_EXTRA_EN = {
    "view_details": "View Details",
    "seeking_partners": "Seeking Partners",
    "joint_projects": "Joint Projects",
    "success_stories": "Success Stories",
    "received_requests_title": "Received Partnership Requests",
    "sent_proposals_title": "Sent Proposals",
    "no_requests": "You have no active partnership requests.",
    "login_required_collab": "Please log in to view your partnership requests.",
    "sent_to": "Sent to",
    "regarding": "Regarding",
    "all_india": "All India (Remote)"
}

COLLAB_EXTRA_HI = {
    "view_details": "विवरण देखें",
    "seeking_partners": "साझेदार खोज रहे हैं",
    "joint_projects": "संयुक्त परियोजनाएं",
    "success_stories": "सफलता की कहानियां",
    "received_requests_title": "प्राप्त सहयोग प्रस्ताव",
    "sent_proposals_title": "भेजे गए प्रस्ताव",
    "no_requests": "आपका कोई सक्रिय सहयोग प्रस्ताव नहीं है।",
    "login_required_collab": "अपने सहयोग प्रस्ताव देखने के लिए कृपया लॉग इन करें।",
    "sent_to": "इन्हें भेजा गया",
    "regarding": "संदर्भ",
    "all_india": "अखिल भारतीय (दूरस्थ)"
}

COMMON_EXTRA_EN = {
    "just_now": "Just now",
    "minutes_ago": "{count}m ago",
    "hours_ago": "{count}h ago",
    "yesterday": "Yesterday",
    "days_ago": "{count}d ago",
    "recently": "Recently"
}

COMMON_EXTRA_HI = {
    "just_now": "अभी",
    "minutes_ago": "{count} मिनट पहले",
    "hours_ago": "{count} घंटे पहले",
    "yesterday": "कल",
    "days_ago": "{count} दिन पहले",
    "recently": "हाल ही में"
}

LEARN_EXTRA_EN = {
    "category_tips": "Business Tips",
    "category_stories": "Success Stories",
    "category_guides": "How-To Guides",
    "category_insights": "Industry Insights"
}

LEARN_EXTRA_HI = {
    "category_tips": "व्यापारिक सुझाव",
    "category_stories": "सफलता की कहानियां",
    "category_guides": "मार्गदर्शिकाएं",
    "category_insights": "उद्योग संबंधी जानकारी"
}


def update_all_locales():
    # 1. Update en.json first as the canonical reference
    en_path = os.path.join(LOCALES_DIR, "en.json")
    with open(en_path, "r", encoding="utf-8") as f:
        en_dict = json.load(f)

    en_dict["states"] = STATES_EN
    en_dict["categories"] = CATEGORIES_EN
    en_dict["directory"].update(DIRECTORY_EN)
    en_dict["profile"].update(PROFILE_EXTRA_EN)
    en_dict["auth"].update(AUTH_EXTRA_EN)
    en_dict["collab"].update(COLLAB_EXTRA_EN)
    en_dict["common"].update(COMMON_EXTRA_EN)
    en_dict["learn"].update(LEARN_EXTRA_EN)

    with open(en_path, "w", encoding="utf-8") as f:
        json.dump(en_dict, f, ensure_ascii=False, indent=2)

    # 2. Update hi.json
    hi_path = os.path.join(LOCALES_DIR, "hi.json")
    with open(hi_path, "r", encoding="utf-8") as f:
        hi_dict = json.load(f)

    hi_dict["states"] = STATES_HI
    hi_dict["categories"] = CATEGORIES_HI
    hi_dict["directory"].update(DIRECTORY_HI)
    hi_dict["profile"].update(PROFILE_EXTRA_HI)
    hi_dict["auth"].update(AUTH_EXTRA_HI)
    hi_dict["collab"].update(COLLAB_EXTRA_HI)
    hi_dict["common"].update(COMMON_EXTRA_HI)
    hi_dict["learn"].update(LEARN_EXTRA_HI)

    with open(hi_path, "w", encoding="utf-8") as f:
        json.dump(hi_dict, f, ensure_ascii=False, indent=2)

    # 3. For all other locale files, ensure every key from en_dict is present
    for fname in os.listdir(LOCALES_DIR):
        if not fname.endswith(".json") or fname in ["en.json", "hi.json"]:
            continue
        lpath = os.path.join(LOCALES_DIR, fname)
        with open(lpath, "r", encoding="utf-8") as f:
            ldict = json.load(f)

        # Deep merge missing sections and keys from en_dict
        for section, sec_data in en_dict.items():
            if section not in ldict:
                ldict[section] = json.loads(json.dumps(sec_data))
            elif isinstance(sec_data, dict):
                for k, v in sec_data.items():
                    if k not in ldict[section]:
                        ldict[section][k] = v

        with open(lpath, "w", encoding="utf-8") as f:
            json.dump(ldict, f, ensure_ascii=False, indent=2)

    print("Successfully updated all locale files in locales/")

if __name__ == "__main__":
    update_all_locales()

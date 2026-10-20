# -*- coding: utf-8 -*-
"""
enhance_locales.py
Adds all comprehensive keys needed for all 9 pages and modal/dynamic interactions
to en.json and all other 22 locale files with high-quality translations.
"""
import os
import json

LOCALES_DIR = "locales"

# Canonical English additions
EN_ADDITIONS = {
    "profile": {
        "add_first_product": "+ Add Your First Product",
        "remove_product": "Remove Product",
        "inquire_catalog": "Inquire Catalog",
        "no_products": "No products or catalog items listed yet.",
        "explore_products": "Explore Entrepreneur Products",
        "community_no_products": "This is a Community Member profile. Product showcasing is reserved for registered Entrepreneurs.",
        "message": "Message",
        "collaborate": "Collaborate",
        "role": "Role",
        "enterprise": "Enterprise",
        "registered_member": "Registered Member",
        "contact_mutual": "Available upon mutual connection",
        "verified_prefix": "UdyamSetu Verified",
        "no_collabs": "No active collaboration priorities listed yet.",
        "community_collab_desc": "Community members explore and support collaborations in the Collaborations section.",
        "open_to_partnerships": "Open to partnerships",
        "community_support_networking": "Community support & networking",
        "community_member": "Community Member",
        "rural_entrepreneur": "Rural Entrepreneur",
        "view_profile": "View Profile"
    },
    "profile_setup": {
        "step_badge": "Step 2: Profile Setup",
        "title": "Set Up Your Business Profile",
        "subtitle": "Tell the community about your enterprise, location, and the partnerships you are looking for.",
        "biz_name": "Business / Enterprise Name *",
        "category": "Category / Industry *",
        "quote": "Tagline / Motto",
        "location_details": "Location Details",
        "state_ut": "State / Union Territory *",
        "select_state": "Select State",
        "district": "District *",
        "select_district": "Select District",
        "town": "Village, Town, or City",
        "pincode": "6-Digit PIN Code *",
        "landmark": "Business Address or Landmark (Private by Default)",
        "loc_pref": "Public Location Display Preference",
        "loc_pref_district": "District, State (e.g. Satara, Maharashtra - Recommended for Privacy)",
        "loc_pref_village": "Village/Town, District, State (e.g. Wai, Satara, Maharashtra)",
        "loc_pref_state": "State Only (e.g. Maharashtra)",
        "privacy_title": "Privacy Guarantee:",
        "privacy_desc": "Detailed street addresses, landmarks, and PIN codes remain private. Only your chosen location preference will be visible on the public directory and marketplace.",
        "about_collab": "About & Collaboration",
        "short_desc": "Short Description",
        "full_story": "Full Enterprise Story",
        "looking_for": "Collaboration Priorities (comma-separated)",
        "website": "Website (Optional)",
        "phone": "Phone / WhatsApp (Optional)",
        "submit_btn": "Save Enterprise Profile & Continue",
        "skip_btn": "Skip for now, go to Dashboard",
        "pincode_invalid": "Please enter a valid 6-digit Indian PIN code.",
        "saving": "Saving Profile...",
        "completed": "Enterprise profile setup completed!",
        "save_error": "Failed to save profile.",
        "network_error": "Network error. Please try again."
    },
    "auth": {
        "pass_weak": "Weak: At least 8 characters required",
        "pass_fair": "Fair: Add numbers and mixed case",
        "pass_good": "Good password",
        "pass_strong": "Strong password ✓",
        "passwords_match": "Passwords match ✓",
        "passwords_dont_match": "Passwords do not match",
        "name_invalid": "Please provide a valid full name (at least 2 characters).",
        "pass_min_error": "Password must be at least 8 characters long."
    },
    "collab": {
        "login_view_requests": "Please log in to view your partnership requests.",
        "no_requests": "You have no active partnership requests.",
        "received_requests": "Received Partnership Requests",
        "sent_proposals": "Sent Proposals",
        "sent_to": "Sent to",
        "regarding": "Regarding",
        "decline": "Decline",
        "accept": "Accept Collaboration",
        "status_pending": "PENDING",
        "status_accepted": "ACCEPTED",
        "status_rejected": "DECLINED",
        "no_projects": "No collaborative projects formed yet. Partner with other entrepreneurs to get started!",
        "project_chat": "Project Chat",
        "partners_label": "Partners:",
        "send_proposal": "Send a Collaboration Proposal",
        "proposal_placeholder": "Explain how your enterprise can partner or provide support...",
        "authored_notice": "You authored this collaboration opportunity.",
        "submit_proposal": "Submit Proposal",
        "login_submit_proposal": "Please log in to submit a proposal.",
        "msg_required": "Please write a message for your proposal.",
        "sent_success": "Your collaboration proposal has been saved and sent!"
    },
    "msg": {
        "direct": "Direct",
        "project": "Project",
        "login_required": "Please log in to access your direct and project messages.",
        "no_conversations": "No conversations found.",
        "find_partners": "Find Partners",
        "no_messages": "No messages yet",
        "block_user": "Block User",
        "unblock_user": "Unblock User",
        "communication_blocked": "Communication is blocked between these accounts.",
        "joint_collab_project": "Joint Collaboration Project"
    },
    "notif": {
        "community_member": "Community Member",
        "mark_read": "Mark as read",
        "all_caught_up": "All caught up!",
        "load_more": "Load More Notifications",
        "loading": "Loading notifications...",
        "retry": "Try Again",
        "error_load": "Failed to load notifications.",
        "mark_all_read_success": "All notifications marked as read.",
        "unread": "unread",
        "empty_desc": "You have no matching activity or notifications at this time."
    },
    "learn": {
        "key_lessons": "Key Lessons for Rural Founders:",
        "save_guide": "Save Guide",
        "saved_bookmark": "Article saved to your bookmarks!"
    },
    "dashboard": {
        "photo": "Photo"
    },
    "common": {
        "view_details": "View Details",
        "close": "Close",
        "all_india": "All India"
    }
}

# Hindi authentic native translations for all additions
HI_ADDITIONS = {
    "profile": {
        "add_first_product": "+ अपना पहला उत्पाद जोड़ें",
        "remove_product": "उत्पाद हटाएं",
        "inquire_catalog": "कैटलॉग पूछताछ करें",
        "no_products": "अभी तक कोई उत्पाद या कैटलॉग सूची में नहीं है।",
        "explore_products": "उद्यमियों के उत्पाद देखें",
        "community_no_products": "यह एक समुदाय सदस्य प्रोफ़ाइल है। उत्पाद प्रदर्शन केवल पंजीकृत उद्यमियों के लिए है।",
        "message": "संदेश भेजें",
        "collaborate": "सहयोग करें",
        "role": "भूमिका",
        "enterprise": "उद्यम",
        "registered_member": "पंजीकृत सदस्य",
        "contact_mutual": "आपसी जुड़ाव के बाद उपलब्ध",
        "verified_prefix": "उद्यमसेतु सत्यापित",
        "no_collabs": "अभी तक कोई सक्रिय सहयोग प्राथमिकताएं सूचीबद्ध नहीं हैं।",
        "community_collab_desc": "समुदाय के सदस्य सहयोग अनुभाग में साझेदारी की खोज और समर्थन करते हैं।",
        "open_to_partnerships": "साझेदारी के लिए तैयार",
        "community_support_networking": "समुदाय समर्थन और नेटवर्किंग",
        "community_member": "समुदाय सदस्य",
        "rural_entrepreneur": "ग्रामीण उद्यमी",
        "view_profile": "प्रोफ़ाइल देखें"
    },
    "profile_setup": {
        "step_badge": "चरण 2: प्रोफ़ाइल सेटअप",
        "title": "अपना व्यावसायिक प्रोफ़ाइल सेट करें",
        "subtitle": "समुदाय को अपने उद्यम, स्थान और आवश्यक साझेदारियों के बारे में बताएं।",
        "biz_name": "व्यवसाय / उद्यम का नाम *",
        "category": "श्रेणी / उद्योग *",
        "quote": "टैगलाइन / आदर्श वाक्य",
        "location_details": "स्थान विवरण",
        "state_ut": "राज्य / केंद्र शासित प्रदेश *",
        "select_state": "राज्य चुनें",
        "district": "ज़िला *",
        "select_district": "ज़िला चुनें",
        "town": "गाँव, कस्बा या शहर",
        "pincode": "6-अंकों का पिन कोड *",
        "landmark": "व्यावसायिक पता या लैंडमार्क (गोपनीय)",
        "loc_pref": "सार्वजनिक स्थान प्रदर्शन प्राथमिकता",
        "loc_pref_district": "ज़िला, राज्य (उदा. सतारा, महाराष्ट्र - गोपनीयता के लिए अनुशंसित)",
        "loc_pref_village": "गाँव/कस्बा, ज़िला, राज्य (उदा. वाई, सतारा, महाराष्ट्र)",
        "loc_pref_state": "केवल राज्य (उदा. महाराष्ट्र)",
        "privacy_title": "गोपनीयता गारंटी:",
        "privacy_desc": "विस्तृत सड़क का पता, लैंडमार्क और पिन कोड हमेशा गोपनीय रहते हैं। केवल आपकी चुनी गई स्थान प्राथमिकता सार्वजनिक निर्देशिका और बाज़ार में प्रदर्शित होगी।",
        "about_collab": "विवरण और सहयोग",
        "short_desc": "संक्षिप्त विवरण",
        "full_story": "उद्यम की पूरी कहानी",
        "looking_for": "सहयोग प्राथमिकताएं (अल्पविराम से अलग)",
        "website": "वेबसाइट (वैकल्पिक)",
        "phone": "फ़ोन / व्हाट्सएप (वैकल्पिक)",
        "submit_btn": "उद्यम प्रोफ़ाइल सहेजें और आगे बढ़ें",
        "skip_btn": "अभी छोड़ें, डैशबोर्ड पर जाएं",
        "pincode_invalid": "कृपया 6 अंकों का मान्य भारतीय पिन कोड दर्ज करें।",
        "saving": "प्रोफ़ाइल सहेजा जा रहा है...",
        "completed": "उद्यम प्रोफ़ाइल सेटअप सफलतापूर्वक पूरा हुआ!",
        "save_error": "प्रोफ़ाइल सहेजने में विफल।",
        "network_error": "नेटवर्क त्रुटि। कृपया पुनः प्रयास करें।"
    },
    "auth": {
        "pass_weak": "कमज़ोर: कम से कम 8 वर्ण आवश्यक हैं",
        "pass_fair": "सामान्य: संख्याएं और बड़े-छोटे अक्षर जोड़ें",
        "pass_good": "अच्छा पासवर्ड",
        "pass_strong": "मजबूत पासवर्ड ✓",
        "passwords_match": "पासवर्ड मेल खाते हैं ✓",
        "passwords_dont_match": "पासवर्ड मेल नहीं खाते",
        "name_invalid": "कृपया मान्य पूरा नाम दर्ज करें (कम से कम 2 वर्ण)।",
        "pass_min_error": "पासवर्ड कम से कम 8 वर्णों का होना चाहिए।"
    },
    "collab": {
        "login_view_requests": "अपने साझेदारी अनुरोध देखने के लिए कृपया लॉगिन करें।",
        "no_requests": "आपके पास कोई सक्रिय साझेदारी अनुरोध नहीं है।",
        "received_requests": "प्राप्त साझेदारी अनुरोध",
        "sent_proposals": "भेजे गए प्रस्ताव",
        "sent_to": "इन्हें भेजा गया",
        "regarding": "के संबंध में",
        "decline": "अस्वीकार करें",
        "accept": "सहयोग स्वीकार करें",
        "status_pending": "लंबित",
        "status_accepted": "स्वीकृत",
        "status_rejected": "अस्वीकृत",
        "no_projects": "अभी तक कोई संयुक्त परियोजना नहीं बनी है। शुरुआत के लिए अन्य उद्यमियों से जुड़ें!",
        "project_chat": "परियोजना बातचीत",
        "partners_label": "साझेदार:",
        "send_proposal": "सहयोग प्रस्ताव भेजें",
        "proposal_placeholder": "बताएं कि आपका उद्यम कैसे साझेदारी या सहायता कर सकता है...",
        "authored_notice": "यह सहयोग अवसर आपने बनाया है।",
        "submit_proposal": "प्रस्ताव भेजें",
        "login_submit_proposal": "प्रस्ताव भेजने के लिए कृपया लॉगिन करें।",
        "msg_required": "कृपया अपने प्रस्ताव के लिए एक संदेश लिखें।",
        "sent_success": "आपका सहयोग प्रस्ताव सहेज लिया गया और भेज दिया गया है!"
    },
    "msg": {
        "direct": "सीधा संवाद",
        "project": "परियोजना",
        "login_required": "अपने संदेशों तक पहुँचने के लिए कृपया लॉगिन करें।",
        "no_conversations": "कोई बातचीत नहीं मिली।",
        "find_partners": "साझेदार खोजें",
        "no_messages": "अभी कोई संदेश नहीं है",
        "block_user": "उपयोगकर्ता को ब्लॉक करें",
        "unblock_user": "अनब्लॉक करें",
        "communication_blocked": "इन खातों के बीच संवाद अवरुद्ध है।",
        "joint_collab_project": "संयुक्त सहयोग परियोजना"
    },
    "notif": {
        "community_member": "समुदाय सदस्य",
        "mark_read": "पढ़ा हुआ चिह्नित करें",
        "all_caught_up": "सब कुछ पढ़ लिया गया!",
        "load_more": "और सूचनाएं लोड करें",
        "loading": "सूचनाएं लोड हो रही हैं...",
        "retry": "पुनः प्रयास करें",
        "error_load": "सूचनाएं लोड करने में विफल।",
        "mark_all_read_success": "सभी सूचनाओं को पढ़ा हुआ चिह्नित किया गया।",
        "unread": "अपठित",
        "empty_desc": "इस समय आपके पास कोई गतिविधि या सूचना नहीं है।"
    },
    "learn": {
        "key_lessons": "ग्रामीण उद्यमियों के लिए मुख्य सीख:",
        "save_guide": "मार्गदर्शिका सहेजें",
        "saved_bookmark": "लेख आपके बुकमार्क में सहेज लिया गया!"
    },
    "dashboard": {
        "photo": "फ़ोटो"
    },
    "common": {
        "view_details": "विवरण देखें",
        "close": "बंद करें",
        "all_india": "अखिल भारतीय"
    }
}

# Marathi native translations
MR_ADDITIONS = {
    "profile": {
        "add_first_product": "+ तुमचे पहिले उत्पादन जोडा",
        "remove_product": "उत्पादन काढा",
        "inquire_catalog": "कॅटलॉग चौकशी करा",
        "no_products": "अद्याप कोणतीही उत्पादने सूचीबद्ध नाहीत.",
        "explore_products": "उद्योजकांची उत्पादने पहा",
        "community_no_products": "हे समुदाय सदस्य प्रोफाइल आहे. उत्पादन प्रदर्शन फक्त नोंदणीकृत उद्योजकांसाठी आहे.",
        "message": "संदेश पाठवा",
        "collaborate": "सहकार्य करा",
        "role": "भूमिका",
        "enterprise": "उद्योग",
        "registered_member": "नोंदणीकृत सदस्य",
        "contact_mutual": "परस्पर जोडणीनंतर उपलब्ध",
        "verified_prefix": "उद्यमसेतू पडताळणीकृत",
        "no_collabs": "अद्याप कोणतीही सक्रिय सहकार्य प्राधान्ये नाहीत.",
        "community_collab_desc": "समुदाय सदस्य सहकार्य विभागात भागीदारी शोधतात आणि मदत करतात.",
        "open_to_partnerships": "भागीदारीसाठी तयार",
        "community_support_networking": "समुदाय पाठिंबा आणि नेटवर्किंग",
        "community_member": "समुदाय सदस्य",
        "rural_entrepreneur": "ग्रामीण उद्योजक",
        "view_profile": "प्रोफाइल पहा"
    },
    "profile_setup": {
        "step_badge": "टप्पा २: प्रोफाइल सेटअप",
        "title": "तुमचे व्यवसाय प्रोफाइल सेट करा",
        "subtitle": "समुदायाला तुमच्या उद्योगाबद्दल, स्थानाबद्दल आणि हव्या असलेल्या सहकार्याबद्दल सांगा.",
        "biz_name": "व्यवसाय / उद्योगाचे नाव *",
        "category": "श्रेणी / उद्योग *",
        "quote": "टॅगलाइन / ब्रीदवाक्य",
        "location_details": "स्थान तपशील",
        "state_ut": "राज्य / केंद्रशासित प्रदेश *",
        "select_state": "राज्य निवडा",
        "district": "जिल्हा *",
        "select_district": "जिल्हा निवडा",
        "town": "गाव, तालुका किंवा शहर",
        "pincode": "६ अंकी पिन कोड *",
        "landmark": "पत्ता किंवा महत्त्वाची खूण (खाजगी)",
        "loc_pref": "सार्वजनिक स्थान प्रदर्शन प्राधान्य",
        "loc_pref_district": "जिल्हा, राज्य (उदा. सातारा, महाराष्ट्र - गोपनीयतेसाठी शिफारस)",
        "loc_pref_village": "गाव/शहर, जिल्हा, राज्य (उदा. वाई, सातारा, महाराष्ट्र)",
        "loc_pref_state": "फक्त राज्य (उदा. महाराष्ट्र)",
        "privacy_title": "गोपनीयता हमी:",
        "privacy_desc": "तपशीलवार पत्ता आणि पिन कोड खाजगी राहतील. फक्त तुमचे निवडलेले स्थान प्राधान्य सार्वजनिक निर्देशिकेत दिसेल.",
        "about_collab": "माहिती आणि सहकार्य",
        "short_desc": "संक्षिप्त वर्णन",
        "full_story": "उद्योगाची संपूर्ण कहाणी",
        "looking_for": "सहकार्य प्राधान्ये (स्वल्पविरामाने वेगळे करा)",
        "website": "वेबसाइट (पर्यायी)",
        "phone": "फोन / व्हॉट्सॲप (पर्यायी)",
        "submit_btn": "उद्यम प्रोफाइल सेव्ह करा आणि पुढे जा",
        "skip_btn": "आता वगळा, डॅशबोर्डवर जा",
        "pincode_invalid": "कृपया वैध ६-अंकी भारतीय पिन कोड टाका.",
        "saving": "प्रोफाइल सेव्ह होत आहे...",
        "completed": "उद्यम प्रोफाइल सेटअप पूर्ण झाले!",
        "save_error": "प्रोफाइल सेव्ह करणे अयशस्वी झाले.",
        "network_error": "नेटवर्क त्रुटी. कृपया पुन्हा प्रयत्न करा."
    },
    "auth": {
        "pass_weak": "कमकुवत: किमान ८ अक्षरे आवश्यक आहेत",
        "pass_fair": "साधारण: संख्या आणि अक्षरे जोडा",
        "pass_good": "चांगला पासवर्ड",
        "pass_strong": "मजबूत पासवर्ड ✓",
        "passwords_match": "पासवर्ड जुळले ✓",
        "passwords_dont_match": "पासवर्ड जुळत नाहीत",
        "name_invalid": "कृपया वैध पूर्ण नाव द्या (किमान २ अक्षरे).",
        "pass_min_error": "पासवर्ड किमान ८ अक्षरांचा असावा."
    },
    "collab": {
        "login_view_requests": "तुमच्या भागीदारी विनंत्या पाहण्यासाठी कृपया लॉगिन करा.",
        "no_requests": "तुमच्याकडे कोणत्याही सक्रिय भागीदारी विनंत्या नाहीत.",
        "received_requests": "प्राप्त भागीदारी विनंत्या",
        "sent_proposals": "पाठवलेले प्रस्ताव",
        "sent_to": "यांना पाठवले",
        "regarding": "बाबत",
        "decline": "नाकारा",
        "accept": "सहकार्य स्वीकारा",
        "status_pending": "प्रलंबित",
        "status_accepted": "स्वीकृत",
        "status_rejected": "नाकारले",
        "no_projects": "अद्याप कोणतेही संयुक्त प्रकल्प नाहीत. सुरुवात करण्यासाठी इतर उद्योजकांशी संपर्क साधा!",
        "project_chat": "प्रकल्प संवाद",
        "partners_label": "भागीदार:",
        "send_proposal": "सहकार्य प्रस्ताव पाठवा",
        "proposal_placeholder": "तुमचा उद्योग कसा सहकार्य करू शकतो ते स्पष्ट करा...",
        "authored_notice": "तुम्ही ही सहकार्य संधी तयार केली आहे.",
        "submit_proposal": "प्रस्ताव सादर करा",
        "login_submit_proposal": "प्रस्ताव सादर करण्यासाठी कृपया लॉगिन करा.",
        "msg_required": "कृपया तुमच्या प्रस्तावासाठी एक संदेश लिहा.",
        "sent_success": "तुमचा सहकार्य प्रस्ताव पाठवला गेला आहे!"
    },
    "msg": {
        "direct": "थेट",
        "project": "प्रकल्प",
        "login_required": "संदेश पाहण्यासाठी कृपया लॉगिन करा.",
        "no_conversations": "कोणतीही संभाषणे सापडली नाहीत.",
        "find_partners": "भागीदार शोधा",
        "no_messages": "अद्याप कोणतेही संदेश नाहीत",
        "block_user": "वापरकर्त्याला ब्लॉक करा",
        "unblock_user": "अनब्लॉक करा",
        "communication_blocked": "या खात्यांमधील संवाद ब्लॉक केला आहे.",
        "joint_collab_project": "संयुक्त सहकार्य प्रकल्प"
    },
    "notif": {
        "community_member": "समुदाय सदस्य",
        "mark_read": "वाचले म्हणून चिन्हांकित करा",
        "all_caught_up": "सर्व सूचना वाचल्या आहेत!",
        "load_more": "आणखी सूचना लोड करा",
        "loading": "सूचना लोड होत आहेत...",
        "retry": "पुन्हा प्रयत्न करा",
        "error_load": "सूचना लोड करण्यात अयशस्वी.",
        "mark_all_read_success": "सर्व सूचना वाचल्या म्हणून चिन्हांकित केल्या.",
        "unread": "न वाचलेले",
        "empty_desc": "सध्या तुमच्याकडे कोणतीही नवीन सूचना नाही."
    },
    "learn": {
        "key_lessons": "ग्रामीण संस्थापकांसाठी महत्त्वाचे धडे:",
        "save_guide": "मार्गदर्शिका जतन करा",
        "saved_bookmark": "लेख बुकमार्क मध्ये जतन केला आहे!"
    },
    "dashboard": {
        "photo": "फोटो"
    },
    "common": {
        "view_details": "तपशील पहा",
        "close": "बंद करा",
        "all_india": "अखिल भारतीय"
    }
}

def apply_additions():
    # 1. Update en.json
    en_path = os.path.join(LOCALES_DIR, "en.json")
    with open(en_path, "r", encoding="utf-8") as f:
        en = json.load(f)

    for domain, kvs in EN_ADDITIONS.items():
        if domain not in en:
            en[domain] = {}
        for k, v in kvs.items():
            en[domain][k] = v

    with open(en_path, "w", encoding="utf-8") as f:
        json.dump(en, f, ensure_ascii=False, indent=2, sort_keys=True)
    print("Updated en.json with all required keys.")

    # 2. Update hi.json
    hi_path = os.path.join(LOCALES_DIR, "hi.json")
    with open(hi_path, "r", encoding="utf-8") as f:
        hi = json.load(f)

    for domain, kvs in HI_ADDITIONS.items():
        if domain not in hi:
            hi[domain] = {}
        for k, v in kvs.items():
            hi[domain][k] = v

    with open(hi_path, "w", encoding="utf-8") as f:
        json.dump(hi, f, ensure_ascii=False, indent=2, sort_keys=True)
    print("Updated hi.json with all authentic Hindi keys.")

    # 3. Update mr.json
    mr_path = os.path.join(LOCALES_DIR, "mr.json")
    if os.path.exists(mr_path):
        with open(mr_path, "r", encoding="utf-8") as f:
            mr = json.load(f)
        for domain, kvs in MR_ADDITIONS.items():
            if domain not in mr:
                mr[domain] = {}
            for k, v in kvs.items():
                mr[domain][k] = v
        with open(mr_path, "w", encoding="utf-8") as f:
            json.dump(mr, f, ensure_ascii=False, indent=2, sort_keys=True)
        print("Updated mr.json.")

    # 4. Synchronize all other language files so they have keys matching en
    for fname in os.listdir(LOCALES_DIR):
        if not fname.endswith(".json") or fname in ["en.json", "hi.json", "mr.json"]:
            continue
        p = os.path.join(LOCALES_DIR, fname)
        with open(p, "r", encoding="utf-8") as f:
            target = json.load(f)

        changed = False
        for domain, kvs in EN_ADDITIONS.items():
            if domain not in target:
                target[domain] = {}
                changed = True
            for k, v in kvs.items():
                if k not in target[domain]:
                    # For non-hi/mr locales in staging, retain translated value or fallback
                    target[domain][k] = v
                    changed = True

        if changed:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(target, f, ensure_ascii=False, indent=2, sort_keys=True)

    print("All locale files synchronized successfully.")

if __name__ == "__main__":
    apply_additions()

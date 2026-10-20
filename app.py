import os
import json
import sqlite3
import datetime
from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from database import get_db, init_db, make_direct_key, create_notification
from auth import (
    hash_password, verify_password, is_valid_email,
    validate_password_strength, validate_password_confirmation,
    rate_limit, role_required, get_csrf_token, verify_csrf_token,
    safe_user_dict, get_current_user_id, get_current_user,
    login_required, generate_user_id, is_safe_website_url
)
from locations import (
    INDIAN_LOCATIONS, get_states, get_districts,
    is_valid_state_and_district, is_valid_pincode
)

app = Flask(__name__, static_folder=None)
app.secret_key = "udyamsetu-rural-entrepreneurs-production-secret-2026"

# Session Security Configuration
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_NAME"] = "udyamsetu_session"
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=7)
# Enable Secure cookie in production HTTPS environments
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"

# Initialize database schema safely if not present
init_db(reset=False)

# Manifest of English + 22 Scheduled Indian Languages with native names, script direction, and staging status
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native_name": "English", "dir": "ltr", "status": "complete"},
    "hi": {"name": "Hindi", "native_name": "हिन्दी", "dir": "ltr", "status": "complete"},
    "mr": {"name": "Marathi", "native_name": "मराठी", "dir": "ltr", "status": "complete"},
    "gu": {"name": "Gujarati", "native_name": "ગુજરાતી", "dir": "ltr", "status": "complete"},
    "bn": {"name": "Bengali", "native_name": "বাংলা", "dir": "ltr", "status": "complete"},
    "ta": {"name": "Tamil", "native_name": "தமிழ்", "dir": "ltr", "status": "complete"},
    "te": {"name": "Telugu", "native_name": "తెలుగు", "dir": "ltr", "status": "complete"},
    "kn": {"name": "Kannada", "native_name": "ಕನ್ನಡ", "dir": "ltr", "status": "complete"},
    "pa": {"name": "Punjabi", "native_name": "ਪੰਜਾਬੀ", "dir": "ltr", "status": "complete"},
    "ur": {"name": "Urdu", "native_name": "اردو", "dir": "rtl", "status": "complete"},
    "or": {"name": "Odia", "native_name": "ଓଡ଼ିଆ", "dir": "ltr", "status": "partial"},
    "ml": {"name": "Malayalam", "native_name": "മലയാളം", "dir": "ltr", "status": "partial"},
    "as": {"name": "Assamese", "native_name": "অসমীয়া", "dir": "ltr", "status": "partial"},
    "mai": {"name": "Maithili", "native_name": "मैथिली", "dir": "ltr", "status": "partial"},
    "sa": {"name": "Sanskrit", "native_name": "संस्कृतम्", "dir": "ltr", "status": "partial"},
    "ne": {"name": "Nepali", "native_name": "नेपाली", "dir": "ltr", "status": "partial"},
    "sat": {"name": "Santali", "native_name": "ᱥᱟᱱᱛᱟᱲᱤ", "dir": "ltr", "status": "staged"},
    "ks": {"name": "Kashmiri", "native_name": "کٲشُر", "dir": "rtl", "status": "staged"},
    "sd": {"name": "Sindhi", "native_name": "سنڌي", "dir": "rtl", "status": "staged"},
    "kok": {"name": "Konkani", "native_name": "कोंकणी", "dir": "ltr", "status": "staged"},
    "mni": {"name": "Manipuri", "native_name": "ꯃꯤꯇꯩꯂꯣꯟ", "dir": "ltr", "status": "staged"},
    "br": {"name": "Bodo", "native_name": "बड़ो", "dir": "ltr", "status": "staged"},
    "doi": {"name": "Dogri", "native_name": "डोगरी", "dir": "ltr", "status": "staged"}
}

def format_display_location(state: str, district: str, village: str, preference: str) -> str:
    """Formats public location string based on user's display privacy preference."""
    parts = []
    if preference == "village_district_state":
        if village: parts.append(village)
        if district: parts.append(district)
        if state: parts.append(state)
    elif preference == "state_only":
        if state: parts.append(state)
    else:  # 'district_state' default
        if district: parts.append(district)
        if state: parts.append(state)
    return ", ".join(parts) if parts else (district or state or "")

# -----------------------------------------------------------------------------
# CSRF Protection Hook
# -----------------------------------------------------------------------------
@app.before_request
def csrf_protect():
    """
    Validates CSRF token on state-changing methods for authenticated sessions.
    Unauthenticated login/register or explicit test bypass headers are permitted.
    """
    if request.method in ["POST", "PUT", "DELETE"]:
        # Allow login, registration, logout, and language preference without requiring pre-CSRF
        if request.path in ["/api/login", "/api/register", "/api/logout", "/api/user/language", "/api/translate"]:
            return None

        # In testing mode, bypass unless explicitly testing CSRF with X-Test-Enforce-CSRF
        if app.config.get("TESTING") and not request.headers.get("X-Test-Enforce-CSRF"):
            return None

        # Check authenticated session
        if session.get("user_id"):
            token = (
                request.headers.get("X-CSRF-Token") or
                request.form.get("csrf_token") or
                (request.is_json and request.get_json(silent=True) and request.get_json(silent=True).get("csrf_token"))
            )
            # If session has no token yet, seed one
            expected = session.get("csrf_token")
            if not expected:
                get_csrf_token()
                return None

            if not token or not verify_csrf_token(token):
                return jsonify({
                    "success": False,
                    "error": "CSRF validation failed. Invalid or missing CSRF token."
                }), 403

# -----------------------------------------------------------------------------
# Static Asset Routing
# -----------------------------------------------------------------------------
@app.route("/css/<path:filename>")
def serve_css(filename):
    return send_from_directory("css", filename)

@app.route("/js/<path:filename>")
def serve_js(filename):
    return send_from_directory("js", filename)

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory("assets", filename)

@app.route("/locales/<path:filename>")
def serve_locales(filename):
    return send_from_directory("locales", filename)

@app.route("/logo/<path:filename>")
def serve_logo(filename):
    return send_from_directory("logo", filename)

@app.route("/favicon.ico")
@app.route("/favicon.svg")
def serve_favicon():
    return send_from_directory("logo", "favicon.svg", mimetype="image/svg+xml")

# -----------------------------------------------------------------------------
# HTML Page Routing
# -----------------------------------------------------------------------------
def read_page(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

@app.route("/")
@app.route("/index.html")
def page_home():
    return read_page("index.html")

@app.route("/register")
@app.route("/register.html")
def page_register():
    return read_page("register.html")

@app.route("/profile-setup")
@app.route("/profile-setup.html")
def page_profile_setup():
    return read_page("profile-setup.html")

@app.route("/dashboard")
@app.route("/dashboard.html")
def page_dashboard():
    return read_page("dashboard.html")

@app.route("/directory")
@app.route("/directory.html")
def page_directory():
    return read_page("directory.html")

@app.route("/profile")
@app.route("/profile.html")
def page_profile():
    return read_page("profile.html")

@app.route("/collaborations")
@app.route("/collaborations.html")
def page_collaborations():
    return read_page("collaborations.html")

@app.route("/messages")
@app.route("/messages.html")
def page_messages():
    return read_page("messages.html")

@app.route("/notifications")
@app.route("/notifications.html")
def page_notifications():
    return read_page("notifications.html")

@app.route("/create-collaboration")
@app.route("/create-collaboration.html")
def page_create_collaboration():
    return read_page("create-collaboration.html")

@app.route("/discussion")
@app.route("/discussion.html")
def page_discussion():
    return read_page("discussion.html")

@app.route("/learn")
@app.route("/learn.html")
def page_learn():
    return read_page("learn.html")

# -----------------------------------------------------------------------------
# 1. Locations API
# -----------------------------------------------------------------------------
@app.route("/api/locations", methods=["GET"])
def api_get_locations():
    """Returns the Indian states and districts dataset."""
    return jsonify({
        "success": True,
        "states": get_states(),
        "locations": INDIAN_LOCATIONS
    })

@app.route("/api/locations/states", methods=["GET"])
def api_get_states():
    return jsonify({
        "success": True,
        "states": get_states()
    })

@app.route("/api/locations/districts", methods=["GET"])
def api_get_districts():
    state = request.args.get("state", "").strip()
    districts = get_districts(state)
    return jsonify({
        "success": True,
        "state": state,
        "districts": districts
    })

# -----------------------------------------------------------------------------
# 2. Authentication & Session Endpoints
# -----------------------------------------------------------------------------
@app.route("/api/csrf-token", methods=["GET"])
def api_csrf_token():
    token = get_csrf_token()
    resp = jsonify({"csrf_token": token})
    resp.set_cookie("csrf_token", token, samesite="Lax", httponly=False)
    return resp

@app.route("/api/me", methods=["GET"])
@app.route("/api/session", methods=["GET"])
def api_me():
    """Returns the current authenticated user's profile and CSRF token."""
    user = get_current_user()
    token = get_csrf_token()
    if user:
        return jsonify({"authenticated": True, "user": user, "csrf_token": token})
    return jsonify({"authenticated": False, "user": None, "csrf_token": token})

# -----------------------------------------------------------------------------
# Multilingual / Localization Endpoints
# -----------------------------------------------------------------------------
@app.route("/api/languages", methods=["GET"])
@app.route("/api/locales", methods=["GET"])
def api_get_languages():
    """Returns list of supported languages (English + 22 Scheduled Indian Languages)."""
    return jsonify({
        "success": True,
        "default_language": "en",
        "languages": [
            {
                "code": code,
                "name": info["name"],
                "native_name": info["native_name"],
                "dir": info["dir"],
                "status": info["status"]
            }
            for code, info in SUPPORTED_LANGUAGES.items()
        ]
    })

@app.route("/api/user/language", methods=["POST"])
def api_update_user_language():
    """Persists language preference in session and user account if authenticated."""
    data = request.get_json(silent=True) or request.form
    lang = (data.get("language") or data.get("preferred_language") or "en").strip().lower()

    if lang not in SUPPORTED_LANGUAGES:
        return jsonify({"success": False, "error": f"Unsupported language: {lang}"}), 400

    session["preferred_language"] = lang
    uid = get_current_user_id()
    if uid:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET preferred_language = ? WHERE user_id = ?", (lang, uid))
        conn.commit()
        conn.close()

    return jsonify({
        "success": True,
        "language": lang,
        "language_info": SUPPORTED_LANGUAGES[lang]
    })

@app.route("/api/i18n/audit", methods=["GET"])
def api_i18n_audit():
    """Development check that identifies missing translation keys and coverage statistics."""
    en_path = os.path.join(os.path.dirname(__file__), "locales", "en.json")
    if not os.path.exists(en_path):
        return jsonify({"success": False, "error": "Canonical en.json not found"}), 500

    with open(en_path, "r", encoding="utf-8") as f:
        en_data = json.load(f)

    def flatten_keys(d, prefix=""):
        keys = {}
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                keys.update(flatten_keys(v, full_key))
            else:
                keys[full_key] = v
        return keys

    en_keys = flatten_keys(en_data)
    total_keys = len(en_keys)

    audit_results = {}
    for code, info in SUPPORTED_LANGUAGES.items():
        lang_path = os.path.join(os.path.dirname(__file__), "locales", f"{code}.json")
        if not os.path.exists(lang_path):
            audit_results[code] = {
                "name": info["name"],
                "native_name": info["native_name"],
                "status": "missing_file",
                "total_keys": total_keys,
                "translated_count": 0,
                "missing_count": total_keys,
                "coverage_pct": 0.0,
                "missing_keys": list(en_keys.keys())
            }
            continue

        with open(lang_path, "r", encoding="utf-8") as f:
            lang_data = json.load(f)
        lang_keys = flatten_keys(lang_data)

        missing_keys = []
        translated_count = 0
        for k, en_val in en_keys.items():
            val = lang_keys.get(k)
            if code == "en":
                translated_count += 1
            elif val and val != en_val:
                translated_count += 1
            else:
                missing_keys.append(k)

        cov_pct = round((translated_count / total_keys) * 100, 1) if total_keys else 0.0

        if cov_pct >= 90:
            stage_status = "fully_translated"
        elif cov_pct >= 20:
            stage_status = "partially_translated"
        else:
            stage_status = "staged_awaiting_review"

        audit_results[code] = {
            "name": info["name"],
            "native_name": info["native_name"],
            "declared_status": info["status"],
            "stage_status": stage_status,
            "dir": info["dir"],
            "total_keys": total_keys,
            "translated_count": translated_count,
            "missing_count": len(missing_keys),
            "coverage_pct": cov_pct,
            "missing_keys": missing_keys
        }

    return jsonify({
        "success": True,
        "total_canonical_keys": total_keys,
        "languages_count": len(SUPPORTED_LANGUAGES),
        "audit": audit_results
    })

@app.route("/api/translate", methods=["POST"])
def api_translate():
    """
    Optional translation interface for user-generated content (posts, comments, messages).
    Returns machine translation preview and keeps original content intact.
    """
    data = request.get_json(silent=True) or request.form
    text = (data.get("text") or "").strip()
    source_lang = (data.get("source_lang") or "auto").strip().lower()
    target_lang = (data.get("target_lang") or "en").strip().lower()

    if not text:
        return jsonify({"success": False, "error": "No text provided for translation"}), 400

    if target_lang not in SUPPORTED_LANGUAGES:
        target_lang = "en"

    target_info = SUPPORTED_LANGUAGES.get(target_lang, {})
    target_name = target_info.get("native_name", target_lang)

    return jsonify({
        "success": True,
        "original_text": text,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "target_lang_name": target_name,
        "is_machine_preview": True,
        "translated_text": f"[{target_name} Preview] {text}",
        "disclaimer": "Machine-translated preview. Original content remains unchanged."
    })

@app.route("/api/register", methods=["POST"])
@rate_limit(max_requests=5, window_seconds=600, key_prefix="register")
def api_register():
    data = request.get_json(silent=True) or request.form
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    confirm_password = data.get("confirm_password") or ""
    account_type = (data.get("account_type") or "entrepreneur").strip().lower()
    preferred_language = (data.get("preferred_language") or data.get("language") or "en").strip().lower()

    if account_type not in ["entrepreneur", "community_member"]:
        account_type = "entrepreneur"

    if preferred_language not in SUPPORTED_LANGUAGES:
        preferred_language = "en"

    # Input validation
    if not name or len(name) < 2:
        return jsonify({"success": False, "error": "Please provide a valid full name (at least 2 characters)."}), 400

    if not is_valid_email(email):
        return jsonify({"success": False, "error": "Please provide a valid email address."}), 400

    # Password strength validation: minimum 8 characters
    valid_pass, pass_err = validate_password_strength(password)
    if not valid_pass:
        return jsonify({"success": False, "error": pass_err}), 400

    # Confirm password check (if provided)
    if confirm_password:
        valid_confirm, confirm_err = validate_password_confirmation(password, confirm_password)
        if not valid_confirm:
            return jsonify({"success": False, "error": confirm_err}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check for existing email (case-insensitive)
    cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "error": "An account with this email already exists."}), 409

    user_id = generate_user_id(name, email)
    password_hash = hash_password(password)

    default_avatar = "assets/images/digital_rahul.jpg"
    
    # Clean profile initialization: NO fabricated descriptions, stories, quotes, or products!
    business_name = (data.get("business_name") or "").strip()
    category = (data.get("category") or "").strip()
    state = (data.get("state") or "").strip()
    district = (data.get("district") or "").strip()
    village = (data.get("subdistrict_or_town") or "").strip()
    pincode = (data.get("pincode") or "").strip()
    address_landmark = (data.get("address_landmark") or "").strip()
    pref = (data.get("location_display_preference") or "district_state").strip()
    
    location = format_display_location(state, district, village, pref) if (state or district) else (data.get("location") or "")

    quote = ""
    description = ""
    full_story = ""
    looking_for = "[]"
    skills = "[]"
    website = ""
    phone = ""

    try:
        cursor.execute("""
        INSERT INTO users (
            user_id, name, email, password_hash, account_type,
            business_name, category, location, state, district,
            subdistrict_or_town, pincode, address_landmark, location_display_preference,
            preferred_language,
            avatar, quote, description, full_story, looking_for, skills, website, phone, verified
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            user_id, name, email, password_hash, account_type,
            business_name, category, location, state, district,
            village, pincode, address_landmark, pref,
            preferred_language,
            default_avatar, quote, description, full_story, looking_for, skills, website, phone
        ))
        conn.commit()

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        created_user = safe_user_dict(cursor.fetchone(), is_owner=True)
        conn.close()

        # Establish authenticated session
        session.permanent = True
        session["user_id"] = user_id
        get_csrf_token()

        next_page = "/profile-setup.html" if account_type == "entrepreneur" else "/dashboard.html"

        return jsonify({
            "success": True,
            "user": created_user,
            "account_type": account_type,
            "next_page": next_page
        }), 201

    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "error": "An account with this email already exists."}), 409

@app.route("/api/login", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=300, key_prefix="login")
def api_login():
    data = request.get_json(silent=True) or request.form
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"success": False, "error": "Email and password are required."}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email,))
    user_row = cursor.fetchone()
    conn.close()

    if not user_row or not verify_password(user_row["password_hash"], password):
        return jsonify({"success": False, "error": "Invalid email or password."}), 401

    session.permanent = True
    session["user_id"] = user_row["user_id"]
    get_csrf_token()

    return jsonify({"success": True, "user": safe_user_dict(user_row, is_owner=True)})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully."})

# -----------------------------------------------------------------------------
# 3. Entrepreneur Profiles API
# -----------------------------------------------------------------------------
@app.route("/api/profile", methods=["GET"])
@login_required
def api_get_my_profile():
    uid = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (uid,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    u = safe_user_dict(user, is_owner=True)

    # Fetch products
    cursor.execute("SELECT * FROM products WHERE user_id = ? ORDER BY id DESC", (uid,))
    u["products"] = [dict(p) for p in cursor.fetchall()]

    # Fetch collaborations authored
    cursor.execute("SELECT * FROM collaborations WHERE author_id = ? ORDER BY id DESC", (uid,))
    u["collaborations"] = [dict(c) for c in cursor.fetchall()]

    # Count connections
    cursor.execute("SELECT COUNT(*) FROM connections WHERE user_id_1 = ? OR user_id_2 = ?", (uid, uid))
    u["connections_count"] = cursor.fetchone()[0]

    # Count pending received collaboration requests
    cursor.execute("SELECT COUNT(*) FROM collaboration_requests WHERE receiver_id = ? AND status = 'pending'", (uid,))
    u["pending_requests_count"] = cursor.fetchone()[0]

    conn.close()
    return jsonify(u)

@app.route("/api/profile", methods=["PUT", "POST"])
@login_required
@rate_limit(max_requests=60, window_seconds=60, key_prefix="profile")
def api_update_my_profile():
    uid = get_current_user_id()
    data = request.get_json(silent=True) or request.form

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (uid,))
    current = cursor.fetchone()
    if not current:
        conn.close()
        return jsonify({"success": False, "error": "User not found"}), 404

    name = (data.get("name") if data.get("name") is not None else current["name"]).strip()
    business_name = (data.get("business_name") if data.get("business_name") is not None else current["business_name"]).strip()
    category = (data.get("category") if data.get("category") is not None else current["category"]).strip()
    
    # Location fields
    state = (data.get("state") if data.get("state") is not None else (current["state"] or "")).strip()
    district = (data.get("district") if data.get("district") is not None else (current["district"] or "")).strip()
    subdistrict_or_town = (data.get("subdistrict_or_town") if data.get("subdistrict_or_town") is not None else (current["subdistrict_or_town"] or "")).strip()
    pincode = (data.get("pincode") if data.get("pincode") is not None else (current["pincode"] or "")).strip()
    address_landmark = (data.get("address_landmark") if data.get("address_landmark") is not None else (current["address_landmark"] or "")).strip()
    pref = (data.get("location_display_preference") if data.get("location_display_preference") is not None else (current["location_display_preference"] or "district_state")).strip()

    # Validate state and district
    if state:
        valid_loc, loc_err = is_valid_state_and_district(state, district)
        if not valid_loc:
            conn.close()
            return jsonify({"success": False, "error": loc_err}), 400

    # Validate 6-digit Indian PIN code
    if pincode:
        if not is_valid_pincode(pincode):
            conn.close()
            return jsonify({"success": False, "error": "Please provide a valid 6-digit Indian PIN code."}), 400

    # Format public display location
    computed_loc = format_display_location(state, district, subdistrict_or_town, pref)
    location = computed_loc if computed_loc else (data.get("location") or current["location"])

    quote = data.get("quote") if data.get("quote") is not None else current["quote"]
    description = data.get("description") if data.get("description") is not None else current["description"]
    full_story = data.get("full_story") if data.get("full_story") is not None else current["full_story"]
    raw_website = data.get("website") if data.get("website") is not None else (current["website"] or "")
    website = str(raw_website).strip()
    if website:
        if not is_safe_website_url(website):
            conn.close()
            return jsonify({"success": False, "error": "Invalid website URL. Only http and https web addresses are allowed."}), 400
    phone = data.get("phone") if data.get("phone") is not None else current["phone"]

    # Looking for
    if "looking_for" in data:
        looking_for = data.get("looking_for")
        if isinstance(looking_for, list):
            looking_for_str = json.dumps(looking_for)
        elif isinstance(looking_for, str) and looking_for.strip():
            try:
                parsed = json.loads(looking_for)
                looking_for_str = json.dumps(parsed if isinstance(parsed, list) else [str(parsed)])
            except Exception:
                looking_for_str = json.dumps([item.strip() for item in looking_for.split(",") if item.strip()])
        else:
            looking_for_str = json.dumps([])
    else:
        looking_for_str = current["looking_for"]

    # Skills
    if "skills" in data:
        skills = data.get("skills")
        if isinstance(skills, list):
            skills_str = json.dumps(skills)
        elif isinstance(skills, str) and skills.strip():
            try:
                parsed = json.loads(skills)
                skills_str = json.dumps(parsed if isinstance(parsed, list) else [str(parsed)])
            except Exception:
                skills_str = json.dumps([s.strip() for s in skills.split(",") if s.strip()])
        else:
            skills_str = json.dumps([])
    else:
        skills_str = current["skills"]

    preferred_language = current["preferred_language"] or "en"
    if "preferred_language" in data or "language" in data:
        cand_lang = (data.get("preferred_language") or data.get("language") or "").strip().lower()
        if cand_lang in SUPPORTED_LANGUAGES:
            preferred_language = cand_lang

    cursor.execute("""
    UPDATE users
    SET name = ?,
        business_name = ?,
        category = ?,
        location = ?,
        state = ?,
        district = ?,
        subdistrict_or_town = ?,
        pincode = ?,
        address_landmark = ?,
        location_display_preference = ?,
        preferred_language = ?,
        quote = ?,
        description = ?,
        full_story = ?,
        looking_for = ?,
        skills = ?,
        website = ?,
        phone = ?
    WHERE user_id = ?
    """, (
        name, business_name, category, location, state, district,
        subdistrict_or_town, pincode, address_landmark, pref,
        preferred_language,
        quote, description, full_story, looking_for_str, skills_str,
        website, phone, uid
    ))
    conn.commit()

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (uid,))
    updated_user = safe_user_dict(cursor.fetchone(), is_owner=True)
    conn.close()

    return jsonify({"success": True, "user": updated_user})

@app.route("/api/profile/products", methods=["POST"])
@login_required
@role_required("entrepreneur")
def api_add_product():
    """Allows only entrepreneurs to showcase products."""
    uid = get_current_user_id()
    data = request.get_json(silent=True) or request.form

    name = (data.get("name") or "").strip()
    price = (data.get("price") or "").strip()
    image = (data.get("image") or "assets/images/packaging_spices.jpg").strip()

    if not name or not price:
        return jsonify({"success": False, "error": "Product name and price are required."}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO products (user_id, name, price, image)
    VALUES (?, ?, ?, ?)
    """, (uid, name, price, image))
    prod_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT * FROM products WHERE id = ?", (prod_id,))
    product = dict(cursor.fetchone())
    conn.close()

    return jsonify({"success": True, "product": product}), 201

@app.route("/api/profile/products/<int:prod_id>", methods=["DELETE"])
@login_required
def api_delete_product(prod_id):
    uid = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM products WHERE id = ?", (prod_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"success": False, "error": "Product not found."}), 404

    if row["user_id"] != uid:
        conn.close()
        return jsonify({"success": False, "error": "Unauthorized to delete this product."}), 403

    cursor.execute("DELETE FROM products WHERE id = ?", (prod_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Product removed."})

@app.route("/api/entrepreneurs", methods=["GET"])
def api_entrepreneurs():
    """
    Returns verified and active entrepreneurs with location and category filters.
    Protects private addresses and pincodes from public visibility.
    """
    q = request.args.get("q", "").strip().lower()
    industry = request.args.get("industry", "All").strip()
    location = request.args.get("location", "All").strip()
    state = request.args.get("state", "All").strip()
    district = request.args.get("district", "All").strip()

    conn = get_db()
    cursor = conn.cursor()

    # Only list entrepreneur account_type
    query = "SELECT * FROM users WHERE account_type = 'entrepreneur'"
    params = []

    if industry and industry != "All":
        query += " AND category LIKE ?"
        params.append(f"%{industry}%")

    if state and state != "All":
        query += " AND (state = ? OR location LIKE ?)"
        params.extend([state, f"%{state}%"])

    if district and district != "All":
        query += " AND (district = ? OR location LIKE ?)"
        params.extend([district, f"%{district}%"])

    if location and location != "All":
        query += " AND (location LIKE ? OR state LIKE ? OR district LIKE ?)"
        params.extend([f"%{location}%", f"%{location}%", f"%{location}%"])

    if q:
        query += """ AND (
            LOWER(name) LIKE ? OR
            LOWER(category) LIKE ? OR
            LOWER(location) LIKE ? OR
            LOWER(state) LIKE ? OR
            LOWER(district) LIKE ? OR
            LOWER(subdistrict_or_town) LIKE ? OR
            LOWER(description) LIKE ? OR
            LOWER(business_name) LIKE ?
        )"""
        params.extend([f"%{q}%"] * 8)

    query += " ORDER BY verified DESC, id ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    current_uid = get_current_user_id()
    for r in rows:
        is_owner = (current_uid == r["user_id"])
        u = safe_user_dict(r, is_owner=is_owner)
        cursor.execute("SELECT * FROM products WHERE user_id = ?", (u["user_id"],))
        u["products"] = [dict(p) for p in cursor.fetchall()]
        results.append(u)

    conn.close()
    return jsonify(results)

@app.route("/api/entrepreneurs/<user_id>", methods=["GET"])
def api_entrepreneur_detail(user_id):
    """
    Returns public details of an entrepreneur or user.
    Protects private address and pincode unless viewed by the account owner.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    current_uid = get_current_user_id()
    is_owner = (current_uid == user_id)
    u = safe_user_dict(row, is_owner=is_owner)

    # Fetch products
    cursor.execute("SELECT * FROM products WHERE user_id = ? ORDER BY id DESC", (user_id,))
    u["products"] = [dict(p) for p in cursor.fetchall()]

    # Fetch collaborations
    cursor.execute("SELECT * FROM collaborations WHERE author_id = ? ORDER BY id DESC", (user_id,))
    u["collaborations"] = [dict(c) for c in cursor.fetchall()]

    # Check connection status with current viewer
    u["is_connected"] = False
    u["is_self"] = is_owner
    if current_uid and not is_owner:
        cursor.execute("""
        SELECT id FROM connections
        WHERE (user_id_1 = ? AND user_id_2 = ?) OR (user_id_1 = ? AND user_id_2 = ?)
        """, (current_uid, user_id, user_id, current_uid))
        if cursor.fetchone():
            u["is_connected"] = True

    conn.close()
    return jsonify(u)

# -----------------------------------------------------------------------------
# 4. Community Feed & Posts API
# -----------------------------------------------------------------------------
@app.route("/api/feed", methods=["GET"])
def api_feed():
    post_type = request.args.get("type", "all").strip().lower()
    current_uid = get_current_user_id()

    conn = get_db()
    cursor = conn.cursor()

    query = """
    SELECT p.*, u.name as author_name, u.category as author_category, u.location as author_location, u.avatar as author_avatar
    FROM posts p
    JOIN users u ON p.author_id = u.user_id
    """
    params = []

    if post_type != "all":
        query += " WHERE p.post_type = ?"
        params.append(post_type)

    query += " ORDER BY p.id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        p = dict(r)
        p["has_liked"] = False
        if current_uid:
            cursor.execute("SELECT id FROM post_likes WHERE post_id = ? AND user_id = ?", (p["id"], current_uid))
            if cursor.fetchone():
                p["has_liked"] = True
        results.append(p)

    conn.close()
    return jsonify(results)

@app.route("/api/feed", methods=["POST"])
@login_required
def api_create_post():
    data = request.get_json(silent=True) or request.form
    content = (data.get("content") or "").strip()
    post_type = (data.get("post_type") or "update").strip()
    tag = (data.get("tag") or "Community Update").strip()

    if not content:
        return jsonify({"success": False, "error": "Post content cannot be empty."}), 400

    author_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO posts (author_id, content, post_type, tag, likes, comments_count)
    VALUES (?, ?, ?, ?, 0, 0)
    """, (author_id, content, post_type, tag))
    post_id = cursor.lastrowid
    conn.commit()

    cursor.execute("""
    SELECT p.*, u.name as author_name, u.category as author_category, u.location as author_location, u.avatar as author_avatar
    FROM posts p
    JOIN users u ON p.author_id = u.user_id
    WHERE p.id = ?
    """, (post_id,))
    new_post = dict(cursor.fetchone())
    new_post["has_liked"] = False
    conn.close()

    return jsonify({"success": True, "post": new_post}), 201

@app.route("/api/posts/<int:post_id>/like", methods=["POST"])
@login_required
def api_like_post(post_id):
    uid = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM post_likes WHERE post_id = ? AND user_id = ?", (post_id, uid))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("DELETE FROM post_likes WHERE id = ?", (existing["id"],))
        cursor.execute("UPDATE posts SET likes = MAX(0, likes - 1) WHERE id = ?", (post_id,))
        liked = False
    else:
        cursor.execute("INSERT INTO post_likes (post_id, user_id) VALUES (?, ?)", (post_id, uid))
        cursor.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (post_id,))
        liked = True

    conn.commit()
    cursor.execute("SELECT likes FROM posts WHERE id = ?", (post_id,))
    row = cursor.fetchone()
    conn.close()

    likes_count = row["likes"] if row else 0
    return jsonify({"success": True, "likes": likes_count, "liked": liked})

# -----------------------------------------------------------------------------
# 5. Collaboration Opportunities, Requests & Projects API
# -----------------------------------------------------------------------------
@app.route("/api/collaborations", methods=["GET"])
def api_collaborations():
    collab_type = request.args.get("type", "All").strip()

    conn = get_db()
    cursor = conn.cursor()

    query = """
    SELECT c.*, u.name as author_name, u.avatar as author_avatar
    FROM collaborations c
    JOIN users u ON c.author_id = u.user_id
    """
    params = []

    if collab_type != "All":
        query += " WHERE c.collab_type = ?"
        params.append(collab_type)

    query += " ORDER BY c.id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])

@app.route("/api/collaborations", methods=["POST"])
@login_required
@role_required("entrepreneur")
def api_create_collab():
    """Restricted to entrepreneur accounts."""
    data = request.get_json(silent=True) or request.form
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    category = (data.get("category") or "").strip()
    location = (data.get("location") or "All India").strip()
    collab_type = (data.get("collab_type") or "Seeking Partners").strip()
    tag = (data.get("tag") or category).strip()

    if not title or not description or not category:
        return jsonify({"success": False, "error": "Title, description, and category are required."}), 400

    collab_id = f"collab-{int(os.urandom(4).hex(), 16)}"
    subtitle = description[:80] + ("..." if len(description) > 80 else "")
    author_id = get_current_user_id()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO collaborations (collab_id, title, subtitle, full_description, category, collab_type, tag, location, author_id, thumb, time_ago)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'assets/images/packaging_spices.jpg', 'Just now')
    """, (collab_id, title, subtitle, description, category, collab_type, tag, location, author_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "collab_id": collab_id}), 201

@app.route("/api/collaborations/<collab_id>/propose", methods=["POST"])
@app.route("/api/collaborations/request", methods=["POST"])
@login_required
def api_propose_collab(collab_id=None):
    data = request.get_json(silent=True) or request.form
    message = (data.get("message") or "").strip()
    target_receiver = data.get("receiver_id")
    target_collab_id = collab_id or data.get("collab_id")

    if not message:
        return jsonify({"success": False, "error": "Please enter a proposal message."}), 400

    sender_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()

    receiver_id = target_receiver
    if not receiver_id and target_collab_id:
        cursor.execute("SELECT author_id FROM collaborations WHERE collab_id = ?", (target_collab_id,))
        collab_row = cursor.fetchone()
        if collab_row:
            receiver_id = collab_row["author_id"]

    if not receiver_id:
        conn.close()
        return jsonify({"success": False, "error": "Could not identify recipient for this proposal."}), 400

    if receiver_id == sender_id:
        conn.close()
        return jsonify({"success": False, "error": "You cannot send a collaboration proposal to yourself."}), 400

    cursor.execute("""
    INSERT INTO collaboration_requests (collab_id, sender_id, receiver_id, message, status)
    VALUES (?, ?, ?, ?, 'pending')
    """, (target_collab_id, sender_id, receiver_id, message))
    req_id = cursor.lastrowid

    # Create notification for receiver
    cursor.execute("SELECT name FROM users WHERE user_id = ?", (sender_id,))
    s_user = cursor.fetchone()
    s_name = s_user["name"] if s_user else "An entrepreneur"
    preview = message[:120] + ("..." if len(message) > 120 else "")
    dedup = f"collab_req:{req_id}:{receiver_id}"
    create_notification(
        cursor,
        recipient_id=receiver_id,
        actor_id=sender_id,
        event_type="collab_request_received",
        title=f"Partnership Request from {s_name}",
        message=f"{s_name} sent a collaboration proposal: \"{preview}\"",
        reference_type="collaboration_request",
        reference_id=str(req_id),
        link_url="collaborations.html",
        dedup_key=dedup
    )

    conn.commit()
    conn.close()

    return jsonify({"success": True, "request_id": req_id, "message": "Collaboration proposal recorded and sent."})

@app.route("/api/collaborations/requests", methods=["GET"])
@login_required
def api_get_collab_requests():
    uid = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT cr.*, u.name as sender_name, u.avatar as sender_avatar, u.category as sender_category,
           u.location as sender_location, c.title as collab_title
    FROM collaboration_requests cr
    JOIN users u ON cr.sender_id = u.user_id
    LEFT JOIN collaborations c ON cr.collab_id = c.collab_id
    WHERE cr.receiver_id = ?
    ORDER BY cr.id DESC
    """, (uid,))
    received = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
    SELECT cr.*, u.name as receiver_name, u.avatar as receiver_avatar, u.category as receiver_category,
           u.location as receiver_location, c.title as collab_title
    FROM collaboration_requests cr
    JOIN users u ON cr.receiver_id = u.user_id
    LEFT JOIN collaborations c ON cr.collab_id = c.collab_id
    WHERE cr.sender_id = ?
    ORDER BY cr.id DESC
    """, (uid,))
    sent = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return jsonify({"received": received, "sent": sent})

@app.route("/api/collaborations/requests/<int:req_id>/action", methods=["POST"])
@app.route("/api/collaborations/requests/<int:req_id>/respond", methods=["POST"])
@login_required
def api_handle_collab_request(req_id):
    uid = get_current_user_id()
    data = request.get_json(silent=True) or request.form
    action = (data.get("action") or "").strip().lower()

    if action not in ["accept", "reject"]:
        return jsonify({"success": False, "error": "Action must be 'accept' or 'reject'."}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM collaboration_requests WHERE id = ?", (req_id,))
    req_row = cursor.fetchone()

    if not req_row:
        conn.close()
        return jsonify({"success": False, "error": "Collaboration request not found."}), 404

    if req_row["receiver_id"] != uid:
        conn.close()
        return jsonify({"success": False, "error": "Unauthorized to update this request."}), 403

    new_status = "accepted" if action == "accept" else "rejected"
    cursor.execute("""
    UPDATE collaboration_requests
    SET status = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (new_status, req_id))

    project_id = None
    collab_conv_id = None

    sender_id = req_row["sender_id"]
    cursor.execute("SELECT name FROM users WHERE user_id = ?", (uid,))
    responder_user = cursor.fetchone()
    responder_name = responder_user["name"] if responder_user else "Partner"

    if action == "accept":
        collab_title = "Joint Entrepreneurship Collaboration"
        collab_category = "General Enterprise"
        if req_row["collab_id"]:
            cursor.execute("SELECT title, category FROM collaborations WHERE collab_id = ?", (req_row["collab_id"],))
            c_info = cursor.fetchone()
            if c_info:
                collab_title = c_info["title"]
                collab_category = c_info["category"]

        # Prevent duplicate project creation if repeated
        cursor.execute("""
        SELECT id FROM collaborative_projects
        WHERE ((partner1_id = ? AND partner2_id = ?) OR (partner1_id = ? AND partner2_id = ?))
          AND title = ?
        """, (sender_id, uid, uid, sender_id, collab_title))
        existing_proj = cursor.fetchone()

        if existing_proj:
            project_id = existing_proj["id"]
        else:
            cursor.execute("""
            INSERT INTO collaborative_projects (title, description, category, partner1_id, partner2_id, status)
            VALUES (?, ?, ?, ?, ?, 'Active')
            """, (
                collab_title,
                req_row["message"],
                collab_category,
                sender_id,
                uid
            ))
            project_id = cursor.lastrowid

        cursor.execute("""
        INSERT OR IGNORE INTO connections (user_id_1, user_id_2, status)
        VALUES (?, ?, 'connected')
        """, (sender_id, uid))
        cursor.execute("""
        INSERT OR IGNORE INTO connections (user_id_1, user_id_2, status)
        VALUES (?, ?, 'connected')
        """, (uid, sender_id))

        # Ensure collaboration conversation exists for this project (prevent duplicate creation)
        cursor.execute("SELECT id, conv_id FROM conversations WHERE project_id = ?", (project_id,))
        existing_conv = cursor.fetchone()

        if existing_conv:
            collab_conv_id = existing_conv["conv_id"]
        else:
            collab_conv_id = f"conv-collab-{project_id}"
            cursor.execute("""
            INSERT INTO conversations (conv_id, conv_type, title, project_id, collab_id, created_by, updated_at)
            VALUES (?, 'collaboration', ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (collab_conv_id, collab_title, project_id, req_row["collab_id"], uid))
            c_id = cursor.lastrowid

            cursor.execute("INSERT OR IGNORE INTO conversation_participants (conversation_id, conv_id, user_id, role) VALUES (?, ?, ?, 'creator')", (c_id, collab_conv_id, uid))
            cursor.execute("INSERT OR IGNORE INTO conversation_participants (conversation_id, conv_id, user_id, role) VALUES (?, ?, ?, 'member')", (c_id, collab_conv_id, sender_id))

            sys_msg_id = f"msg-{os.urandom(6).hex()}"
            cursor.execute("""
            INSERT INTO messages (msg_id, conversation_id, conv_id, sender_id, body, message_type)
            VALUES (?, ?, ?, ?, ?, 'system')
            """, (sys_msg_id, c_id, collab_conv_id, uid, f"Collaboration request accepted! Joint project '{collab_title}' formed."))

        # Notification for requester on acceptance
        dedup = f"collab_resp:{req_id}:accepted"
        link = f"messages.html?conversation={collab_conv_id}" if collab_conv_id else "collaborations.html"
        create_notification(
            cursor,
            recipient_id=sender_id,
            actor_id=uid,
            event_type="collab_request_accepted",
            title=f"Partnership Accepted by {responder_name}",
            message=f"{responder_name} accepted your collaboration proposal for '{collab_title}'! A joint project and chat have been started.",
            reference_type="collaboration_request",
            reference_id=str(req_id),
            link_url=link,
            dedup_key=dedup
        )
    else:
        # action == "reject"
        collab_title = "Joint Collaboration"
        if req_row["collab_id"]:
            cursor.execute("SELECT title FROM collaborations WHERE collab_id = ?", (req_row["collab_id"],))
            c_info = cursor.fetchone()
            if c_info:
                collab_title = c_info["title"]
        dedup = f"collab_resp:{req_id}:rejected"
        create_notification(
            cursor,
            recipient_id=sender_id,
            actor_id=uid,
            event_type="collab_request_rejected",
            title="Partnership Proposal Declined",
            message=f"{responder_name} declined your collaboration proposal for '{collab_title}'.",
            reference_type="collaboration_request",
            reference_id=str(req_id),
            link_url="collaborations.html",
            dedup_key=dedup
        )

    conn.commit()
    conn.close()
    return jsonify({
        "success": True,
        "status": new_status,
        "project_id": project_id,
        "conv_id": collab_conv_id
    })

@app.route("/api/collaborative-projects", methods=["GET"])
@app.route("/api/collaborations/projects", methods=["GET"])
def api_collaborative_projects():
    user_only = request.args.get("my", "false").lower() == "true"
    uid = get_current_user_id()

    conn = get_db()
    cursor = conn.cursor()

    if user_only and uid:
        cursor.execute("""
        SELECT cp.*,
               u1.name as partner1_name, u1.avatar as partner1_avatar,
               u2.name as partner2_name, u2.avatar as partner2_avatar
        FROM collaborative_projects cp
        JOIN users u1 ON cp.partner1_id = u1.user_id
        JOIN users u2 ON cp.partner2_id = u2.user_id
        WHERE cp.partner1_id = ? OR cp.partner2_id = ?
        ORDER BY cp.id DESC
        """, (uid, uid))
    else:
        cursor.execute("""
        SELECT cp.*,
               u1.name as partner1_name, u1.avatar as partner1_avatar,
               u2.name as partner2_name, u2.avatar as partner2_avatar
        FROM collaborative_projects cp
        JOIN users u1 ON cp.partner1_id = u1.user_id
        JOIN users u2 ON cp.partner2_id = u2.user_id
        ORDER BY cp.id DESC
        """)

    projects = [dict(p) for p in cursor.fetchall()]
    conn.close()
    return jsonify(projects)

# -----------------------------------------------------------------------------
# 6. Discussions & Comments API
# -----------------------------------------------------------------------------
@app.route("/api/discussions", methods=["GET"])
def api_discussions():
    tag = request.args.get("tag", "All").strip()
    conn = get_db()
    cursor = conn.cursor()

    query = """
    SELECT d.*, u.name as author_name, u.category as author_category, u.location as author_location, u.avatar as author_avatar
    FROM discussions d
    JOIN users u ON d.author_id = u.user_id
    """
    params = []
    if tag != "All":
        query += " WHERE d.tag = ?"
        params.append(tag)

    query += " ORDER BY d.id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    discs = []
    for d in rows:
        item = dict(d)
        cursor.execute("SELECT COUNT(*) FROM comments WHERE disc_id = ?", (item["disc_id"],))
        item["comments_count"] = cursor.fetchone()[0]
        discs.append(item)

    conn.close()
    return jsonify(discs)

@app.route("/api/discussions", methods=["POST"])
@login_required
def api_create_discussion():
    data = request.get_json(silent=True) or request.form
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    tag = (data.get("tag") or "Question").strip()

    if not title or not body:
        return jsonify({"success": False, "error": "Title and body are required."}), 400

    disc_id = f"disc-{int(os.urandom(4).hex(), 16)}"
    author_id = get_current_user_id()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO discussions (disc_id, author_id, title, body, tag, likes)
    VALUES (?, ?, ?, ?, ?, 0)
    """, (disc_id, author_id, title, body, tag))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "disc_id": disc_id}), 201

@app.route("/api/discussions/<disc_id>", methods=["GET"])
def api_discussion(disc_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT d.*, u.name as author_name, u.category as author_category, u.location as author_location, u.avatar as author_avatar
    FROM discussions d
    JOIN users u ON d.author_id = u.user_id
    WHERE d.disc_id = ?
    """, (disc_id,))
    disc = cursor.fetchone()
    if not disc:
        conn.close()
        return jsonify({"error": "Discussion not found"}), 404

    d_dict = dict(disc)

    cursor.execute("""
    SELECT c.*, u.name as author_name, u.category as author_category, u.location as author_location, u.avatar as author_avatar
    FROM comments c
    JOIN users u ON c.author_id = u.user_id
    WHERE c.disc_id = ?
    ORDER BY c.id ASC
    """, (disc_id,))
    d_dict["comments"] = [dict(c) for c in cursor.fetchall()]

    conn.close()
    return jsonify(d_dict)

@app.route("/api/discussions/<disc_id>/comment", methods=["POST"])
@app.route("/api/discussions/<disc_id>/comments", methods=["POST"])
@login_required
def api_add_comment(disc_id):
    data = request.get_json(silent=True) or request.form
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"success": False, "error": "Comment text cannot be empty."}), 400

    author_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO comments (disc_id, author_id, text, time_ago)
    VALUES (?, ?, ?, 'Just now')
    """, (disc_id, author_id, text))
    comment_id = cursor.lastrowid

    # Notify discussion author if not self
    cursor.execute("SELECT author_id, title FROM discussions WHERE disc_id = ?", (disc_id,))
    disc_row = cursor.fetchone()
    if disc_row and disc_row["author_id"] != author_id:
        cursor.execute("SELECT name FROM users WHERE user_id = ?", (author_id,))
        c_user = cursor.fetchone()
        c_name = c_user["name"] if c_user else "A community member"
        preview = text[:100] + ("..." if len(text) > 100 else "")
        create_notification(
            cursor,
            recipient_id=disc_row["author_id"],
            actor_id=author_id,
            event_type="new_comment",
            title=f"New comment from {c_name}",
            message=f"{c_name} replied to '{disc_row['title']}': \"{preview}\"",
            reference_type="discussion",
            reference_id=disc_id,
            link_url=f"discussion.html?id={disc_id}",
            dedup_key=f"comment:{comment_id}:{disc_row['author_id']}"
        )

    conn.commit()

    cursor.execute("""
    SELECT c.*, u.name as author_name, u.avatar as author_avatar
    FROM comments c
    JOIN users u ON c.author_id = u.user_id
    WHERE c.id = ?
    """, (comment_id,))
    new_comment = dict(cursor.fetchone())
    conn.close()

    return jsonify({"success": True, "comment": new_comment}), 201

# -----------------------------------------------------------------------------
# 7. Learn & Share Articles API
# -----------------------------------------------------------------------------
@app.route("/api/articles", methods=["GET"])
def api_articles():
    category = request.args.get("category", "All").strip()

    conn = get_db()
    cursor = conn.cursor()

    query = """
    SELECT a.*, u.name as author_name, u.category as author_category, u.avatar as author_avatar
    FROM articles a
    JOIN users u ON a.author_id = u.user_id
    """
    params = []

    if category != "All":
        query += " WHERE a.category = ?"
        params.append(category)

    query += " ORDER BY a.id ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        if "lessons" in d and isinstance(d["lessons"], str):
            try:
                d["lessons"] = json.loads(d["lessons"])
            except Exception:
                d["lessons"] = []
        results.append(d)

    return jsonify(results)

# -----------------------------------------------------------------------------
# 8. Connect API
# -----------------------------------------------------------------------------
@app.route("/api/connect", methods=["POST"])
@login_required
def api_connect():
    data = request.get_json(silent=True) or request.form
    target_id = (data.get("target_id") or "").strip()
    current_id = get_current_user_id()

    if not target_id or target_id == current_id:
        return jsonify({"success": False, "error": "Invalid target entrepreneur."}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id FROM connections
    WHERE (user_id_1 = ? AND user_id_2 = ?) OR (user_id_1 = ? AND user_id_2 = ?)
    """, (current_id, target_id, target_id, current_id))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("DELETE FROM connections WHERE id = ?", (existing["id"],))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "status": "disconnected"})
    else:
        cursor.execute("""
        INSERT INTO connections (user_id_1, user_id_2, status)
        VALUES (?, ?, 'connected')
        """, (current_id, target_id))

        cursor.execute("SELECT name FROM users WHERE user_id = ?", (current_id,))
        c_user = cursor.fetchone()
        c_name = c_user["name"] if c_user else "An entrepreneur"
        create_notification(
            cursor,
            recipient_id=target_id,
            actor_id=current_id,
            event_type="new_connection",
            title=f"New connection with {c_name}",
            message=f"{c_name} connected with you on ThriveHub.",
            reference_type="user",
            reference_id=current_id,
            link_url=f"profile.html?id={current_id}",
            dedup_key=f"connect:{current_id}:{target_id}"
        )

        conn.commit()
        conn.close()
        return jsonify({"success": True, "status": "connected"})

@app.route("/api/connections", methods=["GET"])
@login_required
def api_get_connections():
    current_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT DISTINCT u.* FROM users u
    JOIN connections c ON (c.user_id_1 = u.user_id AND c.user_id_2 = ?)
                       OR (c.user_id_2 = u.user_id AND c.user_id_1 = ?)
    WHERE u.user_id != ?
    """, (current_id, current_id, current_id))
    rows = cursor.fetchall()
    conn.close()

    return jsonify([safe_user_dict(r, is_owner=(current_id == r["user_id"])) for r in rows])

# -----------------------------------------------------------------------------
# 9. Real-Time Database-Backed Messaging API (Phase 2)
# -----------------------------------------------------------------------------

@app.route("/api/conversations", methods=["GET"])
@login_required
def api_get_conversations():
    """
    Returns list of conversations for current user with participant details,
    latest message snippet, timestamp, and unread count.
    """
    uid = get_current_user_id()
    filter_type = request.args.get("type", "all").strip().lower()

    conn = get_db()
    cursor = conn.cursor()

    query = """
    SELECT c.id, c.conv_id, c.conv_type, c.title, c.project_id, c.collab_id,
           c.created_by, c.created_at, c.updated_at,
           cp.last_read_at, cp.role as my_role
    FROM conversations c
    JOIN conversation_participants cp ON c.id = cp.conversation_id
    WHERE cp.user_id = ?
    """
    params = [uid]

    if filter_type in ["direct", "collaboration"]:
        query += " AND c.conv_type = ?"
        params.append(filter_type)

    query += " ORDER BY c.updated_at DESC"
    cursor.execute(query, params)
    conv_rows = cursor.fetchall()

    results = []
    for cr in conv_rows:
        conv_dict = dict(cr)
        c_id = conv_dict["id"]
        last_read_at = conv_dict["last_read_at"]

        # Calculate unread messages (sent by others after my last_read_at)
        cursor.execute("""
        SELECT COUNT(*) FROM messages
        WHERE conversation_id = ? AND sender_id != ? AND created_at > ?
        """, (c_id, uid, last_read_at))
        conv_dict["unread_count"] = cursor.fetchone()[0]

        # Get latest message
        cursor.execute("""
        SELECT m.id, m.msg_id, m.sender_id, m.body, m.message_type, m.created_at,
               u.name as sender_name
        FROM messages m
        JOIN users u ON m.sender_id = u.user_id
        WHERE m.conversation_id = ?
        ORDER BY m.id DESC LIMIT 1
        """, (c_id,))
        latest_msg = cursor.fetchone()
        conv_dict["last_message"] = dict(latest_msg) if latest_msg else None

        # Get participants
        cursor.execute("""
        SELECT cp.user_id, cp.role, u.name, u.avatar, u.account_type,
               u.business_name, u.category, u.location, u.verified
        FROM conversation_participants cp
        JOIN users u ON cp.user_id = u.user_id
        WHERE cp.conversation_id = ?
        """, (c_id,))
        participants = [dict(p) for p in cursor.fetchall()]
        conv_dict["participants"] = participants

        # For direct conversations, find the other participant
        other_part = next((p for p in participants if p["user_id"] != uid), None)
        if not other_part and participants:
            other_part = participants[0]
        conv_dict["other_participant"] = other_part

        # Check if other participant is blocked
        if other_part:
            cursor.execute("""
            SELECT blocker_id FROM user_blocks
            WHERE (blocker_id = ? AND blocked_id = ?)
               OR (blocker_id = ? AND blocked_id = ?)
            """, (uid, other_part["user_id"], other_part["user_id"], uid))
            block_row = cursor.fetchone()
            conv_dict["is_blocked"] = block_row is not None
            conv_dict["blocked_by_me"] = (block_row["blocker_id"] == uid) if block_row else False
        else:
            conv_dict["is_blocked"] = False
            conv_dict["blocked_by_me"] = False

        results.append(conv_dict)

    conn.close()
    return jsonify({"success": True, "conversations": results})


@app.route("/api/conversations", methods=["POST"])
@login_required
@rate_limit(max_requests=20, window_seconds=600)
def api_create_or_get_conversation():
    """
    Creates a new direct or collaboration conversation, or retrieves an existing one.
    Idempotent: Reuses existing direct conversation between same pair of users.
    """
    current_uid = get_current_user_id()
    data = request.get_json(silent=True) or request.form

    recipient_id = (data.get("recipient_id") or "").strip()
    project_id = data.get("project_id")
    initial_message = (data.get("initial_message") or "").strip()

    conn = get_db()
    cursor = conn.cursor()

    # Case A: Collaboration conversation requested via project_id
    if project_id:
        try:
            project_id = int(project_id)
        except (ValueError, TypeError):
            conn.close()
            return jsonify({"success": False, "error": "Invalid project ID."}), 400

        cursor.execute("SELECT * FROM collaborative_projects WHERE id = ?", (project_id,))
        proj = cursor.fetchone()
        if not proj:
            conn.close()
            return jsonify({"success": False, "error": "Collaborative project not found."}), 404

        # Check that current user is one of the project partners
        if current_uid not in [proj["partner1_id"], proj["partner2_id"]]:
            conn.close()
            return jsonify({"success": False, "error": "You are not an authorized partner on this project."}), 403

        # Check if conversation already exists for this project
        cursor.execute("SELECT * FROM conversations WHERE project_id = ?", (project_id,))
        existing = cursor.fetchone()
        if existing:
            conv_dict = dict(existing)
            conn.close()
            return jsonify({"success": True, "conversation": conv_dict, "is_new": False}), 200

        # Create new collaboration conversation inside transaction
        collab_conv_id = f"conv-collab-{project_id}"
        with conn:
            cursor.execute("""
            INSERT INTO conversations (conv_id, conv_type, title, project_id, created_by, updated_at)
            VALUES (?, 'collaboration', ?, ?, ?, CURRENT_TIMESTAMP)
            """, (collab_conv_id, proj["title"], project_id, current_uid))
            new_c_id = cursor.lastrowid

            cursor.execute("INSERT INTO conversation_participants (conversation_id, conv_id, user_id, role) VALUES (?, ?, ?, 'creator')", (new_c_id, collab_conv_id, current_uid))
            other_uid = proj["partner2_id"] if proj["partner1_id"] == current_uid else proj["partner1_id"]
            cursor.execute("INSERT INTO conversation_participants (conversation_id, conv_id, user_id, role) VALUES (?, ?, ?, 'member')", (new_c_id, collab_conv_id, other_uid))

            # System welcome message
            sys_msg_id = f"msg-{os.urandom(6).hex()}"
            cursor.execute("""
            INSERT INTO messages (msg_id, conversation_id, conv_id, sender_id, body, message_type)
            VALUES (?, ?, ?, ?, ?, 'system')
            """, (sys_msg_id, new_c_id, collab_conv_id, current_uid, f"Collaboration project '{proj['title']}' active. Coordinate deliverables here."))

        cursor.execute("SELECT * FROM conversations WHERE id = ?", (new_c_id,))
        new_conv = dict(cursor.fetchone())
        conn.close()
        return jsonify({"success": True, "conversation": new_conv, "is_new": True}), 201

    # Case B: Direct conversation between current user and recipient
    if not recipient_id:
        conn.close()
        return jsonify({"success": False, "error": "Recipient ID or Project ID is required."}), 400

    if recipient_id == current_uid:
        conn.close()
        return jsonify({"success": False, "error": "You cannot start a conversation with yourself."}), 400

    # Verify recipient exists
    cursor.execute("SELECT user_id, name FROM users WHERE user_id = ?", (recipient_id,))
    recipient = cursor.fetchone()
    if not recipient:
        conn.close()
        return jsonify({"success": False, "error": "Recipient user not found."}), 404

    # Check blocking
    cursor.execute("""
    SELECT blocker_id FROM user_blocks
    WHERE (blocker_id = ? AND blocked_id = ?) OR (blocker_id = ? AND blocked_id = ?)
    """, (current_uid, recipient_id, recipient_id, current_uid))
    block_row = cursor.fetchone()
    if block_row:
        conn.close()
        return jsonify({"success": False, "error": "Cannot start conversation. Communication is blocked between these accounts."}), 403

    direct_key = make_direct_key(current_uid, recipient_id)

    cursor.execute("SELECT * FROM conversations WHERE direct_key = ?", (direct_key,))
    existing = cursor.fetchone()

    if existing:
        c_id = existing["id"]
        conv_id = existing["conv_id"]
        conv_dict = dict(existing)

        # If an initial message was supplied, append it in a transaction
        if initial_message:
            if len(initial_message) > 2000:
                conn.close()
                return jsonify({"success": False, "error": "Message body exceeds 2000 characters."}), 400

            with conn:
                msg_id = f"msg-{os.urandom(6).hex()}"
                cursor.execute("""
                INSERT INTO messages (msg_id, conversation_id, conv_id, sender_id, body, message_type)
                VALUES (?, ?, ?, ?, ?, 'text')
                """, (msg_id, c_id, conv_id, current_uid, initial_message))
                cursor.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (c_id,))
                cursor.execute("UPDATE conversation_participants SET last_read_at = CURRENT_TIMESTAMP WHERE conversation_id = ? AND user_id = ?", (c_id, current_uid))

                cursor.execute("SELECT name FROM users WHERE user_id = ?", (current_uid,))
                s_user = cursor.fetchone()
                s_name = s_user["name"] if s_user else "Someone"
                preview = initial_message[:120] + ("..." if len(initial_message) > 120 else "")
                create_notification(
                    cursor,
                    recipient_id=recipient_id,
                    actor_id=current_uid,
                    event_type="new_message",
                    title=f"New message from {s_name}",
                    message=preview,
                    reference_type="conversation",
                    reference_id=conv_id,
                    link_url=f"messages.html?conversation={conv_id}",
                    dedup_key=f"msg:{msg_id}:{recipient_id}"
                )

        conn.close()
        return jsonify({"success": True, "conversation": conv_dict, "is_new": False}), 200

    # Create new direct conversation in transaction
    conv_id = f"conv-{os.urandom(6).hex()}"
    with conn:
        cursor.execute("""
        INSERT INTO conversations (conv_id, conv_type, direct_key, created_by, updated_at)
        VALUES (?, 'direct', ?, ?, CURRENT_TIMESTAMP)
        """, (conv_id, direct_key, current_uid))
        new_c_id = cursor.lastrowid

        cursor.execute("INSERT INTO conversation_participants (conversation_id, conv_id, user_id, role) VALUES (?, ?, ?, 'creator')", (new_c_id, conv_id, current_uid))
        cursor.execute("INSERT INTO conversation_participants (conversation_id, conv_id, user_id, role) VALUES (?, ?, ?, 'member')", (new_c_id, conv_id, recipient_id))

        if initial_message:
            if len(initial_message) > 2000:
                raise ValueError("Message body exceeds 2000 characters.")
            msg_id = f"msg-{os.urandom(6).hex()}"
            cursor.execute("""
            INSERT INTO messages (msg_id, conversation_id, conv_id, sender_id, body, message_type)
            VALUES (?, ?, ?, ?, ?, 'text')
            """, (msg_id, new_c_id, conv_id, current_uid, initial_message))

            cursor.execute("SELECT name FROM users WHERE user_id = ?", (current_uid,))
            s_user = cursor.fetchone()
            s_name = s_user["name"] if s_user else "Someone"
            preview = initial_message[:120] + ("..." if len(initial_message) > 120 else "")
            create_notification(
                cursor,
                recipient_id=recipient_id,
                actor_id=current_uid,
                event_type="new_message",
                title=f"New message from {s_name}",
                message=preview,
                reference_type="conversation",
                reference_id=conv_id,
                link_url=f"messages.html?conversation={conv_id}",
                dedup_key=f"msg:{msg_id}:{recipient_id}"
            )

    cursor.execute("SELECT * FROM conversations WHERE id = ?", (new_c_id,))
    new_conv = dict(cursor.fetchone())
    conn.close()
    return jsonify({"success": True, "conversation": new_conv, "is_new": True}), 201


@app.route("/api/conversations/<conv_id>/messages", methods=["GET"])
@login_required
def api_get_conversation_messages(conv_id):
    """
    Retrieves paginated message history for a conversation.
    Verifies that the authenticated user is a participant.
    """
    uid = get_current_user_id()
    limit = min(int(request.args.get("limit", 50)), 100)
    before_id = request.args.get("before_id")

    conn = get_db()
    cursor = conn.cursor()

    # Verify conversation exists and user is a participant
    cursor.execute("""
    SELECT c.*, cp.last_read_at
    FROM conversations c
    JOIN conversation_participants cp ON c.id = cp.conversation_id
    WHERE c.conv_id = ? AND cp.user_id = ?
    """, (conv_id, uid))
    participant_row = cursor.fetchone()

    if not participant_row:
        conn.close()
        return jsonify({"success": False, "error": "Conversation not found or access denied."}), 403

    c_id = participant_row["id"]

    query = """
    SELECT m.id, m.msg_id, m.sender_id, m.body, m.message_type, m.created_at,
           u.name as sender_name, u.avatar as sender_avatar
    FROM messages m
    JOIN users u ON m.sender_id = u.user_id
    WHERE m.conversation_id = ?
    """
    params = [c_id]

    if before_id:
        try:
            query += " AND m.id < ?"
            params.append(int(before_id))
        except ValueError:
            pass

    query += " ORDER BY m.id DESC LIMIT ?"
    params.append(limit + 1)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    has_more = len(rows) > limit
    message_slice = rows[:limit]
    messages = [dict(r) for r in reversed(message_slice)]

    # Automatically mark conversation as read for this user
    cursor.execute("""
    UPDATE conversation_participants
    SET last_read_at = CURRENT_TIMESTAMP
    WHERE conversation_id = ? AND user_id = ?
    """, (c_id, uid))
    conn.commit()

    conv_info = dict(participant_row)

    # Get other participant info for direct chats
    if conv_info["conv_type"] == "direct":
        cursor.execute("""
        SELECT u.user_id, u.name, u.avatar, u.account_type, u.business_name, u.category, u.location, u.verified
        FROM conversation_participants cp
        JOIN users u ON cp.user_id = u.user_id
        WHERE cp.conversation_id = ? AND cp.user_id != ?
        """, (c_id, uid))
        other_row = cursor.fetchone()
        conv_info["other_participant"] = dict(other_row) if other_row else None
    else:
        conv_info["other_participant"] = None

    conn.close()
    return jsonify({
        "success": True,
        "messages": messages,
        "has_more": has_more,
        "conversation": conv_info
    })


@app.route("/api/conversations/<conv_id>/messages", methods=["POST"])
@login_required
@rate_limit(max_requests=40, window_seconds=60)
def api_send_message(conv_id):
    """
    Sends a message to a conversation.
    Sender ID is strictly extracted from authenticated session.
    Verifies membership and blocking status.
    """
    current_uid = get_current_user_id()
    data = request.get_json(silent=True) or request.form

    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"success": False, "error": "Message body cannot be empty."}), 400

    if len(body) > 2000:
        return jsonify({"success": False, "error": "Message body exceeds 2000 characters."}), 400

    conn = get_db()
    cursor = conn.cursor()

    # 1. Verify user is a participant
    cursor.execute("""
    SELECT c.id, c.conv_type, c.direct_key, cp.id as part_id
    FROM conversations c
    JOIN conversation_participants cp ON c.id = cp.conversation_id
    WHERE c.conv_id = ? AND cp.user_id = ?
    """, (conv_id, current_uid))
    membership = cursor.fetchone()

    if not membership:
        conn.close()
        return jsonify({"success": False, "error": "Unauthorized. You are not a participant in this conversation."}), 403

    c_id = membership["id"]

    # 2. Check if blocked (for direct conversations)
    if membership["conv_type"] == "direct":
        cursor.execute("""
        SELECT cp.user_id FROM conversation_participants cp
        WHERE cp.conversation_id = ? AND cp.user_id != ?
        """, (c_id, current_uid))
        other_part = cursor.fetchone()
        if other_part:
            other_uid = other_part["user_id"]
            cursor.execute("""
            SELECT blocker_id FROM user_blocks
            WHERE (blocker_id = ? AND blocked_id = ?) OR (blocker_id = ? AND blocked_id = ?)
            """, (current_uid, other_uid, other_uid, current_uid))
            if cursor.fetchone():
                conn.close()
                return jsonify({"success": False, "error": "Cannot send message. Communication is blocked between these users."}), 403

    # 3. Insert message in transaction
    msg_id = f"msg-{os.urandom(6).hex()}"
    with conn:
        cursor.execute("""
        INSERT INTO messages (msg_id, conversation_id, conv_id, sender_id, body, message_type)
        VALUES (?, ?, ?, ?, ?, 'text')
        """, (msg_id, c_id, conv_id, current_uid, body))
        new_msg_id = cursor.lastrowid

        cursor.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (c_id,))
        cursor.execute("UPDATE conversation_participants SET last_read_at = CURRENT_TIMESTAMP WHERE conversation_id = ? AND user_id = ?", (c_id, current_uid))

        # Create notifications for all other participants in conversation
        cursor.execute("""
        SELECT user_id FROM conversation_participants
        WHERE conversation_id = ? AND user_id != ?
        """, (c_id, current_uid))
        other_parts = cursor.fetchall()

        cursor.execute("SELECT name FROM users WHERE user_id = ?", (current_uid,))
        s_user = cursor.fetchone()
        s_name = s_user["name"] if s_user else "Someone"
        preview = body[:120] + ("..." if len(body) > 120 else "")

        for part in other_parts:
            target_uid = part["user_id"]
            dedup = f"msg:{msg_id}:{target_uid}"
            create_notification(
                cursor,
                recipient_id=target_uid,
                actor_id=current_uid,
                event_type="new_message",
                title=f"New message from {s_name}",
                message=preview,
                reference_type="conversation",
                reference_id=conv_id,
                link_url=f"messages.html?conversation={conv_id}",
                dedup_key=dedup
            )

    cursor.execute("""
    SELECT m.id, m.msg_id, m.sender_id, m.body, m.message_type, m.created_at,
           u.name as sender_name, u.avatar as sender_avatar
    FROM messages m
    JOIN users u ON m.sender_id = u.user_id
    WHERE m.id = ?
    """, (new_msg_id,))
    new_msg = dict(cursor.fetchone())
    conn.close()

    return jsonify({"success": True, "message": new_msg}), 201


@app.route("/api/conversations/<conv_id>/read", methods=["POST"])
@login_required
def api_mark_conversation_read(conv_id):
    """Marks all messages in the conversation as read for the current user."""
    uid = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT c.id FROM conversations c
    JOIN conversation_participants cp ON c.id = cp.conversation_id
    WHERE c.conv_id = ? AND cp.user_id = ?
    """, (conv_id, uid))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"success": False, "error": "Conversation not found or access denied."}), 403

    cursor.execute("""
    UPDATE conversation_participants
    SET last_read_at = CURRENT_TIMESTAMP
    WHERE conversation_id = ? AND user_id = ?
    """, (row["id"], uid))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "unread_count": 0})


@app.route("/api/conversations/unread-count", methods=["GET"])
@login_required
def api_get_total_unread_count():
    """Returns total unread messages count across all conversations for current user."""
    uid = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*)
    FROM messages m
    JOIN conversation_participants cp ON m.conversation_id = cp.conversation_id
    WHERE cp.user_id = ? AND m.sender_id != ? AND m.created_at > cp.last_read_at
    """, (uid, uid))
    total_unread = cursor.fetchone()[0]
    conn.close()

    return jsonify({"success": True, "unread_count": total_unread})


@app.route("/api/users/<target_user_id>/block", methods=["POST"])
@login_required
def api_block_user(target_user_id):
    """Blocks a user, preventing further messaging."""
    current_uid = get_current_user_id()
    if target_user_id == current_uid:
        return jsonify({"success": False, "error": "You cannot block yourself."}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (target_user_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "error": "Target user not found."}), 404

    data = request.get_json(silent=True) or request.form
    reason = (data.get("reason") or "").strip()

    cursor.execute("""
    INSERT OR IGNORE INTO user_blocks (blocker_id, blocked_id, reason)
    VALUES (?, ?, ?)
    """, (current_uid, target_user_id, reason))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "blocked": True, "message": "User has been blocked."})


@app.route("/api/users/<target_user_id>/unblock", methods=["POST"])
@login_required
def api_unblock_user(target_user_id):
    """Unblocks a previously blocked user."""
    current_uid = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM user_blocks WHERE blocker_id = ? AND blocked_id = ?
    """, (current_uid, target_user_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "blocked": False, "message": "User has been unblocked."})


@app.route("/api/users/<target_user_id>/block-status", methods=["GET"])
@login_required
def api_get_block_status(target_user_id):
    """Checks block status between current user and target user."""
    current_uid = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM user_blocks WHERE blocker_id = ? AND blocked_id = ?", (current_uid, target_user_id))
    blocked_by_me = cursor.fetchone() is not None

    cursor.execute("SELECT id FROM user_blocks WHERE blocker_id = ? AND blocked_id = ?", (target_user_id, current_uid))
    blocked_by_them = cursor.fetchone() is not None

    conn.close()
    return jsonify({
        "success": True,
        "blocked_by_me": blocked_by_me,
        "blocked_by_them": blocked_by_them,
        "is_blocked": blocked_by_me or blocked_by_them
    })


# -----------------------------------------------------------------------------
# 11. In-App Notification System API
# -----------------------------------------------------------------------------
@app.route("/api/notifications", methods=["GET"])
@login_required
def api_get_notifications():
    """
    Lists notifications for the authenticated user with pagination and optional unread filter.
    Only the authenticated user's notifications are ever returned.
    """
    current_uid = get_current_user_id()
    limit = request.args.get("limit", 20)
    try:
        limit = max(1, min(int(limit), 100))
    except (ValueError, TypeError):
        limit = 20

    offset = request.args.get("offset", 0)
    try:
        offset = max(0, int(offset))
    except (ValueError, TypeError):
        offset = 0

    unread_only = request.args.get("unread", "").lower() in ["1", "true", "yes"]
    event_type = (request.args.get("type") or "").strip()

    conn = get_db()
    cursor = conn.cursor()

    query = """
    SELECT n.id, n.recipient_id, n.actor_id, n.event_type, n.title, n.message,
           n.reference_type, n.reference_id, n.link_url, n.is_read, n.created_at,
           u.name as actor_name, u.avatar as actor_avatar, u.category as actor_category
    FROM notifications n
    LEFT JOIN users u ON n.actor_id = u.user_id
    WHERE n.recipient_id = ?
    """
    params = [current_uid]

    if unread_only:
        query += " AND n.is_read = 0"
    if event_type:
        query += " AND n.event_type = ?"
        params.append(event_type)

    query += " ORDER BY n.created_at DESC, n.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    notifs = [dict(row) for row in cursor.fetchall()]

    # Total counts
    cursor.execute("SELECT COUNT(*) FROM notifications WHERE recipient_id = ?", (current_uid,))
    total_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM notifications WHERE recipient_id = ? AND is_read = 0", (current_uid,))
    unread_count = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "success": True,
        "notifications": notifs,
        "total_count": total_count,
        "unread_count": unread_count,
        "limit": limit,
        "offset": offset
    })


@app.route("/api/notifications/unread-count", methods=["GET"])
@login_required
def api_get_notifications_unread_count():
    """Returns the unread notifications count for the authenticated user."""
    current_uid = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM notifications WHERE recipient_id = ? AND is_read = 0", (current_uid,))
    unread_count = cursor.fetchone()[0]
    conn.close()
    return jsonify({"success": True, "unread_count": unread_count})


@app.route("/api/notifications/<int:notif_id>/read", methods=["POST"])
@login_required
def api_mark_notification_read(notif_id):
    """
    Marks a single notification as read.
    Enforces that only the recipient can mark the notification as read.
    """
    current_uid = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, recipient_id, is_read FROM notifications WHERE id = ?", (notif_id,))
    notif = cursor.fetchone()

    if not notif:
        conn.close()
        return jsonify({"success": False, "error": "Notification not found."}), 404

    if notif["recipient_id"] != current_uid:
        conn.close()
        return jsonify({"success": False, "error": "Unauthorized. You cannot modify notifications belonging to another user."}), 403

    cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND recipient_id = ?", (notif_id, current_uid))
    cursor.execute("SELECT COUNT(*) FROM notifications WHERE recipient_id = ? AND is_read = 0", (current_uid,))
    unread_count = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "id": notif_id,
        "unread_count": unread_count
    })


@app.route("/api/notifications/read-all", methods=["POST"])
@login_required
def api_mark_all_notifications_read():
    """Marks all notifications as read for the authenticated user."""
    current_uid = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("UPDATE notifications SET is_read = 1 WHERE recipient_id = ? AND is_read = 0", (current_uid,))
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "unread_count": 0,
        "message": "All notifications marked as read."
    })


@app.route("/api/notifications/<int:notif_id>", methods=["DELETE"])
@login_required
def api_delete_notification(notif_id):
    """Deletes a notification belonging to the authenticated user."""
    current_uid = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, recipient_id FROM notifications WHERE id = ?", (notif_id,))
    notif = cursor.fetchone()

    if not notif:
        conn.close()
        return jsonify({"success": False, "error": "Notification not found."}), 404

    if notif["recipient_id"] != current_uid:
        conn.close()
        return jsonify({"success": False, "error": "Unauthorized. You cannot delete notifications belonging to another user."}), 403

    cursor.execute("DELETE FROM notifications WHERE id = ? AND recipient_id = ?", (notif_id, current_uid))
    cursor.execute("SELECT COUNT(*) FROM notifications WHERE recipient_id = ? AND is_read = 0", (current_uid,))
    unread_count = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "id": notif_id,
        "unread_count": unread_count
    })

# -----------------------------------------------------------------------------
# App Runner
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("==================================================")
    print("  Starting ThriveHub Production Server (Port 5000)")
    print("  SQLite Database: udyamsetu.db")
    print("  Access Platform at: http://127.0.0.1:5000/")
    print("==================================================")
    app.run(host="0.0.0.0", port=5000, debug=True)

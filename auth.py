import re
import json
import time
import secrets
import functools
from collections import defaultdict
from flask import session, jsonify, request, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

# In-memory sliding-window store for rate limiting: key -> list of timestamps
_RATE_LIMIT_STORE = defaultdict(list)

def get_client_ip() -> str:
    """Extracts client IP address safely, respecting reverse proxy headers if set."""
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr or "127.0.0.1"

def check_rate_limit(key: str, max_requests: int, window_seconds: int):
    """
    In-memory sliding window rate limiter.
    Returns (allowed: bool, retry_after: int).
    Note: Application-level rate limiting prevents brute force and credential stuffing,
    while DDoS protection requires network/infrastructure layer mitigations (e.g. WAF/CDN).
    """
    try:
        if current_app and current_app.config.get("TESTING"):
            if not request.headers.get("X-Test-Rate-Limit"):
                return True, 0
    except RuntimeError:
        pass

    now = time.time()
    timestamps = _RATE_LIMIT_STORE[key]
    # Prune timestamps older than window
    cutoff = now - window_seconds
    valid_timestamps = [t for t in timestamps if t > cutoff]
    _RATE_LIMIT_STORE[key] = valid_timestamps

    if len(valid_timestamps) >= max_requests:
        oldest = valid_timestamps[0]
        retry_after = int(oldest + window_seconds - now) + 1
        return False, max(1, retry_after)

    _RATE_LIMIT_STORE[key].append(now)
    return True, 0

def clear_rate_limits():
    """Clears rate limit store (used in automated testing)."""
    _RATE_LIMIT_STORE.clear()

def rate_limit(max_requests: int, window_seconds: int, key_prefix: str = ""):
    """Decorator to apply rate limiting by client IP."""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            ip = get_client_ip()
            key = f"{key_prefix}:{ip}"
            allowed, retry_after = check_rate_limit(key, max_requests, window_seconds)
            if not allowed:
                return jsonify({
                    "success": False,
                    "error": f"Too many requests. Please wait {retry_after} seconds before trying again."
                }), 429
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# -----------------------------------------------------------------------------
# Password & Input Validation
# -----------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(password_hash: str, password: str) -> bool:
    if not password_hash or not password:
        return False
    return check_password_hash(password_hash, password)

def is_valid_email(email: str) -> bool:
    if not email or len(email) > 120:
        return False
    return bool(EMAIL_REGEX.match(email))

def validate_password_strength(password: str):
    """
    Validates password strength:
    - Minimum 8 characters
    - Returns (valid: bool, message: str)
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    return True, ""

def validate_password_confirmation(password: str, confirm_password: str):
    if password != confirm_password:
        return False, "Passwords do not match."
    return True, ""

def is_safe_website_url(url: str) -> bool:
    """Validates that a URL uses safe protocols (http/https) and contains no dangerous schemes."""
    if not url:
        return True
    u = url.strip().lower()
    if u.startswith("javascript:") or u.startswith("data:") or u.startswith("vbscript:") or "<" in u or ">" in u or '"' in u:
        return False
    if "://" in u:
        return u.startswith("http://") or u.startswith("https://")
    if ":" in u:
        return False
    return True

# -----------------------------------------------------------------------------
# CSRF Token Management
# -----------------------------------------------------------------------------
def get_csrf_token() -> str:
    """Generates or retrieves CSRF token from current session."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]

def verify_csrf_token(token: str) -> bool:
    """Validates provided CSRF token against session token."""
    expected = session.get("csrf_token")
    if not expected or not token:
        return False
    return secrets.compare_digest(str(expected), str(token))

# -----------------------------------------------------------------------------
# Safe Serialization & User Helpers
# -----------------------------------------------------------------------------
def safe_user_dict(row, is_owner: bool = False):
    """
    Serializes a user row into a safe dictionary.
    - Strips passwords and hashes.
    - Parses JSON lists.
    - Enforces location privacy: detailed addresses (address_landmark, pincode)
      are excluded for public views unless is_owner is True.
    """
    if row is None:
        return None
    d = dict(row)
    # Remove sensitive authentication credentials
    d.pop("password", None)
    d.pop("password_hash", None)

    # Parse JSON fields safely
    for field in ["looking_for", "skills", "lessons"]:
        if field in d and isinstance(d[field], str):
            try:
                d[field] = json.loads(d[field])
            except Exception:
                d[field] = []

    # Enforce location privacy for public viewing
    if not is_owner:
        d.pop("address_landmark", None)
        d.pop("pincode", None)

    return d

def get_current_user_id():
    """Returns the authenticated user_id from session, or None."""
    uid = session.get("user_id")
    if not uid:
        return None
    return str(uid).strip()

def get_current_user():
    """Returns the authenticated user dict from SQLite, or None."""
    uid = get_current_user_id()
    if not uid:
        return None

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (uid,))
    user = cursor.fetchone()
    conn.close()

    # The logged-in user viewing their own account has is_owner=True
    return safe_user_dict(user, is_owner=True)

def login_required(f):
    """Decorator to protect API endpoints against unauthorized access."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_current_user_id():
            return jsonify({
                "success": False,
                "error": "Authentication required. Please log in to perform this action."
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role: str):
    """
    Decorator to protect role-restricted API endpoints.
    Allows only users with matching account_type (e.g. 'entrepreneur').
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({
                    "success": False,
                    "error": "Authentication required. Please log in to perform this action."
                }), 401
            
            user_role = user.get("account_type", "entrepreneur")
            if user_role != required_role:
                role_label = "entrepreneurs" if required_role == "entrepreneur" else required_role
                return jsonify({
                    "success": False,
                    "error": f"Permission denied. Only registered {role_label} can perform this action."
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def generate_user_id(name: str, email: str) -> str:
    """Generates a clean, unique user_id slug."""
    base = re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")
    if not base:
        base = email.split("@")[0].lower().replace(".", "-")
    
    conn = get_db()
    cursor = conn.cursor()
    candidate = base
    suffix = 1
    while True:
        cursor.execute("SELECT id FROM users WHERE user_id = ?", (candidate,))
        if not cursor.fetchone():
            break
        candidate = f"{base}-{suffix}"
        suffix += 1
    conn.close()
    return candidate

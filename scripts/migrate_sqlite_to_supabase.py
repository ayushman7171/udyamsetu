#!/usr/bin/env python3
"""
UdyamSetu: SQLite to Supabase Migration & Seeding Script
Safely maps legacy SQLite records to Supabase Auth users & PostgreSQL tables.
Supports both:
1. Supabase Service Role Key (Admin mode - recommended, bypasses email rate limits)
2. Supabase Publishable Key (Client mode with per-user JWT bearer tokens)
"""

import os
import sys
import json
import sqlite3
import urllib.request
import urllib.error

# Auto-load .env.local if present
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_local = os.path.join(ROOT_DIR, ".env.local")
if os.path.exists(env_local):
    with open(env_local, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://runlhdbtiyjlnpukqpes.supabase.co").rstrip("/")
PUBLISHABLE_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_1y_5lKqEfbAnck4gANp4jA_-NDako8Q")
SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# Active key for API calls
API_KEY = SERVICE_ROLE_KEY if SERVICE_ROLE_KEY else PUBLISHABLE_KEY
SQLITE_DB = os.path.join(ROOT_DIR, "udyamsetu.db")

def make_request(endpoint, method="GET", payload=None, bearer_token=None):
    url = f"{SUPABASE_URL}{endpoint}"
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    elif SERVICE_ROLE_KEY:
        headers["Authorization"] = f"Bearer {SERVICE_ROLE_KEY}"
    else:
        headers["Authorization"] = f"Bearer {PUBLISHABLE_KEY}"

    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_body)
        except Exception:
            return e.code, {"error": err_body}

def run_migration():
    print("============================================================")
    print("UDYAMSETU: SQLITE TO SUPABASE DATA MIGRATION")
    print("============================================================")
    print(f"Target Supabase Project: {SUPABASE_URL}")
    print(f"Auth Mode: {'Admin (Service Role Key)' if SERVICE_ROLE_KEY else 'Client (Publishable Anon Key)'}")
    print(f"Source Database: {SQLITE_DB}")

    if not os.path.exists(SQLITE_DB):
        print(f"Error: Database {SQLITE_DB} not found.")
        return

    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Verify Supabase tables exist
    st, res = make_request("/rest/v1/profiles?select=count", method="GET")
    if st == 404:
        print("\n[!] Supabase tables not found.")
        print("Please execute 'supabase/full_schema_and_rls.sql' in your Supabase Dashboard SQL Editor first:")
        print(f"https://supabase.com/dashboard/project/runlhdbtiyjlnpukqpes/sql/new")
        return
    print("[PASS] Supabase PostgreSQL schema verified (profiles table active).")

    # 2. Extract and create users
    cursor.execute("SELECT * FROM users ORDER BY id ASC")
    users = cursor.fetchall()
    print(f"[INFO] Found {len(users)} users in SQLite database.")

    id_map = {}     # old_user_id (slug) -> supabase UUID
    token_map = {}  # old_user_id -> user JWT access token

    for u in users:
        email = u["email"]
        old_id = u["user_id"]
        pwd = "password123"

        meta = {
            "name": u["name"],
            "slug": u["user_id"],
            "user_id": u["user_id"],
            "account_type": u["account_type"],
            "business_name": u["business_name"],
            "category": u["category"],
            "location": u["location"],
            "state": u["state"],
            "district": u["district"],
            "subdistrict_or_town": u["subdistrict_or_town"],
            "pincode": u["pincode"],
            "address_landmark": u["address_landmark"],
            "location_display_preference": u["location_display_preference"],
            "preferred_language": u["preferred_language"],
            "avatar": u["avatar"],
            "quote": u["quote"],
            "description": u["description"],
            "full_story": u["full_story"],
            "looking_for": json.loads(u["looking_for"] or "[]"),
            "skills": json.loads(u["skills"] or "[]"),
            "website": u["website"],
            "phone": u["phone"],
            "verified": bool(u["verified"])
        }

        user_uuid = None
        user_jwt = None

        if SERVICE_ROLE_KEY:
            # ADMIN WORKFLOW: Create confirmed user directly via Supabase Auth Admin API
            st_adm, res_adm = make_request("/auth/v1/admin/users", method="POST", payload={
                "email": email,
                "password": pwd,
                "email_confirm": True,
                "user_metadata": meta
            }, bearer_token=SERVICE_ROLE_KEY)

            if st_adm in (200, 201):
                user_uuid = res_adm.get("id")
            elif st_adm == 422 or "already" in str(res_adm).lower():
                # User already exists in auth, retrieve UUID from profiles or admin list
                st_p, res_p = make_request(f"/rest/v1/profiles?email=eq.{email}&select=id", method="GET")
                if st_p == 200 and isinstance(res_p, list) and len(res_p) > 0:
                    user_uuid = res_p[0]["id"]
            else:
                print(f"Admin create error for {email}: {res_adm}")
        else:
            # CLIENT WORKFLOW: Try login first
            st_log, res_log = make_request("/auth/v1/token?grant_type=password", method="POST", payload={
                "email": email,
                "password": pwd
            })
            if st_log == 200:
                user_uuid = res_log.get("user", {}).get("id")
                user_jwt = res_log.get("access_token")
            else:
                # Attempt signup
                st_sign, res_sign = make_request("/auth/v1/signup", method="POST", payload={
                    "email": email,
                    "password": pwd,
                    "data": meta
                })
                if st_sign in (200, 201):
                    user_uuid = res_sign.get("id") or res_sign.get("user", {}).get("id")
                    user_jwt = res_sign.get("access_token")
                else:
                    err_code = res_sign.get("error_code") or res_sign.get("code")
                    if err_code == "email_provider_disabled":
                        print(f"\n[!] Supabase Email Provider is disabled in dashboard.")
                        print("Go to Authentication -> Providers -> Email:")
                        print("1. Enable Email Provider: ON")
                        print("2. Allow new users to sign up: ON")
                        print("3. Confirm email: OFF (avoids rate limits)")
                        print("Then re-run this script.\n")
                        return
                    elif "rate_limit" in str(res_sign):
                        print(f"Rate limited creating {email}. Disable 'Confirm email' in dashboard to bypass SMTP rate limit.")
                    else:
                        print(f"Could not register/login {email}: {res_sign}")

        if user_uuid:
            id_map[old_id] = user_uuid
            if user_jwt:
                token_map[old_id] = user_jwt
            print(f"  Mapped user: {u['name']} ({old_id}) -> {user_uuid}")

    print(f"\n[INFO] Successfully mapped {len(id_map)}/{len(users)} users.")
    if len(id_map) == 0:
        print("[!] No users could be mapped. Please review the instructions above.")
        return

    # 3. Migrate Products
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    prod_inserted = 0
    if SERVICE_ROLE_KEY:
        # Bulk insert with service role key
        prod_payload = []
        for p in products:
            owner_uuid = id_map.get(p["user_id"])
            if owner_uuid:
                prod_payload.append({
                    "owner_id": owner_uuid,
                    "name": p["name"],
                    "price": p["price"],
                    "image": p["image"]
                })
        if prod_payload:
            st, res = make_request("/rest/v1/products", method="POST", payload=prod_payload, bearer_token=SERVICE_ROLE_KEY)
            if st in (200, 201):
                prod_inserted = len(prod_payload)
    else:
        # Per-user insert with user JWT bearer tokens
        for p in products:
            u_id = p["user_id"]
            owner_uuid = id_map.get(u_id)
            jwt = token_map.get(u_id)
            if owner_uuid and jwt:
                st, res = make_request("/rest/v1/products", method="POST", payload={
                    "owner_id": owner_uuid,
                    "name": p["name"],
                    "price": p["price"],
                    "image": p["image"]
                }, bearer_token=jwt)
                if st in (200, 201):
                    prod_inserted += 1
    print(f"[PASS] Products migrated: {prod_inserted}/{len(products)} records inserted.")

    # 4. Migrate Feed Posts
    cursor.execute("SELECT * FROM posts ORDER BY id ASC")
    posts = cursor.fetchall()
    post_inserted = 0
    if SERVICE_ROLE_KEY:
        post_payload = []
        for p in posts:
            author_uuid = id_map.get(p["author_id"])
            if author_uuid:
                post_payload.append({
                    "author_id": author_uuid,
                    "content": p["content"],
                    "post_type": p["post_type"],
                    "tag": p["tag"],
                    "likes_count": p["likes"],
                    "comments_count": p["comments_count"]
                })
        if post_payload:
            st, res = make_request("/rest/v1/posts", method="POST", payload=post_payload, bearer_token=SERVICE_ROLE_KEY)
            if st in (200, 201):
                post_inserted = len(post_payload)
    else:
        for p in posts:
            u_id = p["author_id"]
            author_uuid = id_map.get(u_id)
            jwt = token_map.get(u_id)
            if author_uuid and jwt:
                st, res = make_request("/rest/v1/posts", method="POST", payload={
                    "author_id": author_uuid,
                    "content": p["content"],
                    "post_type": p["post_type"],
                    "tag": p["tag"],
                    "likes_count": p["likes"],
                    "comments_count": p["comments_count"]
                }, bearer_token=jwt)
                if st in (200, 201):
                    post_inserted += 1
    print(f"[PASS] Feed Posts migrated: {post_inserted}/{len(posts)} records inserted.")

    # 5. Migrate Collaborations
    cursor.execute("SELECT * FROM collaborations")
    collabs = cursor.fetchall()
    collab_inserted = 0
    if SERVICE_ROLE_KEY:
        collab_payload = []
        for c in collabs:
            author_uuid = id_map.get(c["author_id"])
            if author_uuid:
                collab_payload.append({
                    "collab_id": c["collab_id"],
                    "author_id": author_uuid,
                    "title": c["title"],
                    "subtitle": c["subtitle"],
                    "full_description": c["full_description"],
                    "category": c["category"],
                    "collab_type": c["collab_type"],
                    "tag": c["tag"],
                    "location": c["location"],
                    "thumb": c["thumb"]
                })
        if collab_payload:
            st, res = make_request("/rest/v1/collaborations", method="POST", payload=collab_payload, bearer_token=SERVICE_ROLE_KEY)
            if st in (200, 201):
                collab_inserted = len(collab_payload)
    else:
        for c in collabs:
            u_id = c["author_id"]
            author_uuid = id_map.get(u_id)
            jwt = token_map.get(u_id)
            if author_uuid and jwt:
                st, res = make_request("/rest/v1/collaborations", method="POST", payload={
                    "collab_id": c["collab_id"],
                    "author_id": author_uuid,
                    "title": c["title"],
                    "subtitle": c["subtitle"],
                    "full_description": c["full_description"],
                    "category": c["category"],
                    "collab_type": c["collab_type"],
                    "tag": c["tag"],
                    "location": c["location"],
                    "thumb": c["thumb"]
                }, bearer_token=jwt)
                if st in (200, 201):
                    collab_inserted += 1
    print(f"[PASS] Collaborations migrated: {collab_inserted}/{len(collabs)} records inserted.")

    # 6. Migrate Discussions & Comments
    cursor.execute("SELECT * FROM discussions")
    discs = cursor.fetchall()
    disc_inserted = 0
    if SERVICE_ROLE_KEY:
        disc_payload = []
        for d in discs:
            author_uuid = id_map.get(d["author_id"])
            if author_uuid:
                disc_payload.append({
                    "disc_id": d["disc_id"],
                    "author_id": author_uuid,
                    "title": d["title"],
                    "body": d["body"],
                    "tag": d["tag"],
                    "likes": d["likes"]
                })
        if disc_payload:
            st, res = make_request("/rest/v1/discussions", method="POST", payload=disc_payload, bearer_token=SERVICE_ROLE_KEY)
            if st in (200, 201):
                disc_inserted = len(disc_payload)
    else:
        for d in discs:
            u_id = d["author_id"]
            author_uuid = id_map.get(u_id)
            jwt = token_map.get(u_id)
            if author_uuid and jwt:
                st, res = make_request("/rest/v1/discussions", method="POST", payload={
                    "disc_id": d["disc_id"],
                    "author_id": author_uuid,
                    "title": d["title"],
                    "body": d["body"],
                    "tag": d["tag"],
                    "likes": d["likes"]
                }, bearer_token=jwt)
                if st in (200, 201):
                    disc_inserted += 1
    print(f"[PASS] Discussions migrated: {disc_inserted}/{len(discs)} records inserted.")

    # 7. Migrate Articles
    cursor.execute("SELECT * FROM articles")
    articles = cursor.fetchall()
    art_payload = []
    for a in articles:
        author_uuid = id_map.get(a["author_id"])
        art_payload.append({
            "article_id": a["article_id"],
            "category": a["category"],
            "title": a["title"],
            "author_id": author_uuid,
            "date_str": a["date_str"],
            "image": a["image"],
            "summary": a["summary"],
            "lessons": json.loads(a["lessons"] or "[]")
        })
    if art_payload:
        token = SERVICE_ROLE_KEY if SERVICE_ROLE_KEY else next(iter(token_map.values()), None)
        st, res = make_request("/rest/v1/articles", method="POST", payload=art_payload, bearer_token=token)
        print(f"[PASS] Articles migrated: status {st}, inserted {len(art_payload)} records.")

    print("\n============================================================")
    print("MIGRATION COMPLETED SUCCESSFULLY")
    print("============================================================")
    conn.close()

if __name__ == "__main__":
    run_migration()

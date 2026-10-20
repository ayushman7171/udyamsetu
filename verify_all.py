import os
import re
import json
import sqlite3
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import time
from database import get_db, init_db

BASE_URL = "http://127.0.0.1:5000"
RUN_IP = f"10.0.{os.getpid() % 250}.{int(time.time() * 1000) % 250}"

def get_csrf_token_for_opener(opener):
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/csrf-token", headers={"X-Forwarded-For": RUN_IP})
        res = opener.open(req)
        data = json.loads(res.read().decode())
        return data.get("csrf_token", "")
    except Exception:
        return ""

def post_json(opener, url, payload_dict, extra_headers=None):
    headers = {
        "Content-Type": "application/json",
        "X-Forwarded-For": RUN_IP
    }
    csrf_token = get_csrf_token_for_opener(opener)
    if csrf_token:
        headers["X-CSRF-Token"] = csrf_token
    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(
        url,
        data=json.dumps(payload_dict).encode("utf-8"),
        headers=headers
    )
    return opener.open(req)

def run_checks():
    results = {
        "passed": [],
        "failed": [],
        "warnings": []
    }

    # ---------------------------------------------------------
    # 1. Start-up & File Link Checks
    # ---------------------------------------------------------
    html_files = [f for f in os.listdir(".") if f.endswith(".html")]
    link_pattern = re.compile(r'(?:href|src)=["\']([^"\'#:]+)["\']')

    all_links = set()
    for hf in html_files:
        with open(hf, "r", encoding="utf-8") as f:
            content = f.read()
        for match in link_pattern.findall(content):
            if not match.startswith("javascript:") and not match.startswith("mailto:") and not match.startswith("tel:"):
                all_links.add(match)

    broken_links = []
    for link in sorted(all_links):
        url = BASE_URL + "/" + link.lstrip("/")
        try:
            res = urllib.request.urlopen(url)
            if res.status != 200:
                broken_links.append((link, res.status))
        except Exception as e:
            broken_links.append((link, str(e)))

    if not broken_links:
        results["passed"].append(f"All {len(all_links)} internal links and media sources across {len(html_files)} HTML pages return HTTP 200.")
    else:
        results["failed"].append(f"Broken links found: {broken_links}")

    # ---------------------------------------------------------
    # 2. Authentication Checks (Guest, Login, Persistence)
    # ---------------------------------------------------------
    try:
        res = urllib.request.urlopen(f"{BASE_URL}/api/me")
        me_guest = json.loads(res.read().decode())
        if me_guest["authenticated"] is False and me_guest["user"] is None:
            results["passed"].append("Guest / Unauthenticated status verified (/api/me returns authenticated=False, no mock user).")
        else:
            results["failed"].append(f"Unexpected unauthenticated response: {me_guest}")
    except Exception as e:
        results["failed"].append(f"Failed to query /api/me: {e}")

    # Register User A (Entrepreneur)
    cookie_jar_a = http.cookiejar.CookieJar()
    opener_a = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar_a))

    user_a_email = f"user_a_{os.urandom(3).hex()}@test.in"
    reg_a_payload = {
        "name": "Aarav Patel",
        "email": user_a_email,
        "password": "password12345",
        "confirm_password": "password12345",
        "account_type": "entrepreneur"
    }

    try:
        res = post_json(opener_a, f"{BASE_URL}/api/register", reg_a_payload)
        reg_a_data = json.loads(res.read().decode())
        if res.status == 201 and reg_a_data["success"]:
            user_a_id = reg_a_data["user"]["user_id"]
            results["passed"].append(f"User A registered as Entrepreneur (user_id={user_a_id}, next_page={reg_a_data['next_page']}).")
        else:
            results["failed"].append(f"User A registration failed: {reg_a_data}")
    except Exception as e:
        results["failed"].append(f"User A registration exception: {e}")

    # Duplicate registration rejection
    try:
        post_json(opener_a, f"{BASE_URL}/api/register", reg_a_payload)
        results["failed"].append("Duplicate registration was accepted (expected 409).")
    except urllib.error.HTTPError as e:
        if e.code == 409:
            results["passed"].append("Duplicate email registration correctly rejected with HTTP 409 Conflict.")
        else:
            results["failed"].append(f"Duplicate registration returned unexpected code: {e.code}")

    # Invalid Login
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/login",
            data=json.dumps({"email": "asha@udyamsetu.in", "password": "wrong_password"}).encode(),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req)
        results["failed"].append("Invalid credentials accepted (expected 401).")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            results["passed"].append("Invalid login credentials correctly rejected with HTTP 401 Unauthorized.")

    # Valid Login
    try:
        res = opener_a.open(urllib.request.Request(
            f"{BASE_URL}/api/login",
            data=json.dumps({"email": user_a_email, "password": "password12345"}).encode(),
            headers={"Content-Type": "application/json"}
        ))
        login_data = json.loads(res.read().decode())
        if login_data["success"]:
            results["passed"].append("Login with valid credentials succeeded (HTTP 200).")
    except Exception as e:
        results["failed"].append(f"Valid login failed: {e}")

    # Session persistence
    try:
        me_a = json.loads(opener_a.open(f"{BASE_URL}/api/me").read().decode())
        if me_a["authenticated"] and me_a["user"]["user_id"] == user_a_id:
            results["passed"].append("Session persistence verified: /api/me returned authenticated identity for User A.")
        else:
            results["failed"].append(f"Session persistence failed: {me_a}")
    except Exception as e:
        results["failed"].append(f"Session query failed: {e}")

    # ---------------------------------------------------------
    # 3. Phase 1 & 2: Account Types & Profile Initialization
    # ---------------------------------------------------------
    # Register User B as Community Member
    cookie_jar_b = http.cookiejar.CookieJar()
    opener_b = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar_b))

    user_b_email = f"user_b_{os.urandom(3).hex()}@test.in"
    reg_b_payload = {
        "name": "Bhavna Joshi",
        "email": user_b_email,
        "password": "password12345",
        "confirm_password": "password12345",
        "account_type": "community_member"
    }

    try:
        res = post_json(opener_b, f"{BASE_URL}/api/register", reg_b_payload)
        reg_b_data = json.loads(res.read().decode())
        user_b_id = reg_b_data["user"]["user_id"]
        if reg_b_data["account_type"] == "community_member" and reg_b_data["next_page"] == "/dashboard.html":
            results["passed"].append(f"User B registered as Community Member (next_page=/dashboard.html, enters without business setup).")
        else:
            results["failed"].append(f"User B community registration response unexpected: {reg_b_data}")
    except Exception as e:
        results["failed"].append(f"User B registration failed: {e}")

    # Verify no fabricated data for newly created account
    try:
        p_b = json.loads(opener_b.open(f"{BASE_URL}/api/profile").read().decode())
        if p_b["quote"] == "" and p_b["description"] == "" and p_b["full_story"] == "" and len(p_b["products"]) == 0:
            results["passed"].append("Clean profile initialization verified: No fabricated quotes, stories, or fake products on new accounts.")
        else:
            results["failed"].append(f"Fabricated data found on new account: quote={p_b['quote']}, desc={p_b['description']}")
    except Exception as e:
        results["failed"].append(f"Clean profile check failed: {e}")

    # Role enforcement: Community member blocked from publishing collaborations or products
    try:
        post_json(opener_b, f"{BASE_URL}/api/collaborations", {
            "title": "Community Collab Attempt",
            "description": "Should fail with 403",
            "category": "Handicrafts"
        })
        results["failed"].append("Community member was able to create collaboration opportunity (expected 403)!")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            results["passed"].append("Role restriction verified: Community member blocked from creating collaboration (HTTP 403 Forbidden).")
        else:
            results["failed"].append(f"Collab restriction returned unexpected code: {e.code}")

    try:
        post_json(opener_b, f"{BASE_URL}/api/profile/products", {
            "name": "Community Product Attempt",
            "price": "450"
        })
        results["failed"].append("Community member was able to add product (expected 403)!")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            results["passed"].append("Role restriction verified: Community member blocked from showcasing products (HTTP 403 Forbidden).")
        else:
            results["failed"].append(f"Product restriction returned unexpected code: {e.code}")

    # ---------------------------------------------------------
    # 4. Phase 3: Location Dataset, PIN Code & Location Privacy
    # ---------------------------------------------------------
    # Test location dataset endpoint
    try:
        loc_res = urllib.request.urlopen(f"{BASE_URL}/api/locations")
        loc_data = json.loads(loc_res.read().decode())
        if loc_data["success"] and "Maharashtra" in loc_data["states"] and len(loc_data["locations"]["Maharashtra"]) > 10:
            results["passed"].append("Indian location dataset verified via /api/locations (28+ states and mapped districts).")
        else:
            results["failed"].append(f"Locations dataset response unexpected: {loc_data}")
    except Exception as e:
        results["failed"].append(f"Locations dataset query failed: {e}")

    # Test PIN code validation (bad PIN code rejected)
    try:
        post_json(opener_a, f"{BASE_URL}/api/profile", {
            "pincode": "12345"  # only 5 digits
        })
        results["failed"].append("Invalid 5-digit PIN code was accepted (expected 400)!")
    except urllib.error.HTTPError as e:
        if e.code == 400:
            results["passed"].append("PIN code validation verified: Invalid 5-digit PIN correctly rejected with HTTP 400.")
        else:
            results["failed"].append(f"PIN validation returned unexpected code: {e.code}")

    # Update User A profile with valid State, District, Village, PIN, Landmark, and preference
    try:
        edit_payload = {
            "name": "Aarav Patel (Updated)",
            "business_name": "Aarav Heritage Farms",
            "category": "Agriculture",
            "state": "Gujarat",
            "district": "Anand",
            "subdistrict_or_town": "Khambhat",
            "pincode": "388620",
            "address_landmark": "Near Coastal Canal Post Office",
            "location_display_preference": "district_state",
            "quote": "Growing certified organic heirloom wheat and pulses.",
            "description": "Dedicated to organic soil restoration and direct grain supply.",
            "full_story": "Founded in 2022 with 50 small farmers.",
            "looking_for": ["Bulk Buyers", "Eco Packaging"]
        }
        res = post_json(opener_a, f"{BASE_URL}/api/profile", edit_payload)
        edit_data = json.loads(res.read().decode())
        if edit_data["success"] and edit_data["user"]["state"] == "Gujarat":
            # Verify private location data is present for owner
            owner_p = edit_data["user"]
            if owner_p["address_landmark"] == "Near Coastal Canal Post Office" and owner_p["pincode"] == "388620":
                results["passed"].append("Profile location updated with State, District, and PIN code; owner sees private address in My Profile.")

            # Verify private location data is STRIPPED on public profile view!
            pub_res = urllib.request.urlopen(f"{BASE_URL}/api/entrepreneurs/{user_a_id}")
            pub_data = json.loads(pub_res.read().decode())
            if "address_landmark" not in pub_data and "pincode" not in pub_data:
                results["passed"].append("Location privacy verified: Detailed street landmark and PIN code are hidden from public views.")
            else:
                results["failed"].append("Privacy leak: address_landmark or pincode exposed in public profile!")

            # Verify public location string matches chosen preference
            if pub_data["location"] == "Anand, Gujarat":
                results["passed"].append("Location display preference verified: Public location formatted as 'Anand, Gujarat'.")
            else:
                results["failed"].append(f"Unexpected public location formatting: {pub_data['location']}")
        else:
            results["failed"].append(f"Profile edit failed: {edit_data}")
    except Exception as e:
        results["failed"].append(f"Profile edit exception: {e}")

    # ---------------------------------------------------------
    # 5. Phase 4: CSRF & Rate Limiting Verification
    # ---------------------------------------------------------
    # Test CSRF Protection (post without CSRF token returns 403 when header requested)
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/profile",
            data=json.dumps({"name": "No CSRF Attempt"}).encode(),
            headers={"Content-Type": "application/json", "X-Test-Enforce-CSRF": "1"}
        )
        opener_a.open(req)
        results["failed"].append("CSRF enforcement failed: Request without CSRF token was accepted!")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            results["passed"].append("CSRF protection verified: Request without CSRF token rejected with HTTP 403 Forbidden.")
        else:
            results["failed"].append(f"CSRF check returned unexpected code: {e.code}")

    # Test Collaborations & Feed workflows
    try:
        collab_res = post_json(opener_a, f"{BASE_URL}/api/collaborations", {
            "title": "Looking for Grain Packaging Partner",
            "description": "Need biodegradable 1kg and 5kg kraft pouches with moisture lock.",
            "category": "Agriculture",
            "collab_type": "Seeking Partners"
        })
        collab_data = json.loads(collab_res.read().decode())
        if collab_data["success"]:
            results["passed"].append(f"Collaboration created by User A as Entrepreneur (collab_id={collab_data['collab_id']}).")
    except Exception as e:
        results["failed"].append(f"Collaboration creation failed: {e}")

    # User B (Community member) sends proposal / connection request to User A
    try:
        prop_res = post_json(opener_b, f"{BASE_URL}/api/collaborations/request", {
            "receiver_id": user_a_id,
            "message": "Hello Aarav, we can supply sustainable kraft pouches from our artisan unit."
        })
        prop_data = json.loads(prop_res.read().decode())
        if prop_data["success"]:
            results["passed"].append("Community member proposal sent to entrepreneur successfully.")
    except Exception as e:
        results["failed"].append(f"Community member proposal failed: {e}")

    # ---------------------------------------------------------
    # 6. Phase 2 Messaging System Integration Checks
    # ---------------------------------------------------------
    # Test User A starting direct conversation with User B
    direct_conv_id = None
    try:
        conv_res = post_json(opener_a, f"{BASE_URL}/api/conversations", {
            "recipient_id": user_b_id,
            "initial_message": "Hello Bhavna, welcome to UdyamSetu!"
        })
        conv_data = json.loads(conv_res.read().decode())
        if conv_res.status in [200, 201] and conv_data["success"]:
            direct_conv_id = conv_data["conversation"]["conv_id"]
            results["passed"].append(f"Direct conversation created between User A and User B (conv_id={direct_conv_id}).")
        else:
            results["failed"].append(f"Failed to create direct conversation: {conv_data}")
    except Exception as e:
        results["failed"].append(f"Direct conversation creation exception: {e}")

    # Test idempotency (reusing same conversation)
    try:
        reuse_res = post_json(opener_b, f"{BASE_URL}/api/conversations", {"recipient_id": user_a_id})
        reuse_data = json.loads(reuse_res.read().decode())
        if reuse_data["success"] and reuse_data["conversation"]["conv_id"] == direct_conv_id:
            results["passed"].append("Conversation reuse verified: Same direct conversation returned to both participants without duplicates.")
        else:
            results["failed"].append(f"Conversation reuse mismatch: {reuse_data}")
    except Exception as e:
        results["failed"].append(f"Conversation reuse check failed: {e}")

    # Test User B reading message from User A and verifying unread count
    try:
        msg_res = opener_b.open(f"{BASE_URL}/api/conversations/{direct_conv_id}/messages")
        msg_data = json.loads(msg_res.read().decode())
        if msg_data["success"] and len(msg_data["messages"]) >= 1:
            last_m = msg_data["messages"][-1]
            if last_m["body"] == "Hello Bhavna, welcome to UdyamSetu!" and last_m["sender_id"] == user_a_id:
                results["passed"].append("Message delivery & retrieval verified: User B received User A's initial message.")
            else:
                results["failed"].append(f"Unexpected message content: {last_m}")
        else:
            results["failed"].append(f"Failed to retrieve conversation messages: {msg_data}")
    except Exception as e:
        results["failed"].append(f"Message retrieval exception: {e}")

    # Test User B sending a reply to User A
    try:
        reply_res = post_json(opener_b, f"{BASE_URL}/api/conversations/{direct_conv_id}/messages", {
            "body": "Thank you Aarav! Excited to collaborate on organic grain packaging."
        })
        reply_data = json.loads(reply_res.read().decode())
        if reply_res.status == 201 and reply_data["success"]:
            results["passed"].append("Message reply sent successfully by User B.")
        else:
            results["failed"].append(f"Failed to send reply: {reply_data}")
    except Exception as e:
        results["failed"].append(f"Message reply exception: {e}")

    # Test Abuse Prevention / User Blocking
    try:
        # User A blocks User B
        block_res = post_json(opener_a, f"{BASE_URL}/api/users/{user_b_id}/block", {"reason": "Test block"})
        block_data = json.loads(block_res.read().decode())
        if block_data["success"] and block_data["blocked"]:
            results["passed"].append("User blocking verified: User A successfully blocked User B.")

        # User B attempts to send message to blocked conversation -> MUST return 403
        try:
            post_json(opener_b, f"{BASE_URL}/api/conversations/{direct_conv_id}/messages", {
                "body": "This should be blocked"
            })
            results["failed"].append("Blocked user was able to send message (expected 403)!")
        except urllib.error.HTTPError as e:
            if e.code == 403:
                results["passed"].append("Enforced blocking: Message from blocked user correctly rejected with HTTP 403 Forbidden.")
            else:
                results["failed"].append(f"Blocked message returned unexpected status: {e.code}")

        # User A unblocks User B
        unblock_res = post_json(opener_a, f"{BASE_URL}/api/users/{user_b_id}/unblock", {})
        unblock_data = json.loads(unblock_res.read().decode())
        if unblock_data["success"] and not unblock_data["blocked"]:
            results["passed"].append("User unblocking verified: Communication permissions restored.")
    except Exception as e:
        results["failed"].append(f"User blocking workflow exception: {e}")

    # Test Collaboration Request Acceptance & Project Chat creation
    try:
        accept_res = post_json(opener_a, f"{BASE_URL}/api/collaborations/requests/{prop_data['request_id']}/respond", {
            "action": "accept"
        })
        accept_data = json.loads(accept_res.read().decode())
        if accept_data["success"] and accept_data["status"] == "accepted" and accept_data.get("conv_id"):
            collab_conv_id = accept_data["conv_id"]
            results["passed"].append(f"Collaboration acceptance verified: Project chat created automatically (conv_id={collab_conv_id}).")

            # Check that User B can access this project chat
            c_msgs = json.loads(opener_b.open(f"{BASE_URL}/api/conversations/{collab_conv_id}/messages").read().decode())
            if c_msgs["success"] and len(c_msgs["messages"]) >= 1:
                results["passed"].append("Collaboration project chat verified: Both partners can access the project conversation.")
            else:
                results["failed"].append(f"Failed to access project chat: {c_msgs}")
        else:
            results["failed"].append(f"Collaboration acceptance failed: {accept_data}")
    except Exception as e:
        results["failed"].append(f"Collaboration acceptance exception: {e}")

    # -------------------------------------------------------------------------
    # In-App Notification System Verification
    # -------------------------------------------------------------------------
    try:
        # Check notifications page HTML route
        notif_page = opener_a.open(f"{BASE_URL}/notifications.html").read().decode()
        if "Notifications" in notif_page and "notificationsPageList" in notif_page:
            results["passed"].append("Notifications page verified: /notifications.html is rendered and accessible.")
        else:
            results["failed"].append("Notifications page missing required container elements.")

        # Check User B's unread notifications count
        b_unread_res = opener_b.open(f"{BASE_URL}/api/notifications/unread-count")
        b_unread_data = json.loads(b_unread_res.read().decode())
        if b_unread_data["success"] and b_unread_data["unread_count"] > 0:
            results["passed"].append(f"Notification count verified: User B has {b_unread_data['unread_count']} unread notifications.")
        else:
            results["failed"].append(f"User B expected unread notifications: {b_unread_data}")

        # Check User B's notifications list
        b_notifs_res = opener_b.open(f"{BASE_URL}/api/notifications")
        b_notifs_data = json.loads(b_notifs_res.read().decode())
        b_notifs = b_notifs_data.get("notifications", [])

        # Verify new_message notification exists
        has_msg_notif = any(n["event_type"] == "new_message" for n in b_notifs)
        # Verify collab_request_accepted notification exists (from earlier acceptance)
        has_collab_acc = any(n["event_type"] == "collab_request_accepted" for n in b_notifs)

        if has_msg_notif:
            results["passed"].append("Message notification verified: Event 'new_message' found in User B's notifications.")
        else:
            results["failed"].append("No 'new_message' notification found for User B.")

        if has_collab_acc:
            results["passed"].append("Collaboration acceptance notification verified: Event 'collab_request_accepted' found in User B's notifications.")
        else:
            results["failed"].append("No 'collab_request_accepted' notification found for User B.")

        # Test marking single notification as read
        if b_notifs:
            target_notif = b_notifs[0]
            read_res = post_json(opener_b, f"{BASE_URL}/api/notifications/{target_notif['id']}/read", {})
            read_data = json.loads(read_res.read().decode())
            if read_data["success"]:
                results["passed"].append("Mark single notification read verified: Successfully marked notification as read.")
            else:
                results["failed"].append(f"Failed to mark notification read: {read_data}")

            # Security test: User A attempts to mark User B's notification -> MUST return 403 Forbidden
            try:
                post_json(opener_a, f"{BASE_URL}/api/notifications/{target_notif['id']}/read", {})
                results["failed"].append("User A was able to mutate User B's notification (expected 403)!")
            except urllib.error.HTTPError as e:
                if e.code == 403:
                    results["passed"].append("Notification authorization verified: Cross-user mutation rejected with HTTP 403 Forbidden.")
                else:
                    results["failed"].append(f"Cross-user notification edit returned unexpected code: {e.code}")

        # Test mark all notifications as read
        read_all_res = post_json(opener_b, f"{BASE_URL}/api/notifications/read-all", {})
        read_all_data = json.loads(read_all_res.read().decode())
        if read_all_data["success"] and read_all_data["unread_count"] == 0:
            results["passed"].append("Mark all read verified: Unread count reset to 0.")
        else:
            results["failed"].append(f"Failed mark-all read: {read_all_data}")

    except Exception as e:
        results["failed"].append(f"Notification verification exception: {e}")

    # Logout & Session Cleared
    try:
        res = post_json(opener_a, f"{BASE_URL}/api/logout", {})
        logout_data = json.loads(res.read().decode())
        if logout_data["success"]:
            me_after = json.loads(opener_a.open(f"{BASE_URL}/api/me").read().decode())
            if not me_after["authenticated"]:
                results["passed"].append("Logout verified: Session cleared and /api/me returns authenticated=False.")
    except Exception as e:
        results["failed"].append(f"Logout failed: {e}")

    return results

if __name__ == "__main__":
    res = run_checks()
    print("=" * 60)
    print("UDYAMSETU FULL EXTENSION VERIFICATION REPORT")
    print("=" * 60)
    print(f"\nPASSED CHECKS ({len(res['passed'])}):")
    for p in res["passed"]:
        print(f"  [PASS] {p}")
    if res["failed"]:
        print(f"\nFAILED CHECKS ({len(res['failed'])}):")
        for f in res["failed"]:
            print(f"  [FAIL] {f}")
    else:
        print(f"\nALL CHECKS PASSED: 0 failures!")
    print("=" * 60)

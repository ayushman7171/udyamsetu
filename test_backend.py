import os
import unittest
import json
import datetime

# Ensure test suite runs in an isolated SQLite database file to preserve production udyamsetu.db
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_udyamsetu.db")
os.environ["UDYAMSETU_DB_PATH"] = TEST_DB_PATH

from app import app
from database import init_db, get_db

class ThriveHubBackendTestCase(unittest.TestCase):
    def setUp(self):
        # Reset database for tests
        init_db(reset=True)
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret-key-12345"
        self.client = app.test_client()

    def test_01_register_new_account(self):
        """1. Register a new account."""
        res = self.client.post("/api/register", json={
            "name": "Priya Sharma",
            "email": "priya@example.com",
            "password": "securepassword123",
            "business_name": "Priya Handicrafts",
            "category": "Handicrafts",
            "location": "Jaipur, Rajasthan"
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["name"], "Priya Sharma")
        self.assertEqual(data["user"]["category"], "Handicrafts")
        self.assertNotIn("password", data["user"])
        self.assertNotIn("password_hash", data["user"])

    def test_02_duplicate_email_registration(self):
        """2. Attempt to register the same email again."""
        # First registration
        self.client.post("/api/register", json={
            "name": "User One",
            "email": "duplicate@test.com",
            "password": "password123",
            "category": "Agriculture",
            "location": "Bihar"
        })
        # Second registration with same email
        res2 = self.client.post("/api/register", json={
            "name": "User Two",
            "email": "DUPLICATE@TEST.COM",  # case-insensitive check
            "password": "password456",
            "category": "Handicrafts",
            "location": "Punjab"
        })
        self.assertEqual(res2.status_code, 409)
        data = res2.get_json()
        self.assertFalse(data["success"])
        self.assertIn("already exists", data["error"])

    def test_03_login_valid_and_invalid(self):
        """3. Log in with valid and invalid credentials."""
        # Seeded user test
        res_valid = self.client.post("/api/login", json={
            "email": "asha@udyamsetu.in",
            "password": "password123"
        })
        self.assertEqual(res_valid.status_code, 200)
        data_valid = res_valid.get_json()
        self.assertTrue(data_valid["success"])
        self.assertEqual(data_valid["user"]["name"], "Asha Devi")

        # Invalid password
        res_invalid = self.client.post("/api/login", json={
            "email": "asha@udyamsetu.in",
            "password": "wrong_password"
        })
        self.assertEqual(res_invalid.status_code, 401)
        data_inv = res_invalid.get_json()
        self.assertFalse(data_inv["success"])

        # Nonexistent user
        res_none = self.client.post("/api/login", json={
            "email": "nobody@nowhere.com",
            "password": "password123"
        })
        self.assertEqual(res_none.status_code, 401)

    def test_04_session_persistence_and_api_me(self):
        """4 & 5. Navigate / refresh and verify session via /api/me."""
        # Unauthenticated first
        res_guest = self.client.get("/api/me")
        self.assertEqual(res_guest.status_code, 200)
        self.assertFalse(res_guest.get_json()["authenticated"])
        self.assertIsNone(res_guest.get_json()["user"])

        # Log in
        self.client.post("/api/login", json={
            "email": "meera@udyamsetu.in",
            "password": "password123"
        })

        # Subsequent request with session cookie
        res_logged = self.client.get("/api/me")
        self.assertEqual(res_logged.status_code, 200)
        data = res_logged.get_json()
        self.assertTrue(data["authenticated"])
        self.assertEqual(data["user"]["user_id"], "meera-patil")
        self.assertEqual(data["user"]["name"], "Meera Patil")

    def test_06_my_profile_data(self):
        """6. Open My Profile and verify the correct user's data."""
        self.client.post("/api/login", json={
            "email": "ramesh@udyamsetu.in",
            "password": "password123"
        })
        res = self.client.get("/api/profile")
        self.assertEqual(res.status_code, 200)
        profile = res.get_json()
        self.assertEqual(profile["user_id"], "ramesh-kumar")
        self.assertIn("Karnataka", profile["location"])
        self.assertEqual(profile["state"], "Karnataka")

    def test_07_edit_profile_persistence(self):
        """7. Edit the profile and confirm persistence."""
        self.client.post("/api/login", json={
            "email": "ramesh@udyamsetu.in",
            "password": "password123"
        })
        edit_res = self.client.post("/api/profile", json={
            "name": "Ramesh Kumar Gowda",
            "business_name": "Malnad GI Spices Collective",
            "category": "Organic Farming",
            "location": "Chikkamagaluru, Karnataka",
            "quote": "Growing high-grade organic cardamom and turmeric sustainably.",
            "description": "Updated enterprise description for nationwide spice delivery.",
            "full_story": "Our family tradition now supplies over 50 organic supermarkets.",
            "looking_for": ["Bulk Buyers", "Eco Pouches", "Cold Chain Logistics"],
            "website": "https://malnadspices.example.com",
            "phone": "+91 99001 22334"
        })
        self.assertEqual(edit_res.status_code, 200)
        updated = edit_res.get_json()["user"]
        self.assertEqual(updated["name"], "Ramesh Kumar Gowda")
        self.assertEqual(updated["business_name"], "Malnad GI Spices Collective")

        # Verify persistence from independent query
        get_res = self.client.get("/api/entrepreneurs/ramesh-kumar")
        self.assertEqual(get_res.status_code, 200)
        fetched = get_res.get_json()
        self.assertEqual(fetched["name"], "Ramesh Kumar Gowda")
        self.assertEqual(fetched["phone"], "+91 99001 22334")
        self.assertIn("Cold Chain Logistics", fetched["looking_for"])

    def test_08_logout_and_protection(self):
        """8. Log out and verify protected actions are inaccessible."""
        # Log in
        self.client.post("/api/login", json={
            "email": "asha@udyamsetu.in",
            "password": "password123"
        })
        # Log out
        logout_res = self.client.post("/api/logout")
        self.assertEqual(logout_res.status_code, 200)
        self.assertTrue(logout_res.get_json()["success"])

        # Check /api/me
        me_res = self.client.get("/api/me")
        self.assertFalse(me_res.get_json()["authenticated"])

        # Protected endpoints must reject with 401
        res_post = self.client.post("/api/feed", json={"content": "Should fail"})
        self.assertEqual(res_post.status_code, 401)

        res_profile = self.client.get("/api/profile")
        self.assertEqual(res_profile.status_code, 401)

        res_collab = self.client.post("/api/collaborations", json={"title": "Test", "description": "Fail", "category": "Food"})
        self.assertEqual(res_collab.status_code, 401)

    def test_09_two_separate_accounts_and_profiles(self):
        """9. Register a second account and confirm it has a separate profile."""
        c1 = app.test_client()
        c2 = app.test_client()

        res1 = c1.post("/api/register", json={
            "name": "Kavita Rao",
            "email": "kavita@test.com",
            "password": "password123",
            "business_name": "Kavita Silks",
            "category": "Textiles & Handlooms",
            "location": "Varanasi"
        })
        self.assertEqual(res1.status_code, 201)
        uid1 = res1.get_json()["user"]["user_id"]

        res2 = c2.post("/api/register", json={
            "name": "Rajesh Singh",
            "email": "rajesh@test.com",
            "password": "password123",
            "business_name": "Rajesh Agro Tools",
            "category": "Agriculture",
            "location": "Nashik"
        })
        self.assertEqual(res2.status_code, 201)
        uid2 = res2.get_json()["user"]["user_id"]

        self.assertNotEqual(uid1, uid2)

        # Profile 1 check
        p1 = c1.get("/api/profile").get_json()
        self.assertEqual(p1["name"], "Kavita Rao")
        self.assertEqual(p1["business_name"], "Kavita Silks")

        # Profile 2 check
        p2 = c2.get("/api/profile").get_json()
        self.assertEqual(p2["name"], "Rajesh Singh")
        self.assertEqual(p2["business_name"], "Rajesh Agro Tools")

    def test_10_collaboration_request_authorization(self):
        """10. Send a collaboration request between two accounts and verify that only the intended recipient can accept it."""
        client_sender = app.test_client()
        client_receiver = app.test_client()
        client_intruder = app.test_client()

        # Sender registers
        s_res = client_sender.post("/api/register", json={
            "name": "Sunita Devi",
            "email": "sunita@dev.in",
            "password": "password123",
            "category": "Handicrafts",
            "location": "Odisha"
        })
        sender_id = s_res.get_json()["user"]["user_id"]

        # Receiver registers
        r_res = client_receiver.post("/api/register", json={
            "name": "Harish Patel",
            "email": "harish@dev.in",
            "password": "password123",
            "category": "Food Products",
            "location": "Gujarat"
        })
        receiver_id = r_res.get_json()["user"]["user_id"]

        # Intruder registers
        client_intruder.post("/api/register", json={
            "name": "Intruder User",
            "email": "intruder@dev.in",
            "password": "password123",
            "category": "Digital Services",
            "location": "Delhi"
        })

        # Sender sends collaboration request to Receiver
        req_res = client_sender.post("/api/collaborations/request", json={
            "receiver_id": receiver_id,
            "message": "Let's partner on eco-friendly packaging for handicrafts!"
        })
        self.assertEqual(req_res.status_code, 200)
        req_id = req_res.get_json()["request_id"]
        self.assertTrue(req_id > 0)

        # Receiver can see the request in their received list
        recv_res = client_receiver.get("/api/collaborations/requests")
        self.assertEqual(recv_res.status_code, 200)
        received_list = recv_res.get_json()["received"]
        self.assertEqual(len(received_list), 1)
        self.assertEqual(received_list[0]["sender_name"], "Sunita Devi")

        # Intruder attempts to accept Receiver's request -> MUST BE FORBIDDEN (403)
        intrude_res = client_intruder.post(f"/api/collaborations/requests/{req_id}/respond", json={
            "action": "accept"
        })
        self.assertEqual(intrude_res.status_code, 403)
        self.assertFalse(intrude_res.get_json()["success"])

        # Intended Receiver accepts the request -> SUCCESS (200)
        accept_res = client_receiver.post(f"/api/collaborations/requests/{req_id}/respond", json={
            "action": "accept"
        })
        self.assertEqual(accept_res.status_code, 200)
        self.assertEqual(accept_res.get_json()["status"], "accepted")

        # Verify a collaborative project is now created for both partners
        proj_res = client_receiver.get("/api/collaborations/projects")
        self.assertEqual(proj_res.status_code, 200)
        projects = proj_res.get_json()
        self.assertTrue(len(projects) >= 1)
        self.assertTrue(any(
            (p["partner1_id"] == sender_id and p["partner2_id"] == receiver_id) or
            (p["partner1_id"] == receiver_id and p["partner2_id"] == sender_id)
            for p in projects
        ))

    def test_11_account_types_and_registration_redirect(self):
        """11. Verify entrepreneur vs community_member account types and redirection targets."""
        # 1. Entrepreneur registration
        res_ent = self.client.post("/api/register", json={
            "name": "Devendra Patil",
            "email": "devendra@test.in",
            "password": "strongPassword123",
            "confirm_password": "strongPassword123",
            "account_type": "entrepreneur"
        })
        self.assertEqual(res_ent.status_code, 201)
        data_ent = res_ent.get_json()
        self.assertEqual(data_ent["account_type"], "entrepreneur")
        self.assertEqual(data_ent["next_page"], "/profile-setup.html")

        # 2. Community member registration
        res_comm = self.client.post("/api/register", json={
            "name": "Sneha Joshi",
            "email": "sneha@test.in",
            "password": "strongPassword123",
            "confirm_password": "strongPassword123",
            "account_type": "community_member"
        })
        self.assertEqual(res_comm.status_code, 201)
        data_comm = res_comm.get_json()
        self.assertEqual(data_comm["account_type"], "community_member")
        self.assertEqual(data_comm["next_page"], "/dashboard.html")

    def test_12_profile_clean_initialization_no_fabrication(self):
        """12. Ensure newly registered accounts have no fabricated descriptions, quotes, or products."""
        res = self.client.post("/api/register", json={
            "name": "Clean Slate User",
            "email": "clean@test.in",
            "password": "cleanPassword123",
            "account_type": "entrepreneur"
        })
        self.assertEqual(res.status_code, 201)
        user = res.get_json()["user"]
        
        # Verify no fabricated data
        self.assertEqual(user["quote"], "")
        self.assertEqual(user["description"], "")
        self.assertEqual(user["full_story"], "")
        self.assertEqual(user["looking_for"], [])
        self.assertEqual(user["skills"], [])
        self.assertEqual(user["business_name"], "")

        # Verify no products fabricated
        prod_res = self.client.get("/api/profile")
        self.assertEqual(prod_res.status_code, 200)
        self.assertEqual(len(prod_res.get_json()["products"]), 0)

        # Confirm seed account still retains rich authentic data
        seed_res = self.client.get("/api/entrepreneurs/asha-devi")
        self.assertEqual(seed_res.status_code, 200)
        asha = seed_res.get_json()
        self.assertTrue(len(asha["full_story"]) > 20)
        self.assertTrue(len(asha["products"]) > 0)

    def test_13_role_restrictions_community_vs_entrepreneur(self):
        """13. Enforce that community members cannot publish collaborations or showcase products."""
        # Community member
        c_comm = app.test_client()
        c_comm.post("/api/register", json={
            "name": "Community Observer",
            "email": "observer@test.in",
            "password": "password12345",
            "account_type": "community_member"
        })

        # Entrepreneur
        c_ent = app.test_client()
        c_ent.post("/api/register", json={
            "name": "Active Founder",
            "email": "founder@test.in",
            "password": "password12345",
            "account_type": "entrepreneur"
        })

        # Community member attempts to publish collaboration -> 403 Forbidden
        collab_fail = c_comm.post("/api/collaborations", json={
            "title": "Unauthorized Collab",
            "description": "Should fail",
            "category": "Handicrafts"
        })
        self.assertEqual(collab_fail.status_code, 403)
        self.assertFalse(collab_fail.get_json()["success"])

        # Entrepreneur publishes collaboration -> 201 Created
        collab_ok = c_ent.post("/api/collaborations", json={
            "title": "Need Bamboo Weaving Partner",
            "description": "We are seeking skilled bamboo basket weavers in Assam.",
            "category": "Handicrafts"
        })
        self.assertEqual(collab_ok.status_code, 201)
        self.assertTrue(collab_ok.get_json()["success"])

        # Community member attempts to add product -> 403 Forbidden
        prod_fail = c_comm.post("/api/profile/products", json={
            "name": "Fake Craft",
            "price": "500"
        })
        self.assertEqual(prod_fail.status_code, 403)
        self.assertFalse(prod_fail.get_json()["success"])

        # Entrepreneur adds product -> 201 Created
        prod_ok = c_ent.post("/api/profile/products", json={
            "name": "Handmade Clay Water Bottle",
            "price": "350"
        })
        self.assertEqual(prod_ok.status_code, 201)
        self.assertTrue(prod_ok.get_json()["success"])

        # Community member CAN participate in discussions
        disc_comm = c_comm.post("/api/discussions", json={
            "title": "Where can we find organic jaggery in bulk?",
            "body": "Looking for recommendations from local farmers.",
            "tag": "Question"
        })
        self.assertEqual(disc_comm.status_code, 201)

    def test_14_location_dataset_and_validation(self):
        """14. Validate Indian states, districts, and 6-digit PIN codes on the server."""
        c = app.test_client()
        c.post("/api/register", json={
            "name": "Location Tester",
            "email": "loc@test.in",
            "password": "password12345",
            "account_type": "entrepreneur"
        })

        # 1. Invalid State
        inv_state = c.post("/api/profile", json={
            "state": "NonExistentState",
            "district": "Pune"
        })
        self.assertEqual(inv_state.status_code, 400)
        self.assertIn("not a recognized state", inv_state.get_json()["error"])

        # 2. Valid State, Invalid District for that state
        inv_dist = c.post("/api/profile", json={
            "state": "Maharashtra",
            "district": "Varanasi"  # Varanasi is in UP, not MH
        })
        self.assertEqual(inv_dist.status_code, 400)
        self.assertIn("not recognized in Maharashtra", inv_dist.get_json()["error"])

        # 3. Invalid PIN codes
        for bad_pin in ["12345", "1234567", "012345", "PIN123"]:
            inv_pin = c.post("/api/profile", json={
                "pincode": bad_pin
            })
            self.assertEqual(inv_pin.status_code, 400)
            self.assertIn("valid 6-digit", inv_pin.get_json()["error"])

        # 4. Valid State, District, and PIN Code
        valid_loc = c.post("/api/profile", json={
            "state": "Maharashtra",
            "district": "Satara",
            "subdistrict_or_town": "Wai",
            "pincode": "412803",
            "address_landmark": "Near Krishna River Ghat",
            "location_display_preference": "district_state"
        })
        self.assertEqual(valid_loc.status_code, 200)
        user_loc = valid_loc.get_json()["user"]
        self.assertEqual(user_loc["state"], "Maharashtra")
        self.assertEqual(user_loc["district"], "Satara")
        self.assertEqual(user_loc["pincode"], "412803")
        self.assertEqual(user_loc["location"], "Satara, Maharashtra")

    def test_15_location_privacy_and_preferences(self):
        """15. Ensure private addresses and pincodes are never leaked in public profiles."""
        c_owner = app.test_client()
        reg_res = c_owner.post("/api/register", json={
            "name": "Private Artisan",
            "email": "artisan@privacy.in",
            "password": "password12345",
            "account_type": "entrepreneur"
        })
        uid = reg_res.get_json()["user"]["user_id"]

        c_owner.post("/api/profile", json={
            "state": "Rajasthan",
            "district": "Jaipur",
            "subdistrict_or_town": "Amer",
            "pincode": "302028",
            "address_landmark": "House 45, Private Lane, Old Amber",
            "location_display_preference": "district_state"
        })

        # Owner gets their own private address details in My Profile
        owner_view = c_owner.get("/api/profile").get_json()
        self.assertEqual(owner_view["address_landmark"], "House 45, Private Lane, Old Amber")
        self.assertEqual(owner_view["pincode"], "302028")

        # Anonymous visitor or other user views public profile -> private details stripped!
        anon_client = app.test_client()
        public_view = anon_client.get(f"/api/entrepreneurs/{uid}").get_json()
        self.assertNotIn("address_landmark", public_view)
        self.assertNotIn("pincode", public_view)
        self.assertEqual(public_view["location"], "Jaipur, Rajasthan")

        # Verify village display preference
        c_owner.post("/api/profile", json={
            "location_display_preference": "village_district_state"
        })
        public_view2 = anon_client.get(f"/api/entrepreneurs/{uid}").get_json()
        self.assertEqual(public_view2["location"], "Amer, Jaipur, Rajasthan")

    def test_16_directory_location_filtering(self):
        """16. Test location-based entrepreneur filtering via state parameter."""
        res_mh = self.client.get("/api/entrepreneurs?state=Maharashtra")
        self.assertEqual(res_mh.status_code, 200)
        items_mh = res_mh.get_json()
        self.assertTrue(len(items_mh) >= 1)
        for item in items_mh:
            self.assertIn("Maharashtra", item["location"])

        res_rj = self.client.get("/api/entrepreneurs?state=Rajasthan")
        self.assertEqual(res_rj.status_code, 200)
        items_rj = res_rj.get_json()
        self.assertTrue(len(items_rj) >= 1)
        for item in items_rj:
            self.assertIn("Rajasthan", item["location"])

    def test_17_password_security_and_confirm_validation(self):
        """17. Reject weak passwords and confirmation mismatches."""
        # Too short (< 8 chars)
        short_res = self.client.post("/api/register", json={
            "name": "Weak Pass User",
            "email": "weak@test.in",
            "password": "short"
        })
        self.assertEqual(short_res.status_code, 400)
        self.assertIn("at least 8 characters", short_res.get_json()["error"])

        # Confirm password mismatch
        mismatch_res = self.client.post("/api/register", json={
            "name": "Mismatch User",
            "email": "mismatch@test.in",
            "password": "password123",
            "confirm_password": "password456"
        })
        self.assertEqual(mismatch_res.status_code, 400)
        self.assertIn("do not match", mismatch_res.get_json()["error"])

    def test_18_csrf_protection_and_rate_limiting(self):
        """18. Test CSRF enforcement on state-changing requests and rate limiting."""
        from auth import clear_rate_limits
        clear_rate_limits()

        c = app.test_client()
        c.post("/api/register", json={
            "name": "Security Tester",
            "email": "sec@test.in",
            "password": "password12345",
            "account_type": "entrepreneur"
        })

        # When CSRF is enforced and token is missing -> 403 Forbidden
        csrf_fail = c.post("/api/profile", json={"name": "Hacked"}, headers={"X-Test-Enforce-CSRF": "1"})
        self.assertEqual(csrf_fail.status_code, 403)
        self.assertIn("CSRF validation failed", csrf_fail.get_json()["error"])

        # Fetch valid CSRF token and pass it -> 200 Success
        csrf_token_res = c.get("/api/csrf-token")
        token = csrf_token_res.get_json()["csrf_token"]
        csrf_ok = c.post(
            "/api/profile",
            json={"name": "Protected Name"},
            headers={"X-Test-Enforce-CSRF": "1", "X-CSRF-Token": token}
        )
        self.assertEqual(csrf_ok.status_code, 200)

        # Test rate limiting with X-Test-Rate-Limit header
        # Rate limit on login is 10 requests. After 10 rapid calls, the 11th must return 429.
        clear_rate_limits()
        for i in range(10):
            res = c.post("/api/login", json={"email": "nobody@test.in", "password": "pass"}, headers={"X-Test-Rate-Limit": "1"})
            self.assertEqual(res.status_code, 401)
        
        # 11th attempt hits rate limit
        res_blocked = c.post("/api/login", json={"email": "nobody@test.in", "password": "pass"}, headers={"X-Test-Rate-Limit": "1"})
        self.assertEqual(res_blocked.status_code, 429)
        self.assertIn("Too many requests", res_blocked.get_json()["error"])

    def test_19_direct_conversation_creation_and_reuse(self):
        """19. Create direct conversation, test idempotency/reuse, and reject unauthenticated requests."""
        # Unauthenticated request to GET /api/conversations -> 401
        anon_client = app.test_client()
        res_unauth = anon_client.get("/api/conversations")
        self.assertEqual(res_unauth.status_code, 401)

        res_unauth_post = anon_client.post("/api/conversations", json={"recipient_id": "ramesh-kumar"})
        self.assertEqual(res_unauth_post.status_code, 401)

        # Authenticate as Asha Devi
        c_asha = app.test_client()
        c_asha.post("/api/login", json={"email": "asha@udyamsetu.in", "password": "password123"})

        # Cannot start conversation with self
        self_res = c_asha.post("/api/conversations", json={"recipient_id": "asha-devi"})
        self.assertEqual(self_res.status_code, 400)
        self.assertIn("cannot start a conversation with yourself", self_res.get_json()["error"])

        # Create/retrieve conversation with Ramesh Kumar
        res_create = c_asha.post("/api/conversations", json={
            "recipient_id": "ramesh-kumar",
            "initial_message": "Hello from automated test!"
        })
        self.assertIn(res_create.status_code, [200, 201])
        data_create = res_create.get_json()
        self.assertTrue(data_create["success"])
        conv_id_1 = data_create["conversation"]["conv_id"]

        # Call again with Ramesh Kumar -> MUST reuse same conversation (idempotent, no duplicates)
        res_reuse = c_asha.post("/api/conversations", json={"recipient_id": "ramesh-kumar"})
        self.assertEqual(res_reuse.status_code, 200)
        data_reuse = res_reuse.get_json()
        self.assertFalse(data_reuse["is_new"])
        self.assertEqual(data_reuse["conversation"]["conv_id"], conv_id_1)

        # Confirm from Ramesh's side that the same conversation is returned
        c_ramesh = app.test_client()
        c_ramesh.post("/api/login", json={"email": "ramesh@udyamsetu.in", "password": "password123"})
        res_ramesh_side = c_ramesh.post("/api/conversations", json={"recipient_id": "asha-devi"})
        self.assertEqual(res_ramesh_side.status_code, 200)
        self.assertEqual(res_ramesh_side.get_json()["conversation"]["conv_id"], conv_id_1)

    def test_20_send_and_retrieve_messages_chronological(self):
        """20. Send messages, verify chronological order, and verify read receipts."""
        c_asha = app.test_client()
        c_asha.post("/api/login", json={"email": "asha@udyamsetu.in", "password": "password123"})

        c_ramesh = app.test_client()
        c_ramesh.post("/api/login", json={"email": "ramesh@udyamsetu.in", "password": "password123"})

        # Get conversation
        res_conv = c_asha.post("/api/conversations", json={"recipient_id": "ramesh-kumar"})
        conv_id = res_conv.get_json()["conversation"]["conv_id"]

        # Asha sends message 1
        msg1_text = f"Test message alpha {datetime.datetime.now().isoformat()}"
        res_m1 = c_asha.post(f"/api/conversations/{conv_id}/messages", json={"body": msg1_text})
        self.assertEqual(res_m1.status_code, 201)
        m1_data = res_m1.get_json()["message"]
        self.assertEqual(m1_data["sender_id"], "asha-devi")
        self.assertEqual(m1_data["body"], msg1_text)

        # Ramesh sends message 2
        msg2_text = f"Test message beta {datetime.datetime.now().isoformat()}"
        res_m2 = c_ramesh.post(f"/api/conversations/{conv_id}/messages", json={"body": msg2_text})
        self.assertEqual(res_m2.status_code, 201)
        m2_data = res_m2.get_json()["message"]
        self.assertEqual(m2_data["sender_id"], "ramesh-kumar")

        # Ramesh retrieves messages -> verify both messages appear in chronological order
        res_get = c_ramesh.get(f"/api/conversations/{conv_id}/messages")
        self.assertEqual(res_get.status_code, 200)
        msgs = res_get.get_json()["messages"]
        self.assertTrue(len(msgs) >= 2)
        idx1 = next(i for i, m in enumerate(msgs) if m["msg_id"] == m1_data["msg_id"])
        idx2 = next(i for i, m in enumerate(msgs) if m["msg_id"] == m2_data["msg_id"])
        self.assertTrue(idx1 < idx2, "Messages must be in chronological ascending order")

        # Mark as read
        res_read = c_ramesh.post(f"/api/conversations/{conv_id}/read")
        self.assertEqual(res_read.status_code, 200)
        self.assertEqual(res_read.get_json()["unread_count"], 0)

    def test_21_non_participant_authorization_and_spoof_prevention(self):
        """21. Ensure non-participants cannot read/send messages and sender ID spoofing is rejected."""
        c_asha = app.test_client()
        c_asha.post("/api/login", json={"email": "asha@udyamsetu.in", "password": "password123"})

        # Conversation between Asha Devi and Ramesh Kumar
        conv_res = c_asha.post("/api/conversations", json={"recipient_id": "ramesh-kumar"})
        conv_id = conv_res.get_json()["conversation"]["conv_id"]

        # Ananya Sharma (third party user) attempts to access conversation
        c_ananya = app.test_client()
        c_ananya.post("/api/login", json={"email": "ananya@udyamsetu.in", "password": "password123"})

        # Reading messages should be 403 Forbidden
        read_attempt = c_ananya.get(f"/api/conversations/{conv_id}/messages")
        self.assertEqual(read_attempt.status_code, 403)
        self.assertIn("access denied", read_attempt.get_json()["error"])

        # Sending message should be 403 Forbidden
        send_attempt = c_ananya.post(f"/api/conversations/{conv_id}/messages", json={"body": "Intruder message"})
        self.assertEqual(send_attempt.status_code, 403)
        self.assertIn("Unauthorized", send_attempt.get_json()["error"])

        # Sender ID spoofing prevention:
        # Asha tries to send a message claiming sender_id is "admin-spoof" or "ramesh-kumar"
        spoof_res = c_asha.post(f"/api/conversations/{conv_id}/messages", json={
            "body": "Spoof test message",
            "sender_id": "ramesh-kumar"
        })
        self.assertEqual(spoof_res.status_code, 201)
        # Server MUST ignore request field and bind to session user 'asha-devi'
        self.assertEqual(spoof_res.get_json()["message"]["sender_id"], "asha-devi")

    def test_22_message_validation_and_rate_limits(self):
        """22. Reject empty messages, excessive lengths (>2000 chars), and enforce rate limits."""
        c_asha = app.test_client()
        c_asha.post("/api/login", json={"email": "asha@udyamsetu.in", "password": "password123"})
        conv_res = c_asha.post("/api/conversations", json={"recipient_id": "ramesh-kumar"})
        conv_id = conv_res.get_json()["conversation"]["conv_id"]

        # Empty body
        res_empty = c_asha.post(f"/api/conversations/{conv_id}/messages", json={"body": "   "})
        self.assertEqual(res_empty.status_code, 400)
        self.assertIn("cannot be empty", res_empty.get_json()["error"])

        # Over 2000 characters
        res_long = c_asha.post(f"/api/conversations/{conv_id}/messages", json={"body": "X" * 2005})
        self.assertEqual(res_long.status_code, 400)
        self.assertIn("exceeds 2000 characters", res_long.get_json()["error"])

        # Rate limit test with X-Test-Rate-Limit header (rate limit is 40 per minute)
        from auth import clear_rate_limits
        clear_rate_limits()

        for _ in range(40):
            r = c_asha.post(
                f"/api/conversations/{conv_id}/messages",
                json={"body": "Rapid message"},
                headers={"X-Test-Rate-Limit": "1"}
            )
            self.assertEqual(r.status_code, 201)

        # 41st message hits rate limit
        res_rate_blocked = c_asha.post(
            f"/api/conversations/{conv_id}/messages",
            json={"body": "41st message"},
            headers={"X-Test-Rate-Limit": "1"}
        )
        self.assertEqual(res_rate_blocked.status_code, 429)
        self.assertIn("Too many requests", res_rate_blocked.get_json()["error"])

    def test_23_collaboration_conversation_lifecycle_and_idempotency(self):
        """23. Collaboration request acceptance creates project chat; repeated acceptance is idempotent."""
        c_meera = app.test_client()
        c_meera.post("/api/login", json={"email": "meera@udyamsetu.in", "password": "password123"})

        c_rahul = app.test_client()
        c_rahul.post("/api/login", json={"email": "rahul@udyamsetu.in", "password": "password123"})

        # Rahul proposes collaboration to Meera
        prop_res = c_rahul.post("/api/collaborations/request", json={
            "receiver_id": "meera-patil",
            "message": "Let us partner on packaging design for dry snacks."
        })
        self.assertEqual(prop_res.status_code, 200)
        req_id = prop_res.get_json()["request_id"]

        # Meera accepts collaboration
        accept_res = c_meera.post(f"/api/collaborations/requests/{req_id}/respond", json={"action": "accept"})
        self.assertEqual(accept_res.status_code, 200)
        acc_data = accept_res.get_json()
        self.assertTrue(acc_data["success"])
        project_id = acc_data["project_id"]
        collab_conv_id = acc_data["conv_id"]
        self.assertIsNotNone(collab_conv_id)

        # Repeated accept action MUST NOT create duplicate project or conversation
        repeat_res = c_meera.post(f"/api/collaborations/requests/{req_id}/respond", json={"action": "accept"})
        self.assertEqual(repeat_res.status_code, 200)
        self.assertEqual(repeat_res.get_json()["project_id"], project_id)
        self.assertEqual(repeat_res.get_json()["conv_id"], collab_conv_id)

        # Check conversation list for both partners
        meera_convs = c_meera.get("/api/conversations?type=collaboration").get_json()["conversations"]
        self.assertTrue(any(c["conv_id"] == collab_conv_id for c in meera_convs))

        rahul_convs = c_rahul.get("/api/conversations?type=collaboration").get_json()["conversations"]
        self.assertTrue(any(c["conv_id"] == collab_conv_id for c in rahul_convs))

        # Third party user (Suresh Yadav) cannot access collaboration conversation
        c_suresh = app.test_client()
        c_suresh.post("/api/login", json={"email": "suresh@udyamsetu.in", "password": "password123"})
        suresh_read = c_suresh.get(f"/api/conversations/{collab_conv_id}/messages")
        self.assertEqual(suresh_read.status_code, 403)

    def test_24_user_blocking_and_abuse_prevention(self):
        """24. Blocked users cannot message each other; unblocking restores communication."""
        c_asha = app.test_client()
        c_asha.post("/api/login", json={"email": "asha@udyamsetu.in", "password": "password123"})

        c_suresh = app.test_client()
        c_suresh.post("/api/login", json={"email": "suresh@udyamsetu.in", "password": "password123"})

        # Asha blocks Suresh
        block_res = c_asha.post("/api/users/suresh-yadav/block", json={"reason": "Spam inquiry"})
        self.assertEqual(block_res.status_code, 200)
        self.assertTrue(block_res.get_json()["blocked"])

        # Check block status
        status_res = c_asha.get("/api/users/suresh-yadav/block-status")
        self.assertTrue(status_res.get_json()["blocked_by_me"])
        self.assertTrue(status_res.get_json()["is_blocked"])

        # Suresh attempts to start conversation with Asha -> 403 Forbidden
        conv_attempt = c_suresh.post("/api/conversations", json={"recipient_id": "asha-devi"})
        self.assertEqual(conv_attempt.status_code, 403)
        self.assertIn("blocked", conv_attempt.get_json()["error"])

        # Asha unblocks Suresh
        unblock_res = c_asha.post("/api/users/suresh-yadav/unblock")
        self.assertEqual(unblock_res.status_code, 200)
        self.assertFalse(unblock_res.get_json()["blocked"])

        # Now conversation can be created
        conv_ok = c_suresh.post("/api/conversations", json={"recipient_id": "asha-devi"})
        self.assertIn(conv_ok.status_code, [200, 201])
        self.assertTrue(conv_ok.get_json()["success"])

    def test_25_notification_lifecycle_and_unread_counts(self):
        """25. Sending messages creates notifications; unread counts update and marking as read persists."""
        c_asha = app.test_client()
        c_asha.post("/api/login", json={"email": "asha@udyamsetu.in", "password": "password123"})

        c_ramesh = app.test_client()
        c_ramesh.post("/api/login", json={"email": "ramesh@udyamsetu.in", "password": "password123"})

        # Get initial unread notification count for Ramesh
        initial_unread = c_ramesh.get("/api/notifications/unread-count").get_json()["unread_count"]

        # Asha sends message to Ramesh
        conv_res = c_asha.post("/api/conversations", json={"recipient_id": "ramesh-kumar"})
        conv_id = conv_res.get_json()["conversation"]["conv_id"]

        send_res = c_asha.post(f"/api/conversations/{conv_id}/messages", json={
            "body": "Namaste Ramesh ji, could we coordinate delivery dates?"
        })
        self.assertEqual(send_res.status_code, 201)

        # Ramesh's unread count must increase by 1
        new_unread_res = c_ramesh.get("/api/notifications/unread-count")
        self.assertEqual(new_unread_res.status_code, 200)
        self.assertEqual(new_unread_res.get_json()["unread_count"], initial_unread + 1)

        # Ramesh retrieves his notifications list
        notifs_res = c_ramesh.get("/api/notifications?unread=1")
        self.assertEqual(notifs_res.status_code, 200)
        notifs_data = notifs_res.get_json()
        self.assertTrue(notifs_data["success"])
        notifs = notifs_data["notifications"]

        msg_notif = next((n for n in notifs if n["event_type"] == "new_message" and "coordinate delivery" in n["message"]), None)
        self.assertIsNotNone(msg_notif)
        self.assertEqual(msg_notif["recipient_id"], "ramesh-kumar")
        self.assertEqual(msg_notif["actor_id"], "asha-devi")
        self.assertIn("Asha Devi", msg_notif["title"])
        self.assertIn("messages.html?conversation=", msg_notif["link_url"])
        self.assertEqual(msg_notif["is_read"], 0)

        # Ramesh marks this single notification as read
        mark_res = c_ramesh.post(f"/api/notifications/{msg_notif['id']}/read")
        self.assertEqual(mark_res.status_code, 200)
        self.assertEqual(mark_res.get_json()["unread_count"], initial_unread)

        # Mark all notifications as read
        read_all_res = c_ramesh.post("/api/notifications/read-all")
        self.assertEqual(read_all_res.status_code, 200)
        self.assertEqual(read_all_res.get_json()["unread_count"], 0)

        # Unread count check
        final_unread = c_ramesh.get("/api/notifications/unread-count").get_json()["unread_count"]
        self.assertEqual(final_unread, 0)

    def test_26_collaboration_notifications_and_duplicate_prevention(self):
        """26. Collaboration proposals and acceptance/rejection trigger notifications without duplicates."""
        c_meera = app.test_client()
        c_meera.post("/api/login", json={"email": "meera@udyamsetu.in", "password": "password123"})

        c_rahul = app.test_client()
        c_rahul.post("/api/login", json={"email": "rahul@udyamsetu.in", "password": "password123"})

        # Meera proposes collaboration to Rahul
        prop_res = c_meera.post("/api/collaborations/request", json={
            "receiver_id": "rahul-sharma",
            "message": "Let us partner on regional distribution for agro-processing."
        })
        self.assertEqual(prop_res.status_code, 200)
        req_id = prop_res.get_json()["request_id"]

        # Rahul should have received a notification
        rahul_notifs = c_rahul.get("/api/notifications?unread=1").get_json()["notifications"]
        req_notif = next((n for n in rahul_notifs if n["event_type"] == "collab_request_received" and str(req_id) == str(n["reference_id"])), None)
        self.assertIsNotNone(req_notif)
        self.assertEqual(req_notif["actor_id"], "meera-patil")
        self.assertIn("regional distribution", req_notif["message"])

        # Rahul accepts the collaboration request
        accept_res = c_rahul.post(f"/api/collaborations/requests/{req_id}/respond", json={"action": "accept"})
        self.assertEqual(accept_res.status_code, 200)

        # Meera should have received a notification for acceptance
        meera_notifs = c_meera.get("/api/notifications?unread=1").get_json()["notifications"]
        acc_notif = next((n for n in meera_notifs if n["event_type"] == "collab_request_accepted"), None)
        self.assertIsNotNone(acc_notif)
        self.assertEqual(acc_notif["actor_id"], "rahul-sharma")
        self.assertIn("accepted", acc_notif["title"].lower())

        # If Rahul repeatedly accepts the request, duplicate notifications MUST NOT be created
        c_rahul.post(f"/api/collaborations/requests/{req_id}/respond", json={"action": "accept"})
        meera_all = c_meera.get("/api/notifications").get_json()["notifications"]
        acc_matches = [n for n in meera_all if n["event_type"] == "collab_request_accepted" and str(n["reference_id"]) == str(req_id)]
        self.assertEqual(len(acc_matches), 1, "Duplicate collaboration accepted notification was created!")

        # Rahul proposes to Meera and Meera rejects
        prop2_res = c_rahul.post("/api/collaborations/request", json={
            "receiver_id": "meera-patil",
            "message": "Secondary partnership proposal."
        })
        req2_id = prop2_res.get_json()["request_id"]

        reject_res = c_meera.post(f"/api/collaborations/requests/{req2_id}/respond", json={"action": "reject"})
        self.assertEqual(reject_res.status_code, 200)

        # Rahul should receive collab_request_rejected notification
        rahul_all = c_rahul.get("/api/notifications").get_json()["notifications"]
        rej_notif = next((n for n in rahul_all if n["event_type"] == "collab_request_rejected" and str(n["reference_id"]) == str(req2_id)), None)
        self.assertIsNotNone(rej_notif)
        self.assertIn("declined", rej_notif["message"].lower())

    def test_27_notification_security_and_authorization(self):
        """27. Notifications are strictly private; users cannot view or mutate each other's notifications."""
        # Unauthenticated access rejected with 401
        guest_client = app.test_client()
        res_guest = guest_client.get("/api/notifications")
        self.assertEqual(res_guest.status_code, 401)

        res_guest_count = guest_client.get("/api/notifications/unread-count")
        self.assertEqual(res_guest_count.status_code, 401)

        c_asha = app.test_client()
        c_asha.post("/api/login", json={"email": "asha@udyamsetu.in", "password": "password123"})

        c_ramesh = app.test_client()
        c_ramesh.post("/api/login", json={"email": "ramesh@udyamsetu.in", "password": "password123"})

        # Get a notification that belongs to Ramesh
        ramesh_notifs = c_ramesh.get("/api/notifications").get_json()["notifications"]
        self.assertTrue(len(ramesh_notifs) > 0)
        ramesh_notif_id = ramesh_notifs[0]["id"]

        # Asha tries to mark Ramesh's notification as read -> 403 Forbidden
        tamper_res = c_asha.post(f"/api/notifications/{ramesh_notif_id}/read")
        self.assertEqual(tamper_res.status_code, 403)
        self.assertIn("Unauthorized", tamper_res.get_json()["error"])

        # Asha tries to delete Ramesh's notification -> 403 Forbidden
        del_tamper = c_asha.delete(f"/api/notifications/{ramesh_notif_id}")
        self.assertEqual(del_tamper.status_code, 403)

        # Verify Asha's own notification list does not contain any of Ramesh's notifications
        asha_notifs = c_asha.get("/api/notifications").get_json()["notifications"]
        self.assertTrue(all(n["recipient_id"] == "asha-devi" for n in asha_notifs))

    def test_28_discussion_comment_and_connection_notifications(self):
        """28. Discussion comments and profile connections create notifications for recipients."""
        c_asha = app.test_client()
        c_asha.post("/api/login", json={"email": "asha@udyamsetu.in", "password": "password123"})

        c_ramesh = app.test_client()
        c_ramesh.post("/api/login", json={"email": "ramesh@udyamsetu.in", "password": "password123"})

        # Asha creates a discussion
        disc_res = c_asha.post("/api/discussions", json={
            "title": "Best packaging materials for rural pottery?",
            "body": "Looking for biodegradable and sustainable protective materials for terracotta clay items."
        })
        self.assertEqual(disc_res.status_code, 201)
        disc_id = disc_res.get_json()["disc_id"]

        # Ramesh comments on Asha's discussion
        comment_res = c_ramesh.post(f"/api/discussions/{disc_id}/comments", json={
            "text": "Have you considered dry paddy straw or shredded areca palm leaves? We use them in Shimoga."
        })
        self.assertEqual(comment_res.status_code, 201)

        # Asha should have received a new_comment notification
        asha_notifs = c_asha.get("/api/notifications?unread=1").get_json()["notifications"]
        comment_notif = next((n for n in asha_notifs if n["event_type"] == "new_comment" and disc_id in n["link_url"]), None)
        self.assertIsNotNone(comment_notif)
        self.assertEqual(comment_notif["actor_id"], "ramesh-kumar")
        self.assertIn("replied", comment_notif["message"].lower())

    def test_29_cross_user_product_deletion_authorization(self):
        """29. Ensure users cannot delete other entrepreneurs' products and unauthenticated deletion fails."""
        c_asha = app.test_client()
        c_asha.post("/api/login", json={"email": "asha@udyamsetu.in", "password": "password123"})

        c_ramesh = app.test_client()
        c_ramesh.post("/api/login", json={"email": "ramesh@udyamsetu.in", "password": "password123"})

        # Asha adds a product
        add_res = c_asha.post("/api/profile/products", json={
            "name": "Artisan Cane Storage Basket",
            "price": "₹650"
        })
        self.assertEqual(add_res.status_code, 201)
        prod_id = add_res.get_json()["product"]["id"]

        # Guest attempts to delete -> 401 Unauthorized
        c_guest = app.test_client()
        guest_del = c_guest.delete(f"/api/profile/products/{prod_id}")
        self.assertEqual(guest_del.status_code, 401)

        # Ramesh attempts to delete Asha's product -> 403 Forbidden
        ramesh_del = c_ramesh.delete(f"/api/profile/products/{prod_id}")
        self.assertEqual(ramesh_del.status_code, 403)
        self.assertIn("Unauthorized", ramesh_del.get_json()["error"])

        # Asha deletes her own product -> 200 OK
        asha_del = c_asha.delete(f"/api/profile/products/{prod_id}")
        self.assertEqual(asha_del.status_code, 200)
        self.assertTrue(asha_del.get_json()["success"])

    def test_30_unsafe_website_url_validation(self):
        """30. Reject unsafe or malicious URL schemes in profile website updates."""
        c_asha = app.test_client()
        c_asha.post("/api/login", json={"email": "asha@udyamsetu.in", "password": "password123"})

        # Malicious javascript: scheme
        js_res = c_asha.post("/api/profile", json={"website": "javascript:alert(document.cookie)"})
        self.assertEqual(js_res.status_code, 400)
        self.assertIn("Invalid website URL", js_res.get_json()["error"])

        # Malicious data: scheme
        data_res = c_asha.post("/api/profile", json={"website": "data:text/html;base64,PHNjcmlwdD4="})
        self.assertEqual(data_res.status_code, 400)

        # Valid HTTPS website URL
        valid_res = c_asha.post("/api/profile", json={"website": "https://ashacrafts.org"})
        self.assertEqual(valid_res.status_code, 200)
        self.assertEqual(valid_res.get_json()["user"]["website"], "https://ashacrafts.org")

    def test_31_post_like_toggle_and_counter_integrity(self):
        """31. Test liking and unliking posts, state reflection, and non-negative like count constraint."""
        c_asha = app.test_client()
        c_asha.post("/api/login", json={"email": "asha@udyamsetu.in", "password": "password123"})

        # Get initial feed post #1
        feed_res = c_asha.get("/api/feed")
        posts = feed_res.get_json()
        target_post = posts[0]
        p_id = target_post["id"]
        initial_likes = target_post["likes"]

        # Like the post
        like_res = c_asha.post(f"/api/posts/{p_id}/like")
        self.assertEqual(like_res.status_code, 200)
        like_data = like_res.get_json()
        self.assertTrue(like_data["liked"])
        self.assertEqual(like_data["likes"], initial_likes + 1)

        # Calling like again acts as toggle -> unlikes
        unlike_res = c_asha.post(f"/api/posts/{p_id}/like")
        self.assertEqual(unlike_res.status_code, 200)
        unlike_data = unlike_res.get_json()
        self.assertFalse(unlike_data["liked"])
        self.assertEqual(unlike_data["likes"], initial_likes)

    def test_32_sql_injection_defense_and_safe_parameterization(self):
        """32. Test that SQL injection payloads in search and filters are safely neutralized."""
        c_guest = app.test_client()

        # SQL injection in search text
        sqli_searches = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT id, user_id, name, email, password_hash, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 0, '' FROM users --"
        ]
        for payload in sqli_searches:
            res = c_guest.get(f"/api/entrepreneurs?q={payload}")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            # Must return list (empty or matched) without server error
            self.assertIsInstance(data, list)
            # Password hashes MUST NOT be exposed under any circumstance
            for item in data:
                self.assertNotIn("password_hash", item)
                self.assertNotIn("password", item)

    def test_33_session_cookie_security_configuration(self):
        """33. Verify session cookie HttpOnly and SameSite security attributes."""
        c = app.test_client()
        res = c.post("/api/login", json={"email": "asha@udyamsetu.in", "password": "password123"})
        self.assertEqual(res.status_code, 200)

        # Inspect Set-Cookie header
        set_cookie = res.headers.get("Set-Cookie", "")
        self.assertIn("udyamsetu_session", set_cookie)
        self.assertIn("HttpOnly", set_cookie)
        self.assertIn("SameSite=Lax", set_cookie)

    def test_34_database_foreign_key_enforcement(self):
        """34. Verify SQLite foreign keys cascade on user deletion."""
        conn = get_db()
        cursor = conn.cursor()

        # Check PRAGMA foreign_keys is 1 (ON)
        cursor.execute("PRAGMA foreign_keys;")
        fk_status = cursor.fetchone()[0]
        self.assertEqual(fk_status, 1, "Foreign keys MUST be enabled in SQLite.")

        # Create temporary user and child product
        temp_uid = "temp-cascade-user"
        cursor.execute("""
        INSERT INTO users (user_id, name, email, password_hash)
        VALUES (?, 'Cascade Tester', 'cascade@test.in', 'hash123')
        """, (temp_uid,))
        cursor.execute("""
        INSERT INTO products (user_id, name, price, image)
        VALUES (?, 'Temp Product', '₹100', 'assets/images/digital_rahul.jpg')
        """, (temp_uid,))
        conn.commit()

        # Verify product exists
        cursor.execute("SELECT COUNT(*) FROM products WHERE user_id = ?", (temp_uid,))
        self.assertEqual(cursor.fetchone()[0], 1)

        # Delete user -> cascading deletion of products
        cursor.execute("DELETE FROM users WHERE user_id = ?", (temp_uid,))
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM products WHERE user_id = ?", (temp_uid,))
        self.assertEqual(cursor.fetchone()[0], 0, "Child product should cascade delete when parent user is deleted.")
        conn.close()

if __name__ == "__main__":
    unittest.main()



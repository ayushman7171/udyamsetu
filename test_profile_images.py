import io
import os
import unittest
from PIL import Image
from app import app
from database import init_db, get_db

class ProfileImagesTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        init_db()
        self.client = app.test_client()

    def get_csrf_token(self):
        res = self.client.get("/api/csrf-token")
        return res.get_json().get("csrf_token")

    def create_dummy_image(self, format="JPEG", size=(100, 100), color=(255, 0, 0)):
        buf = io.BytesIO()
        img = Image.new("RGB", size, color=color)
        img.save(buf, format=format)
        buf.seek(0)
        return buf

    def test_upload_requires_authentication(self):
        img_buf = self.create_dummy_image()
        res = self.client.post(
            "/api/upload",
            data={"file": (img_buf, "test.jpg"), "image_type": "avatar"},
            content_type="multipart/form-data"
        )
        self.assertEqual(res.status_code, 401)

    def test_upload_validation(self):
        # Login as asha
        self.client.post("/api/login", json={"email": "asha@udyamsetu.in", "password": "password123"})

        # Missing file
        res = self.client.post("/api/upload", data={"image_type": "avatar"}, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)
        self.assertIn("No file", res.get_json()["error"])

        # Invalid type
        fake_buf = io.BytesIO(b"This is not an image file")
        res = self.client.post(
            "/api/upload",
            data={"file": (fake_buf, "bad.txt"), "image_type": "avatar"},
            content_type="multipart/form-data"
        )
        self.assertEqual(res.status_code, 400)

        # Invalid image_type parameter
        good_buf = self.create_dummy_image()
        res = self.client.post(
            "/api/upload",
            data={"file": (good_buf, "good.jpg"), "image_type": "malicious_type"},
            content_type="multipart/form-data"
        )
        self.assertEqual(res.status_code, 400)

    def test_successful_upload_and_persistence(self):
        # Login as asha
        self.client.post("/api/login", json={"email": "asha@udyamsetu.in", "password": "password123"})

        # Upload avatar
        av_buf = self.create_dummy_image(format="JPEG", color=(10, 20, 30))
        res_av = self.client.post(
            "/api/upload",
            data={"file": (av_buf, "my_avatar.jpg"), "image_type": "avatar"},
            content_type="multipart/form-data"
        )
        self.assertEqual(res_av.status_code, 200)
        av_data = res_av.get_json()
        self.assertTrue(av_data["success"])
        avatar_url = av_data["url"]
        self.assertTrue(avatar_url.startswith("/assets/uploads/"))

        # Upload business logo
        logo_buf = self.create_dummy_image(format="PNG", color=(50, 100, 150))
        res_logo = self.client.post(
            "/api/upload",
            data={"file": (logo_buf, "my_logo.png"), "image_type": "business_logo"},
            content_type="multipart/form-data"
        )
        self.assertEqual(res_logo.status_code, 200)
        logo_url = res_logo.get_json()["url"]

        # Upload cover image
        cover_buf = self.create_dummy_image(format="WEBP", color=(200, 200, 200))
        res_cover = self.client.post(
            "/api/upload",
            data={"file": (cover_buf, "my_cover.webp"), "image_type": "cover"},
            content_type="multipart/form-data"
        )
        self.assertEqual(res_cover.status_code, 200)
        cover_url = res_cover.get_json()["url"]

        # Save to profile
        save_res = self.client.post("/api/profile", json={
            "name": "Asha Devi Updated",
            "avatar": avatar_url,
            "business_logo_url": logo_url,
            "cover_image_url": cover_url
        })
        self.assertEqual(save_res.status_code, 200)
        saved_user = save_res.get_json()["user"]
        self.assertEqual(saved_user["avatar"], avatar_url)
        self.assertEqual(saved_user["business_logo_url"], logo_url)
        self.assertEqual(saved_user["cover_image_url"], cover_url)

        # Confirm persistence on GET /api/profile
        get_profile = self.client.get("/api/profile")
        self.assertEqual(get_profile.status_code, 200)
        p_data = get_profile.get_json()
        self.assertEqual(p_data["avatar"], avatar_url)
        self.assertEqual(p_data["business_logo_url"], logo_url)
        self.assertEqual(p_data["cover_image_url"], cover_url)

        # Confirm public visibility on GET /api/entrepreneurs/asha-devi
        pub_res = self.client.get(f"/api/entrepreneurs/{p_data['user_id']}")
        self.assertEqual(pub_res.status_code, 200)
        pub_data = pub_res.get_json()
        self.assertEqual(pub_data["avatar"], avatar_url)
        self.assertEqual(pub_data["business_logo_url"], logo_url)
        self.assertEqual(pub_data["cover_image_url"], cover_url)

        # Test removing business logo
        remove_logo_res = self.client.post("/api/profile", json={
            "business_logo_url": ""
        })
        self.assertEqual(remove_logo_res.status_code, 200)
        self.assertEqual(remove_logo_res.get_json()["user"]["business_logo_url"], "")

    def test_upload_csrf_protection(self):
        # Login
        self.client.post("/api/login", json={"email": "asha@udyamsetu.in", "password": "password123"})
        buf = self.create_dummy_image()

        # Without token and with CSRF enforcement -> 403
        res_fail = self.client.post(
            "/api/upload",
            data={"file": (buf, "test.jpg"), "image_type": "avatar"},
            content_type="multipart/form-data",
            headers={"X-Test-Enforce-CSRF": "1"}
        )
        self.assertEqual(res_fail.status_code, 403)

        # With valid token -> 200
        token = self.get_csrf_token()
        buf2 = self.create_dummy_image()
        res_ok = self.client.post(
            "/api/upload",
            data={"file": (buf2, "test.jpg"), "image_type": "avatar"},
            content_type="multipart/form-data",
            headers={"X-Test-Enforce-CSRF": "1", "X-CSRF-Token": token}
        )
        self.assertEqual(res_ok.status_code, 200)

if __name__ == "__main__":
    unittest.main()

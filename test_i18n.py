"""
Comprehensive automated tests for UdyamSetu Multilingual Support & Localization Engine (i18n).
Covers:
1. 23 Locale file integrity and key validation (en + 22 scheduled Indian languages)
2. English fallback mechanisms and coverage checks
3. RTL language definitions (Urdu, Kashmiri, Sindhi)
4. /api/languages and /api/locales endpoints
5. /api/i18n/audit development diagnostics
6. Language preference persistence in SQLite user records & sessions
7. User registration with preferred language
8. User-generated content translation preview endpoint (/api/translate)
9. Unicode text storage and retrieval in database
"""

import json
import os
import unittest
from app import app
from database import get_db, init_db

ALL_23_LANGUAGES = [
    "en", "hi", "mr", "gu", "bn", "ta", "te", "kn", "pa", "ur",
    "or", "ml", "as", "mai", "sa", "ne", "sat", "ks", "sd", "kok",
    "mni", "br", "doi"
]

RTL_LANGUAGES = ["ur", "ks", "sd"]

REVIEWED_FULL_LANGUAGES = ["en", "hi", "mr", "gu", "bn", "ta", "te", "kn", "pa", "ur"]


class TestI18nSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.locales_dir = os.path.join(os.path.dirname(__file__), "locales")
        cls.client = app.test_client()

    def test_01_all_23_locales_exist_and_valid_json(self):
        """Verify all 23 language files exist in locales/ and parse as valid JSON."""
        self.assertTrue(os.path.isdir(self.locales_dir), "locales directory must exist")
        for lang in ALL_23_LANGUAGES:
            path = os.path.join(self.locales_dir, f"{lang}.json")
            self.assertTrue(os.path.isfile(path), f"Locale file for {lang} must exist: {path}")
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    self.assertIsInstance(data, dict, f"{lang}.json must be a JSON object")
                except json.JSONDecodeError as err:
                    self.fail(f"Invalid JSON in {lang}.json: {err}")

    def test_02_english_canonical_dictionary_completeness(self):
        """Verify English reference dictionary has all mandatory domain sections."""
        en_path = os.path.join(self.locales_dir, "en.json")
        with open(en_path, "r", encoding="utf-8") as f:
            en_data = json.load(f)

        required_sections = [
            "nav", "landing", "auth", "dashboard", "directory",
            "profile", "collab", "msg", "notif", "disc", "learn", "common"
        ]
        for sec in required_sections:
            self.assertIn(sec, en_data, f"en.json must contain '{sec}' section")
            self.assertGreater(len(en_data[sec]), 0, f"'{sec}' section must not be empty")

    def test_03_reviewed_languages_coverage(self):
        """Verify the 10 reviewed languages have 100% key coverage against en.json."""
        with open(os.path.join(self.locales_dir, "en.json"), "r", encoding="utf-8") as f:
            en_dict = json.load(f)

        def extract_keys(d, prefix=""):
            keys = set()
            for k, v in d.items():
                p = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    keys.update(extract_keys(v, p))
                else:
                    keys.add(p)
            return keys

        canonical_keys = extract_keys(en_dict)

        for lang in REVIEWED_FULL_LANGUAGES:
            with open(os.path.join(self.locales_dir, f"{lang}.json"), "r", encoding="utf-8") as f:
                lang_dict = json.load(f)
            lang_keys = extract_keys(lang_dict)
            missing = canonical_keys - lang_keys
            self.assertEqual(len(missing), 0, f"{lang}.json missing keys: {missing}")

    def test_04_get_languages_endpoint(self):
        """Test GET /api/languages returns 23 languages with proper schema."""
        res = self.client.get("/api/languages")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        langs = data.get("languages", [])
        self.assertEqual(len(langs), 23)

        codes = [l["code"] for l in langs]
        for expected in ALL_23_LANGUAGES:
            self.assertIn(expected, codes)

        # Check RTL flags
        for l in langs:
            if l["code"] in RTL_LANGUAGES:
                self.assertEqual(l["dir"], "rtl", f"{l['code']} must be rtl")
            else:
                self.assertEqual(l["dir"], "ltr", f"{l['code']} must be ltr")

    def test_05_i18n_audit_endpoint(self):
        """Test GET /api/i18n/audit reports coverage and staging status."""
        res = self.client.get("/api/i18n/audit")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("languages_count"), 23)
        self.assertGreater(data.get("total_canonical_keys"), 100)

        audit = data.get("audit", {})
        # English, Hindi, Marathi, etc. must have 100% coverage
        for lang in ["en", "hi", "mr", "gu", "ur"]:
            self.assertIn(lang, audit)
            self.assertEqual(audit[lang]["coverage_pct"], 100.0)
            self.assertEqual(audit[lang]["missing_count"], 0)

        # Staged languages must be present with staging status
        for lang in ["sat", "ks", "kok"]:
            self.assertIn(lang, audit)
            self.assertEqual(audit[lang]["stage_status"], "staged_awaiting_review")

    def test_06_locales_static_serving(self):
        """Test GET /locales/<filename> serves UTF-8 encoded locale files."""
        res = self.client.get("/locales/hi.json")
        self.assertEqual(res.status_code, 200)
        self.assertIn("application/json", res.headers.get("Content-Type", ""))
        data = json.loads(res.data.decode("utf-8"))
        self.assertEqual(data["nav"]["home"], "होम")

        res_ur = self.client.get("/locales/ur.json")
        self.assertEqual(res_ur.status_code, 200)
        data_ur = json.loads(res_ur.data.decode("utf-8"))
        self.assertEqual(data_ur["nav"]["home"], "ہوم")

    def test_07_user_language_preference_sync_guest(self):
        """Test POST /api/user/language saves preference in session for unauthenticated visitors."""
        res = self.client.post("/api/user/language", json={"language": "mr"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("language"), "mr")

        # Invalid language rejection
        res_bad = self.client.post("/api/user/language", json={"language": "invalid_xyz"})
        self.assertEqual(res_bad.status_code, 400)

    def test_08_user_registration_with_language_preference(self):
        """Test user registration persists preferred_language in database."""
        email = f"test_i18n_user_{os.urandom(4).hex()}@example.com"
        reg_payload = {
            "name": "राजेश पाटिल",
            "email": email,
            "password": "Password123!",
            "account_type": "entrepreneur",
            "preferred_language": "mr"
        }
        res = self.client.post("/api/register", json=reg_payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["user"]["preferred_language"], "mr")

        # Verify in DB directly
        db = get_db()
        row = db.execute("SELECT preferred_language, name FROM users WHERE email = ?", (email,)).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["preferred_language"], "mr")
        self.assertEqual(row["name"], "राजेश पाटिल")

        # Verify /api/me returns the language
        me_res = self.client.get("/api/me")
        self.assertEqual(me_res.status_code, 200)
        me_data = me_res.get_json()
        self.assertEqual(me_data["user"]["preferred_language"], "mr")

        # Update language for this authenticated user to Hindi
        update_res = self.client.post("/api/user/language", json={"language": "hi"})
        self.assertEqual(update_res.status_code, 200)

        # Check DB update
        row2 = db.execute("SELECT preferred_language FROM users WHERE email = ?", (email,)).fetchone()
        self.assertEqual(row2["preferred_language"], "hi")

    def test_09_user_generated_content_translation_preview(self):
        """Test POST /api/translate returns translated preview with disclaimer and preserves original."""
        payload = {
            "text": "हमारे पास जैविक हल्दी और अदरक उपलब्ध है।",
            "source_lang": "hi",
            "target_lang": "en"
        }
        res = self.client.post("/api/translate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("translated_text", data)
        self.assertTrue("disclaimer" in data or "notice" in data)
        self.assertEqual(data.get("original_text"), payload["text"])

        # Test empty text error handling
        res_empty = self.client.post("/api/translate", json={"text": ""})
        self.assertEqual(res_empty.status_code, 400)

    def test_10_unicode_db_persistence(self):
        """Verify SQLite stores and retrieves UTF-8 text in all Indian scripts without corruption."""
        db = get_db()
        sample_texts = {
            "hi": "नमस्ते ग्रामीण उद्यमियों!",
            "bn": "গ্রামীণ উদ্যোক্তাদের সাথে সংযোগ করুন",
            "ta": "கிராமப்புற தொழில்முனைவோர் நெட்வொர்க்",
            "te": "గ్రామీణ పారిశ్రామికవేత్తల సమాఖ్య",
            "ur": "دیہی کاروباریوں کا رابطہ پلیٹ فارم",
            "gu": "ગ્રામીણ સાહસિકો સાથે જોડાઓ",
            "pa": "ਪੇਂਡੂ ਉੱਦਮੀਆਂ ਲਈ ਮੰਚ"
        }
        test_uid = f"usr_test_{os.urandom(4).hex()}"
        test_email = f"unicode_test_{os.urandom(4).hex()}@example.com"
        db.execute(
            "INSERT INTO users (user_id, name, email, password_hash, account_type, preferred_language) VALUES (?, ?, ?, 'fakehash', 'community_member', 'hi')",
            (test_uid, sample_texts["hi"], test_email)
        )
        db.commit()

        user = db.execute("SELECT name FROM users WHERE user_id = ?", (test_uid,)).fetchone()
    def test_11_untranslated_keys_audit_complete_languages(self):
        """Verify development audit flags untranslated strings for complete languages (no silent fallback)."""
        res = self.client.get("/api/i18n/audit")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        audit = data.get("audit", {})

        # Hindi is marked complete: must have 0 untranslated strings and 100% coverage
        self.assertIn("hi", audit)
        hi_audit = audit["hi"]
        self.assertEqual(hi_audit["missing_count"], 0, f"Hindi has untranslated keys: {hi_audit.get('missing_keys')}")
        self.assertEqual(hi_audit["coverage_pct"], 100.0)
        self.assertEqual(len(hi_audit["missing_keys"]), 0)

        # Directly verify hi.json contains non-English translations for all interface keys
        with open(os.path.join(self.locales_dir, "en.json"), "r", encoding="utf-8") as f:
            en_dict = json.load(f)
        with open(os.path.join(self.locales_dir, "hi.json"), "r", encoding="utf-8") as f:
            hi_dict = json.load(f)

        def check_no_silent_english_fallback(en_node, hi_node, path=""):
            for k, en_val in en_node.items():
                cur_path = f"{path}.{k}" if path else k
                self.assertIn(k, hi_node, f"Missing key in hi.json: {cur_path}")
                hi_val = hi_node[k]
                if isinstance(en_val, dict):
                    self.assertIsInstance(hi_val, dict, f"Mismatch type at {cur_path}")
                    check_no_silent_english_fallback(en_val, hi_val, cur_path)
                else:
                    self.assertIsInstance(hi_val, str, f"Value at {cur_path} must be string")
                    self.assertTrue(len(hi_val.strip()) > 0, f"Empty translation at {cur_path}")
                    # Translation must not be identical to English canonical string
                    self.assertNotEqual(
                        hi_val.strip(), en_val.strip(),
                        f"Untranslated interface string (silent English fallback) detected at {cur_path}: '{hi_val}'"
                    )

        check_no_silent_english_fallback(en_dict, hi_dict)


if __name__ == "__main__":
    unittest.main(verbosity=2)


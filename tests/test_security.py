import sqlite3
import time
import unittest

from tests.helpers import make_app, get_token, post_json, register_and_login, login_admin, USER


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.app, self.db_path = make_app()
        self.client = self.app.test_client()

    def test_password_is_hashed(self):
        token = get_token(self.client)
        post_json(self.client, "/api/register", USER, token)
        conn = sqlite3.connect(self.db_path)
        stored = conn.execute("SELECT password_hash FROM user WHERE login = ?", (USER["login"],)).fetchone()[0]
        conn.close()
        self.assertNotEqual(stored, USER["password"])
        self.assertTrue(stored.startswith(("scrypt:", "pbkdf2:")))

    def test_sql_injection_in_login(self):
        token = get_token(self.client)
        r = post_json(self.client, "/api/login", {"login": "' OR '1'='1' --", "password": "x"}, token)
        self.assertEqual(r.status_code, 401)
        r = post_json(self.client, "/api/login", {"login": "Conf2027'; DROP TABLE user; --", "password": "Demo77"}, token)
        self.assertEqual(r.status_code, 401)
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM user").fetchone()[0]
        conn.close()
        self.assertEqual(count, 1)   # таблица на месте, остался только админ

    def test_guest_has_no_access(self):
        self.assertEqual(self.client.get("/dashboard").status_code, 302)      # уводит на вход
        self.assertEqual(self.client.get("/admin").status_code, 302)
        self.assertEqual(self.client.get("/api/admin/requests").status_code, 401)

    def test_user_cannot_open_admin(self):
        register_and_login(self.client)
        self.assertEqual(self.client.get("/admin").status_code, 403)
        self.assertEqual(self.client.get("/api/admin/requests").status_code, 403)

    def test_admin_cannot_create_requests(self):
        token, _ = login_admin(self.client)
        r = post_json(self.client, "/api/requests", {}, token)
        self.assertEqual(r.status_code, 403)

    def test_post_without_csrf_token_rejected(self):
        get_token(self.client)
        r = self.client.post("/api/login", json={"login": "Conf2027", "password": "Demo77"})
        self.assertEqual(r.status_code, 400)

    def test_session_cookie_flags(self):
        token = get_token(self.client)
        r = post_json(self.client, "/api/login", {"login": "Conf2027", "password": "Demo77"}, token)
        cookie = r.headers.get("Set-Cookie", "")
        self.assertIn("conf_session=", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)

    def test_session_expires(self):
        login_admin(self.client)
        with self.client.session_transaction() as s:
            s["last_seen"] = time.time() - 31 * 60          # прошло 31 минута
        self.assertEqual(self.client.get("/admin").status_code, 302)

    def test_html_in_review_is_escaped(self):
        token, _ = register_and_login(self.client)
        post_json(self.client, "/api/requests", {"event_name": "Тест экранирования", "date": "2030-01-10", "start_time": "10:00",
                                                  "room_id": 1, "payment_method_id": 1}, token)
        admin = self.app.test_client()
        a_token, _ = login_admin(admin)
        post_json(admin, "/api/admin/requests/1/status", {"status_id": 2}, a_token)
        post_json(admin, "/api/admin/requests/1/status", {"status_id": 3}, a_token)
        post_json(self.client, "/api/requests/1/review", {"text": "<script>alert(1)</script>", "rating": 5}, token)
        page = self.client.get("/dashboard").get_data(as_text=True)
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("&lt;script&gt;", page)


if __name__ == "__main__":
    unittest.main()

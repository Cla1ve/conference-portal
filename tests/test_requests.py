import unittest
from datetime import date, timedelta

from tests.helpers import make_app, get_token, post_json, register_and_login, login_admin, USER

FUTURE = (date.today() + timedelta(days=20)).isoformat()
PAST = (date.today() - timedelta(days=2)).isoformat()


def new_request(date_=FUTURE, name="Встреча клуба"):
    return {"event_name": name, "date": date_, "start_time": "10:00", "room_id": 1, "payment_method_id": 1, "description": ""}


class RequestTests(unittest.TestCase):
    def setUp(self):
        self.app, self.db = make_app()
        self.client = self.app.test_client()
        self.token, _ = register_and_login(self.client)
        self.admin = self.app.test_client()
        self.admin_token, _ = login_admin(self.admin)

    def complete(self, request_id):
        post_json(self.admin, f"/api/admin/requests/{request_id}/status", {"status_id": 2}, self.admin_token)
        post_json(self.admin, f"/api/admin/requests/{request_id}/status", {"status_id": 3}, self.admin_token)

    def test_create_request_ok(self):
        r = post_json(self.client, "/api/requests", new_request(), self.token)
        self.assertEqual(r.status_code, 201)

    def test_past_date_rejected(self):
        r = post_json(self.client, "/api/requests", new_request(PAST), self.token)
        self.assertEqual(r.status_code, 400)
        self.assertIn("date", r.get_json()["errors"])

    def test_room_must_be_from_list(self):
        data = new_request()
        data["room_id"] = 999
        r = post_json(self.client, "/api/requests", data, self.token)
        self.assertEqual(r.status_code, 400)
        self.assertIn("room_id", r.get_json()["errors"])

    def test_review_not_allowed_before_completion(self):
        post_json(self.client, "/api/requests", new_request(), self.token)
        r = post_json(self.client, "/api/requests/1/review", {"text": "Хорошо", "rating": 5}, self.token)
        self.assertEqual(r.status_code, 400)
        self.assertIn("после завершения", r.get_json()["message"])

    def test_review_after_completion_and_only_once(self):
        post_json(self.client, "/api/requests", new_request(), self.token)
        self.complete(1)
        r = post_json(self.client, "/api/requests/1/review", {"text": "Хорошо", "rating": 5}, self.token)
        self.assertEqual(r.status_code, 201)
        r = post_json(self.client, "/api/requests/1/review", {"text": "Ещё раз", "rating": 4}, self.token)
        self.assertEqual(r.status_code, 400)

    def test_status_goes_only_forward(self):
        post_json(self.client, "/api/requests", new_request(), self.token)
        r = post_json(self.admin, "/api/admin/requests/1/status", {"status_id": 3}, self.admin_token)
        self.assertEqual(r.status_code, 400)             # нельзя перескочить через "назначено"
        r = post_json(self.admin, "/api/admin/requests/1/status", {"status_id": 2}, self.admin_token)
        self.assertEqual(r.status_code, 200)

    def test_user_sees_only_own_requests(self):
        post_json(self.client, "/api/requests", new_request(name="Моя заявка"), self.token)
        other = self.app.test_client()
        other_data = dict(USER, login="student02", email="second@example.ru")
        o_token, _ = register_and_login(other, other_data)
        page = other.get("/dashboard").get_data(as_text=True)
        self.assertNotIn("Моя заявка", page)
        self.assertEqual(post_json(other, "/api/requests/1/review", {"text": "Чужая", "rating": 5}, o_token).status_code, 400)

    def test_admin_filters(self):
        post_json(self.client, "/api/requests", new_request(name="Первая"), self.token)
        post_json(self.client, "/api/requests", new_request(name="Вторая"), self.token)
        self.complete(2)
        r = self.admin.get("/api/admin/requests?status=3")
        self.assertEqual([i["event_name"] for i in r.get_json()["items"]], ["Вторая"])
        r = self.admin.get("/api/admin/requests?q=Перв")
        self.assertEqual([i["event_name"] for i in r.get_json()["items"]], ["Первая"])

    def test_status_history_written(self):
        post_json(self.client, "/api/requests", new_request(), self.token)
        self.complete(1)
        import sqlite3
        conn = sqlite3.connect(self.db)
        n = conn.execute("SELECT COUNT(*) FROM status_history WHERE request_id = 1").fetchone()[0]
        conn.close()
        self.assertEqual(n, 3)   # создана, назначена, завершена

    def test_user_can_edit_new_request(self):
        post_json(self.client, "/api/requests", new_request(name="Старое название"), self.token)
        data = new_request(name="Новое название")
        data["room_id"] = 2
        r = self.client.put("/api/requests/1", json=data, headers={"X-CSRF-Token": self.token})
        self.assertEqual(r.status_code, 200)
        page = self.client.get("/dashboard").get_data(as_text=True)
        self.assertIn("Новое название", page)
        self.assertNotIn("Старое название", page)

    def test_cannot_edit_after_status_changed(self):
        post_json(self.client, "/api/requests", new_request(), self.token)
        post_json(self.admin, "/api/admin/requests/1/status", {"status_id": 2}, self.admin_token)
        r = self.client.put("/api/requests/1", json=new_request(), headers={"X-CSRF-Token": self.token})
        self.assertEqual(r.status_code, 400)
        r = self.client.delete("/api/requests/1", headers={"X-CSRF-Token": self.token})
        self.assertEqual(r.status_code, 400)

    def test_user_cancels_own_new_request(self):
        post_json(self.client, "/api/requests", new_request(), self.token)
        r = self.client.delete("/api/requests/1", headers={"X-CSRF-Token": self.token})
        self.assertEqual(r.status_code, 200)
        self.assertIn("У вас пока нет заявок", self.client.get("/dashboard").get_data(as_text=True))

    def test_cannot_cancel_foreign_request(self):
        post_json(self.client, "/api/requests", new_request(), self.token)
        other = self.app.test_client()
        o_token, _ = register_and_login(other, dict(USER, login="student03", email="third@example.ru"))
        r = other.delete("/api/requests/1", headers={"X-CSRF-Token": o_token})
        self.assertEqual(r.status_code, 404)

    def test_admin_delete_removes_everything(self):
        import sqlite3
        post_json(self.client, "/api/requests", new_request(), self.token)
        self.complete(1)
        post_json(self.client, "/api/requests/1/review", {"text": "Хорошо", "rating": 5}, self.token)
        r = self.admin.delete("/api/admin/requests/1", headers={"X-CSRF-Token": self.admin_token})
        self.assertEqual(r.status_code, 200)
        conn = sqlite3.connect(self.db)
        counts = [conn.execute("SELECT COUNT(*) FROM " + t).fetchone()[0] for t in ("request", "review", "event", "status_history")]
        conn.close()
        self.assertEqual(counts, [0, 0, 0, 0])


if __name__ == "__main__":
    unittest.main()

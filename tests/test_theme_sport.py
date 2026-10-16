"""Практика 18: те же сценарии, но для тематики «Спорт.РФ»."""
import re
import unittest
from datetime import date, timedelta

from tests.helpers import make_app, post_json, register_and_login, login_admin

OLD_WORDS = re.compile(r"мероприят|конференц", re.IGNORECASE)
FUTURE = (date.today() + timedelta(days=10)).isoformat()


def request_data():
    return {"event_name": "Тренировка по баскетболу", "date": FUTURE, "start_time": "18:00",
            "room_id": 1, "payment_method_id": 1, "description": ""}


class SportThemeTests(unittest.TestCase):
    def setUp(self):
        self.app, self.db = make_app("sport")
        self.client = self.app.test_client()

    def test_pages_have_no_conference_wording(self):
        for url in ("/", "/login", "/register"):
            html = self.client.get(url).get_data(as_text=True)
            self.assertNotRegex(html, OLD_WORDS, url)
            self.assertIn("Спорт.РФ", html)

    def test_sport_hero_image_and_colors(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("hero_sport.jpg", html)
        css = self.client.get("/theme.css").get_data(as_text=True)
        self.assertIn("#2b8a3e", css)

    def test_sport_dictionaries_in_form(self):
        register_and_login(self.client)
        html = self.client.get("/request/new").get_data(as_text=True)
        for name in ("Спортзал", "Бассейн", "Футбольное поле", "На месте"):
            self.assertIn(name, html)
        self.assertNotIn("Кинозал", html)
        self.assertIn("назначит тренировку", html)

    def test_full_flow_with_sport_status_names(self):
        token, _ = register_and_login(self.client)
        r = post_json(self.client, "/api/requests", request_data(), token)
        self.assertEqual(r.status_code, 201)
        request_id = r.get_json()["id"]

        admin = self.app.test_client()
        admin_token, _ = login_admin(admin)
        r = post_json(admin, f"/api/admin/requests/{request_id}/status", {"status_id": 2}, admin_token)
        self.assertEqual(r.get_json()["item"]["status"], "Тренировка назначена")
        post_json(admin, f"/api/admin/requests/{request_id}/status", {"status_id": 3}, admin_token)

        r = post_json(self.client, f"/api/requests/{request_id}/review", {"text": "Площадка чистая", "rating": 5}, token)
        self.assertEqual(r.status_code, 201)

    def test_rules_still_work_in_sport_theme(self):
        token, _ = register_and_login(self.client)
        data = request_data()
        data["date"] = (date.today() - timedelta(days=1)).isoformat()
        r = post_json(self.client, "/api/requests", data, token)
        self.assertEqual(r.status_code, 400)

    def test_admin_page_has_sport_button_text(self):
        admin = self.app.test_client()
        login_admin(admin)
        html = admin.get("/admin").get_data(as_text=True)
        self.assertIn('data-assign="Назначить тренировку"', html)


if __name__ == "__main__":
    unittest.main()

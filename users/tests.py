import re

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from projects.models import Project

from .validators import normalize_phone

User = get_user_model()


def make_user(email, name="Имя", surname="Фамилия", **extra):
    return User.objects.create_user(email=email, password="StrongPass123", name=name,
                                    surname=surname, **extra)


class UserModelTests(TestCase):
    def test_avatar_is_generated_on_create(self):
        user = make_user("a@example.com")
        self.assertTrue(user.avatar)
        self.assertTrue(user.avatar.name.startswith("avatars/"))

    def test_create_superuser(self):
        admin = User.objects.create_superuser("root@example.com", "StrongPass123",
                                              name="Root", surname="User")
        self.assertTrue(admin.is_staff and admin.is_superuser)


class PhoneValidationTests(TestCase):
    def test_normalize(self):
        self.assertEqual(normalize_phone("89991234567"), "+79991234567")
        self.assertEqual(normalize_phone("+79991234567"), "+79991234567")

    def test_invalid(self):
        for bad in ("123", "+7999123456", "79991234567", "8999123456a"):
            with self.assertRaises(Exception):
                normalize_phone(bad)


class AuthFlowTests(TestCase):
    def test_register_redirects_to_login(self):
        response = self.client.post(reverse("users:register"), {
            "name": "Мария", "surname": "Иванова",
            "email": "maria@example.com", "password": "StrongPass123",
        })
        self.assertRedirects(response, reverse("users:login"))
        self.assertTrue(User.objects.filter(email="maria@example.com").exists())

    def test_register_duplicate_email(self):
        make_user("dup@example.com")
        response = self.client.post(reverse("users:register"), {
            "name": "A", "surname": "B", "email": "DUP@example.com", "password": "StrongPass123",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)

    def test_login_and_logout(self):
        make_user("login@example.com")
        response = self.client.post(reverse("users:login"), {
            "email": "login@example.com", "password": "StrongPass123"})
        self.assertRedirects(response, reverse("projects:list"))
        response = self.client.get(reverse("users:logout"))
        self.assertRedirects(response, reverse("projects:list"))

    def test_login_wrong_password(self):
        make_user("login@example.com")
        response = self.client.post(reverse("users:login"), {
            "email": "login@example.com", "password": "wrong"})
        self.assertContains(response, "Неверный имейл или пароль")


class ProfileTests(TestCase):
    def setUp(self):
        self.user = make_user("me@example.com")
        self.other = make_user("other@example.com", phone="+79990000000")
        self.client.force_login(self.user)

    def test_profile_page_is_public(self):
        self.client.logout()
        response = self.client.get(reverse("users:detail", args=[self.user.pk]))
        self.assertContains(response, "me@example.com")

    def test_edit_profile_normalizes_phone(self):
        response = self.client.post(reverse("users:edit_profile"), {
            "name": "Новое", "surname": "Имя", "about": "Привет",
            "phone": "89991112233", "github_url": "https://github.com/someone",
        })
        self.assertRedirects(response, reverse("users:detail", args=[self.user.pk]))
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, "+79991112233")

    def test_phone_must_be_unique_in_any_format(self):
        response = self.client.post(reverse("users:edit_profile"), {
            "name": "Новое", "surname": "Имя", "phone": "89990000000"})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.phone)

    def test_github_must_lead_to_github(self):
        response = self.client.post(reverse("users:edit_profile"), {
            "name": "Новое", "surname": "Имя", "github_url": "https://example.com/x"})
        self.assertEqual(response.status_code, 200)

    def test_edit_profile_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("users:edit_profile"))
        self.assertEqual(response.status_code, 302)

    def test_change_password(self):
        response = self.client.post(reverse("users:change_password"), {
            "old_password": "StrongPass123",
            "new_password1": "AnotherPass456", "new_password2": "AnotherPass456"})
        self.assertRedirects(response, reverse("users:detail", args=[self.user.pk]))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("AnotherPass456"))


class UserListTests(TestCase):
    def setUp(self):
        self.me = make_user("me@example.com")
        self.author = make_user("author@example.com")
        self.fan = make_user("fan@example.com")
        self.member = make_user("member@example.com")
        self.stranger = make_user("stranger@example.com")
        self.their_project = Project.objects.create(name="Чужой", owner=self.author)
        self.my_project = Project.objects.create(name="Мой", owner=self.me)
        self.me.favorites.add(self.their_project)
        self.their_project.participants.add(self.me)
        self.fan.favorites.add(self.my_project)
        self.my_project.participants.add(self.member)

    def emails(self, response):
        return {u.email for u in response.context["page_obj"]}

    def test_pagination_and_order(self):
        for i in range(15):
            make_user(f"bulk{i}@example.com")
        response = self.client.get(reverse("users:list"))
        self.assertEqual(len(response.context["page_obj"]), 12)
        ids = [u.id for u in response.context["page_obj"]]
        self.assertEqual(ids, sorted(ids, reverse=True))

    def test_filters(self):
        self.client.force_login(self.me)
        expected = {
            "owners-of-favorite-projects": {"author@example.com"},
            "owners-of-participating-projects": {"author@example.com"},
            "interested-in-my-projects": {"fan@example.com"},
            "participants-of-my-projects": {"member@example.com"},
        }
        for filter_name, emails in expected.items():
            with self.subTest(filter=filter_name):
                response = self.client.get(reverse("users:list"), {"filter": filter_name})
                self.assertEqual(self.emails(response), emails)

    def test_filter_ignored_for_guests(self):
        response = self.client.get(reverse("users:list"), {"filter": "interested-in-my-projects"})
        self.assertEqual(len(response.context["page_obj"]), 5)
        self.assertIsNone(response.context["active_filter"])


class AvatarFileTests(TestCase):
    def test_png_signature(self):
        user = make_user("png@example.com")
        user.avatar.open("rb")
        self.assertEqual(user.avatar.read(4), b"\x89PNG")
        user.avatar.close()
        self.assertTrue(re.match(r"avatars/avatar_[0-9a-f-]+\.png$", user.avatar.name))

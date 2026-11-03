import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Project

User = get_user_model()


def make_user(email):
    return User.objects.create_user(email=email, password="StrongPass123",
                                    name="Имя", surname="Фамилия")


class ProjectViewsTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner@example.com")
        self.user = make_user("user@example.com")
        self.project = Project.objects.create(name="Проект", description="Описание",
                                              owner=self.owner)

    def post_json(self, url):
        return self.client.post(url, data=json.dumps({}), content_type="application/json")

    def test_root_redirects_to_list(self):
        self.assertRedirects(self.client.get("/"), reverse("projects:list"))

    def test_list_is_public_and_paginated(self):
        for i in range(14):
            Project.objects.create(name=f"P{i}", owner=self.owner)
        response = self.client.get(reverse("projects:list"))
        self.assertEqual(len(response.context["page_obj"]), 12)
        names = [p.created_at for p in response.context["page_obj"]]
        self.assertEqual(names, sorted(names, reverse=True))

    def test_detail(self):
        response = self.client.get(reverse("projects:detail", args=[self.project.pk]))
        self.assertContains(response, "Проект")

    def test_create_requires_login(self):
        response = self.client.get(reverse("projects:create"))
        self.assertEqual(response.status_code, 302)

    def test_create_sets_owner_and_participant(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("projects:create"), {
            "name": "Новый", "description": "...", "github_url": "", "status": "open"})
        project = Project.objects.get(name="Новый")
        self.assertRedirects(response, reverse("projects:detail", args=[project.pk]))
        self.assertEqual(project.owner, self.user)
        self.assertIn(self.user, project.participants.all())

    def test_create_validates_github(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("projects:create"), {
            "name": "Плохой", "github_url": "https://example.com", "status": "open"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Project.objects.filter(name="Плохой").exists())

    def test_edit_only_owner(self):
        url = reverse("projects:edit", args=[self.project.pk])
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.owner)
        response = self.client.post(url, {"name": "Переименован", "description": "",
                                          "github_url": "", "status": "open"})
        self.assertRedirects(response, reverse("projects:detail", args=[self.project.pk]))
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Переименован")

    def test_complete_project(self):
        url = reverse("projects:complete", args=[self.project.pk])
        self.client.force_login(self.user)
        self.assertEqual(self.post_json(url).status_code, 403)
        self.client.force_login(self.owner)
        response = self.post_json(url)
        self.assertEqual(response.json(), {"status": "ok", "project_status": "closed"})
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, "closed")
        self.assertEqual(self.post_json(url).status_code, 403)

    def test_toggle_participate(self):
        url = reverse("projects:toggle_participate", args=[self.project.pk])
        self.assertEqual(self.post_json(url).status_code, 401)
        self.client.force_login(self.user)
        self.assertTrue(self.post_json(url).json()["participant"])
        self.assertFalse(self.post_json(url).json()["participant"])

    def test_toggle_favorite_and_favorites_page(self):
        url = reverse("projects:toggle_favorite", args=[self.project.pk])
        self.assertEqual(self.post_json(url).status_code, 401)
        self.client.force_login(self.user)
        self.assertEqual(self.post_json(url).json(), {"status": "ok", "favorited": True})
        response = self.client.get(reverse("projects:favorites"))
        self.assertEqual(list(response.context["projects"]), [self.project])
        self.assertEqual(self.post_json(url).json(), {"status": "ok", "favorited": False})

    def test_favorites_page_requires_login(self):
        response = self.client.get(reverse("projects:favorites"))
        self.assertEqual(response.status_code, 302)

    def test_toggle_requires_post(self):
        self.client.force_login(self.user)
        url = reverse("projects:toggle_favorite", args=[self.project.pk])
        self.assertEqual(self.client.get(url).status_code, 405)

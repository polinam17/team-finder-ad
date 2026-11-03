import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("github_url", models.URLField(blank=True)),
                ("status", models.CharField(
                    choices=[("open", "Open"), ("closed", "Closed")],
                    default="open", max_length=6)),
                ("owner", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="owned_projects", to=settings.AUTH_USER_MODEL)),
                ("participants", models.ManyToManyField(
                    blank=True, related_name="participated_projects",
                    to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

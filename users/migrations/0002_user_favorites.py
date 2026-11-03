from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0001_initial"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="favorites",
            field=models.ManyToManyField(
                blank=True, related_name="interested_users", to="projects.project"),
        ),
    ]

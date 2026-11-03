from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from projects.models import Project

User = get_user_model()

DEMO_PASSWORD = "password"

DEMO_USERS = [
    ("maria@yandex.ru", "Мария", "Иванова", "Frontend-разработчик, люблю React."),
    ("ivan@yandex.ru", "Иван", "Петров", "Backend на Django и PostgreSQL."),
    ("anna@yandex.ru", "Анна", "Смирнова", "UI/UX-дизайнер."),
    ("oleg@yandex.ru", "Олег", "Кузнецов", "Ищу команду для pet-проекта."),
]

DEMO_PROJECTS = {
    "maria@yandex.ru": [
        ("Трекер привычек", "Мобильное веб-приложение для отслеживания привычек."),
    ],
    "ivan@yandex.ru": [
        ("Агрегатор мероприятий", "Сервис, который собирает афишу города в одном месте."),
    ],
    "anna@yandex.ru": [
        ("Дизайн-система", "Открытая библиотека компонентов для pet-проектов."),
    ],
    "oleg@yandex.ru": [
        ("Бот для учёбы", "Telegram-бот, который напоминает о дедлайнах."),
    ],
}


class Command(BaseCommand):
    help = "Создаёт тестовых пользователей и проекты (пароль у всех: password)."

    def handle(self, *args, **options):
        users = {}
        for email, name, surname, about in DEMO_USERS:
            user, created = User.objects.get_or_create(
                email=email, defaults={"name": name, "surname": surname, "about": about}
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            users[email] = user

        projects = []
        for email, items in DEMO_PROJECTS.items():
            for name, description in items:
                project, _ = Project.objects.get_or_create(
                    name=name, owner=users[email], defaults={"description": description}
                )
                project.participants.add(users[email])
                projects.append(project)

        # Немного связей между пользователями: участие и избранное.
        maria = users["maria@yandex.ru"]
        ivan = users["ivan@yandex.ru"]
        projects[1].participants.add(maria)
        projects[2].participants.add(maria, ivan)
        maria.favorites.add(projects[1], projects[3])
        ivan.favorites.add(projects[0])

        self.stdout.write(self.style.SUCCESS(
            f"Готово: пользователей {len(users)}, проектов {len(projects)}. "
            f"Пароль у всех: {DEMO_PASSWORD}."
        ))

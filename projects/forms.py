from django import forms

from users.validators import validate_github_url

from .models import Project


class ProjectForm(forms.ModelForm):
    status = forms.ChoiceField(
        label="Статус",
        choices=[(Project.STATUS_OPEN, "Открыт"), (Project.STATUS_CLOSED, "Закрыт")],
    )

    class Meta:
        model = Project
        fields = ("name", "description", "github_url", "status")
        labels = {
            "name": "Название проекта",
            "description": "Описание проекта",
            "github_url": "Ссылка на GitHub",
        }
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url", "")
        validate_github_url(url)
        return url

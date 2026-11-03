from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import BaseUserCreationForm, UserChangeForm

from .models import User


class AdminUserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ("email", "name", "surname")


class AdminUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = AdminUserChangeForm
    add_form = AdminUserCreationForm
    ordering = ("-id",)
    list_display = ("email", "name", "surname", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("email", "name", "surname")
    filter_horizontal = ("groups", "user_permissions", "favorites")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Профиль", {"fields": ("name", "surname", "avatar", "about", "phone", "github_url")}),
        ("Избранное", {"fields": ("favorites",)}),
        ("Права", {"fields": ("is_active", "is_staff", "is_superuser",
                              "groups", "user_permissions")}),
        ("Даты", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "name", "surname", "password1", "password2"),
        }),
    )

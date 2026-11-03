from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import LoginForm, ProfileForm, RegisterForm

User = get_user_model()

USERS_PER_PAGE = 12

USER_FILTERS = ("owners-of-favorite-projects", "owners-of-participating-projects",
                "interested-in-my-projects", "participants-of-my-projects")


def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("users:login")
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    form = LoginForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        login(request, form.user)
        next_url = request.GET.get("next", "")
        if next_url and url_has_allowed_host_and_scheme(next_url, request.get_host()):
            return redirect(next_url)
        return redirect("projects:list")
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("projects:list")


def user_detail(request, pk):
    profile = get_object_or_404(User, pk=pk)
    # Шаблон ожидает профиль в переменной user (владелец страницы), а текущий
    # пользователь берётся из request.user.
    return render(request, "users/user-details.html", {"user": profile})


def _filter_users(request, users, active_filter):
    me = request.user
    if active_filter == "owners-of-favorite-projects":
        return users.filter(owned_projects__in=me.favorites.all())
    if active_filter == "owners-of-participating-projects":
        return users.filter(owned_projects__participants=me).exclude(pk=me.pk)
    if active_filter == "interested-in-my-projects":
        return users.filter(favorites__owner=me).exclude(pk=me.pk)
    if active_filter == "participants-of-my-projects":
        return users.filter(participated_projects__owner=me).exclude(pk=me.pk)
    return users


def user_list(request):
    users = User.objects.all()
    active_filter = request.GET.get("filter")
    if request.user.is_authenticated and active_filter in USER_FILTERS:
        users = _filter_users(request, users, active_filter).distinct()
    else:
        active_filter = None
    users = users.order_by("-id")
    page_obj = Paginator(users, USERS_PER_PAGE).get_page(request.GET.get("page"))
    context = {
        "participants": users,
        "page_obj": page_obj,
        "active_filter": active_filter,
        "query_prefix": f"filter={active_filter}&" if active_filter else "",
    }
    return render(request, "users/participants.html", context)


@login_required
def edit_profile(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Профиль обновлён.")
        return redirect("users:detail", pk=request.user.pk)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return redirect("users:detail", pk=user.pk)
    return render(request, "users/change_password.html", {"form": form})

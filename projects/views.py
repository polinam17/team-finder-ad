from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProjectForm
from .models import Project

PROJECTS_PER_PAGE = 12


def index(request):
    return redirect("projects:list")


def project_list(request):
    projects = Project.objects.select_related("owner").order_by("-created_at", "-id")
    page_obj = Paginator(projects, PROJECTS_PER_PAGE).get_page(request.GET.get("page"))
    context = {"projects": projects, "page_obj": page_obj, "query_prefix": ""}
    return render(request, "projects/project_list.html", context)


@login_required
def favorite_projects(request):
    projects = request.user.favorites.select_related("owner").order_by("-created_at", "-id")
    return render(request, "projects/favorite_projects.html", {"projects": projects})


def project_detail(request, pk):
    project = get_object_or_404(Project.objects.select_related("owner"), pk=pk)
    return render(request, "projects/project-details.html", {"project": project})


@login_required
def create_project(request):
    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        project.participants.add(request.user)
        return redirect("projects:detail", pk=project.pk)
    return render(request, "projects/create-project.html", {"form": form, "is_edit": False})


@login_required
def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.owner_id != request.user.id:
        raise PermissionDenied
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("projects:detail", pk=project.pk)
    return render(request, "projects/create-project.html", {"form": form, "is_edit": True})


def _unauthorized():
    return JsonResponse({"status": "error", "detail": "Необходима авторизация."}, status=401)


@require_POST
def complete_project(request, pk):
    if not request.user.is_authenticated:
        return _unauthorized()
    project = get_object_or_404(Project, pk=pk)
    if project.owner_id != request.user.id or project.status != Project.STATUS_OPEN:
        return JsonResponse({"status": "error"}, status=403)
    project.status = Project.STATUS_CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": Project.STATUS_CLOSED})


@require_POST
def toggle_participate(request, pk):
    if not request.user.is_authenticated:
        return _unauthorized()
    project = get_object_or_404(Project, pk=pk)
    if project.participants.filter(pk=request.user.pk).exists():
        project.participants.remove(request.user)
        participant = False
    else:
        project.participants.add(request.user)
        participant = True
    return JsonResponse({"status": "ok", "participant": participant})


@require_POST
def toggle_favorite(request, pk):
    if not request.user.is_authenticated:
        return _unauthorized()
    project = get_object_or_404(Project, pk=pk)
    if request.user.favorites.filter(pk=project.pk).exists():
        request.user.favorites.remove(project)
        favorited = False
    else:
        request.user.favorites.add(project)
        favorited = True
    return JsonResponse({"status": "ok", "favorited": favorited})

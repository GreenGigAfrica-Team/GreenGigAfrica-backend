"""Landing page view — serves the static HTML landing page."""
from django.shortcuts import render
from apps.tasks.models import Task
from apps.organisations.models import Organisation


def landing(request):
    context = {
        "active_org_count": Organisation.objects.filter(
            status=Organisation.Status.APPROVED
        ).count(),
        "open_task_count": Task.objects.filter(status=Task.Status.OPEN).count(),
        "total_tasks_completed": Task.objects.filter(
            status=Task.Status.COMPLETED
        ).count(),
    }
    return render(request, "landing/index.html", context)


def signup(request):
    return render(request, "accounts/signup.html")


def login_view(request):
    return render(request, "accounts/login.html")


def dashboard(request):
    return render(request, "dashboard/index.html")


def org_register_view(request):
    return render(request, "accounts/org_register.html")

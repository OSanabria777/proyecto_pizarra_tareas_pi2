from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils import timezone

from .forms import LoginForm, TaskForm
from .models import Task


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


class CustomLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = 'login'


def superuser_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'No tienes permisos para realizar esa acción.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)

    return _wrapped


def task_scope_queryset(user, status):
    queryset = Task.objects.filter(status=status)
    if user.is_superuser:
        return queryset
    return queryset.filter(asignado_a=user)


def apply_superuser_filters(request, queryset):
    selected_assignee = request.GET.get('asignado_a', '').strip()
    search_query = request.GET.get('q', '').strip()
    selected_order = request.GET.get('order', 'recent').strip() or 'recent'

    if selected_assignee:
        if selected_assignee == 'unassigned':
            queryset = queryset.filter(asignado_a__isnull=True)
        elif selected_assignee.isdigit():
            queryset = queryset.filter(asignado_a_id=int(selected_assignee))

    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(asignado_a__username__icontains=search_query)
        )

    order_map = {
        'recent': ('-created_at',),
        'oldest': ('created_at',),
    }
    queryset = queryset.order_by(*order_map.get(selected_order, order_map['recent']))

    return queryset, selected_assignee, selected_order, search_query


@login_required
def dashboard(request):
    pending_queryset = task_scope_queryset(request.user, Task.Status.PENDING)
    completed_queryset = task_scope_queryset(request.user, Task.Status.COMPLETED)

    if request.user.is_superuser:
        tasks, selected_assignee, selected_order, search_query = apply_superuser_filters(request, pending_queryset)
        filter_users = get_user_model().objects.order_by('username')
        filtered_count = tasks.count()
    else:
        tasks = pending_queryset
        selected_assignee = ''
        selected_order = 'recent'
        search_query = ''
        filter_users = []
        filtered_count = tasks.count()

    return render(request, 'dashboard.html', {
        'tasks': tasks,
        'pending_count': pending_queryset.count(),
        'completed_count': completed_queryset.count(),
        'filtered_count': filtered_count,
        'filter_users': filter_users,
        'selected_assignee': selected_assignee,
        'selected_order': selected_order,
        'search_query': search_query,
    })


@login_required
def completed_tasks(request):
    pending_queryset = task_scope_queryset(request.user, Task.Status.PENDING)
    completed_queryset = task_scope_queryset(request.user, Task.Status.COMPLETED)

    if request.user.is_superuser:
        tasks, selected_assignee, selected_order, search_query = apply_superuser_filters(request, completed_queryset)
        filter_users = get_user_model().objects.order_by('username')
        filtered_count = tasks.count()
    else:
        tasks = completed_queryset
        selected_assignee = ''
        selected_order = 'recent'
        search_query = ''
        filter_users = []
        filtered_count = tasks.count()

    return render(request, 'completed.html', {
        'tasks': tasks,
        'completed_count': completed_queryset.count(),
        'pending_count': pending_queryset.count(),
        'filtered_count': filtered_count,
        'filter_users': filter_users,
        'selected_assignee': selected_assignee,
        'selected_order': selected_order,
        'search_query': search_query,
    })


@login_required
def profile_view(request):
    pending_count = task_scope_queryset(request.user, Task.Status.PENDING).count()
    completed_count = task_scope_queryset(request.user, Task.Status.COMPLETED).count()
    return render(request, 'profile.html', {
        'profile_user': request.user,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'total_tasks': pending_count + completed_count,
    })


@superuser_required
def task_create(request):
    form = TaskForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        task = form.save(commit=False)
        task.status = Task.Status.PENDING
        task.completed_at = None
        task.save()
        messages.success(request, 'Tarea creada.')
        return redirect('dashboard')

    return render(request, 'task_form.html', {'form': form, 'title': 'Nueva tarea', 'action': 'Crear', 'back_url': 'dashboard'})


@superuser_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    form = TaskForm(request.POST or None, instance=task)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tarea actualizada.')
        return redirect('dashboard' if task.status == Task.Status.PENDING else 'completed')

    return render(request, 'task_form.html', {'form': form, 'title': 'Editar tarea', 'action': 'Guardar cambios', 'back_url': 'completed' if task.status == Task.Status.COMPLETED else 'dashboard'})


@superuser_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Tarea eliminada.')
        return redirect('dashboard')

    return render(request, 'task_confirm_delete.html', {'task': task, 'back_url': 'completed' if task.status == Task.Status.COMPLETED else 'dashboard'})


@login_required
@require_POST
def task_complete(request, pk):
    if request.user.is_superuser:
        task = get_object_or_404(Task, pk=pk)
    else:
        task = get_object_or_404(Task, pk=pk, asignado_a=request.user)
    task.status = Task.Status.COMPLETED
    task.completed_at = timezone.now()
    task.save(update_fields=['status', 'completed_at'])
    messages.success(request, 'Tarea marcada como completada.')
    return redirect('completed')

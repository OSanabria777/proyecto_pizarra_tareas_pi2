from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import LoginForm, RegisterForm, TaskForm
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


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        auth_login(request, user)
        messages.success(request, 'Tu cuenta fue creada correctamente.')
        return redirect('dashboard')

    return render(request, 'register.html', {'form': form})


@login_required
def dashboard(request):
    tasks = Task.objects.filter(user=request.user, status=Task.Status.PENDING)
    completed_count = Task.objects.filter(user=request.user, status=Task.Status.COMPLETED).count()
    return render(request, 'dashboard.html', {
        'tasks': tasks,
        'pending_count': tasks.count(),
        'completed_count': completed_count,
    })


@login_required
def completed_tasks(request):
    tasks = Task.objects.filter(user=request.user, status=Task.Status.COMPLETED)
    return render(request, 'completed.html', {
        'tasks': tasks,
        'completed_count': tasks.count(),
        'pending_count': Task.objects.filter(user=request.user, status=Task.Status.PENDING).count(),
    })


@login_required
def task_create(request):
    form = TaskForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        task = form.save(commit=False)
        task.user = request.user
        task.status = Task.Status.PENDING
        task.completed_at = None
        task.save()
        messages.success(request, 'Tarea creada.')
        return redirect('dashboard')

    return render(request, 'task_form.html', {'form': form, 'title': 'Nueva tarea', 'action': 'Crear', 'back_url': 'dashboard'})


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if task.status == Task.Status.COMPLETED:
        messages.info(request, 'Las tareas completadas no se pueden editar.')
        return redirect('completed')
    form = TaskForm(request.POST or None, instance=task)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tarea actualizada.')
        return redirect('dashboard' if task.status == Task.Status.PENDING else 'completed')

    return render(request, 'task_form.html', {'form': form, 'title': 'Editar tarea', 'action': 'Guardar cambios', 'back_url': 'completed' if task.status == Task.Status.COMPLETED else 'dashboard'})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if task.status == Task.Status.COMPLETED:
        messages.info(request, 'Las tareas completadas no se pueden eliminar desde aquí.')
        return redirect('completed')
    if request.method == 'POST':
        was_pending = task.status == Task.Status.PENDING
        task.delete()
        messages.success(request, 'Tarea eliminada.')
        return redirect('dashboard' if was_pending else 'completed')

    return render(request, 'task_confirm_delete.html', {'task': task, 'back_url': 'completed' if task.status == Task.Status.COMPLETED else 'dashboard'})


@login_required
@require_POST
def task_complete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        task.status = Task.Status.COMPLETED
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'completed_at'])
        messages.success(request, 'Tarea marcada como completada.')
    return redirect('completed')

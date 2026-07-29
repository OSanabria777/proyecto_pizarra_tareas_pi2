from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        COMPLETED = 'completed', 'Completada'

    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#ffeaa7')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    asignado_a = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
    related_name='tareas',
    null=True,
    blank=True
)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

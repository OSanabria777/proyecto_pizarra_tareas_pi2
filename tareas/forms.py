from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Task


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control form-control-lg', 'placeholder': 'Nombre de usuario'})
        self.fields['password'].widget.attrs.update({'class': 'form-control form-control-lg', 'placeholder': 'Contraseña'})


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('title', 'description', 'asignado_a', 'color')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Título de la tarea'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe la tarea'}),
            'asignado_a': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asignado_a'].required = True
        self.fields['asignado_a'].empty_label = 'Selecciona un usuario'

    def clean_color(self):
        color = self.cleaned_data['color'].strip()
        if not color:
            return '#ffeaa7'
        return color

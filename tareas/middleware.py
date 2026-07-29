from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden
from django.urls import reverse


class SessionAndAdminAccessMiddleware:
    open_url_names = {'home', 'login'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        admin_url = reverse('admin:index')
        is_admin_path = request.path.startswith(admin_url)

        if is_admin_path:
            if request.user.is_authenticated and not request.user.is_superuser:
                return HttpResponseForbidden('No posees los permisos necesarios para acceder.')
            return None

        resolver_match = getattr(request, 'resolver_match', None)
        url_name = resolver_match.url_name if resolver_match else None

        if url_name in self.open_url_names:
            return None

        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)

        return None

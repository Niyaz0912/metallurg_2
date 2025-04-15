from django.shortcuts import redirect
from django.urls import reverse


class AuthRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Проверяем только GET-запросы к корневому URL
        if request.method == 'GET' and request.path == '/':
            # Проверяем аутентификацию безопасно
            if hasattr(request, 'user') and request.user.is_authenticated:
                if hasattr(request.user, 'role'):
                    if request.user.role == 'admin':
                        return redirect('admin:index')
                    elif request.user.role in ['director', 'master']:
                        return redirect('production_plan:list')
                return redirect('shift_assignment:list')
            else:
                return redirect('login')

        return response
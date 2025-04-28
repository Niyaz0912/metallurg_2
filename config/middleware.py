from django.shortcuts import redirect


class AuthRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Обработка запросов
        if request.method == 'GET' and request.path == '/':
            if hasattr(request, 'user') and request.user.is_authenticated:
                if hasattr(request.user, 'role'):
                    if request.user.role == 'admin':
                        return redirect('admin:index')
                    elif request.user.role in ['director', 'master']:
                        return redirect('production_plan:list')
                return redirect('users:profile', username=request.user.username)
            else:
                return redirect('login')

        response = self.get_response(request)
        return response

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('production_plan/', include('production_plan.urls')),
    path('shift_assignment/', include('shift_assignment.urls')),
]

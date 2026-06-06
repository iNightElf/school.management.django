from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse, HttpResponseRedirect
from django.db import connections
from rest_framework import generics


def healthz(request):
    return JsonResponse({'status': 'ok'})


def health(request):
    try:
        connections['default'].cursor()
        return JsonResponse({'status': 'healthy', 'database': 'connected'})
    except Exception:
        return JsonResponse({'status': 'unhealthy', 'error': 'Database connection failed'}, status=503)


def root_redirect(request):
    return HttpResponseRedirect('/admin/')


class WakeDBView(generics.GenericAPIView):
    permission_classes = []
    def get(self, request):
        from django.db import connection
        connection.cursor()
        return JsonResponse({'status': 'awake'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root_redirect, name='root'),
    path('healthz/', healthz, name='healthz'),
    path('health/', health, name='health'),
    path('api/wake-db/', WakeDBView.as_view(), name='wake-db'),
    path('api/', include('accounts.urls')),
    path('api/', include('core.urls')),
    path('api/', include('students.urls')),
    path('api/', include('teachers.urls')),
    path('api/', include('staff.urls')),
    path('api/', include('books.urls')),
    path('api/', include('results.urls')),
    path('api/finance/', include('finance.urls')),
]

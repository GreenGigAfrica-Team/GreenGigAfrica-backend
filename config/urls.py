from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/tasks/', include('apps.tasks.urls')),
    path('api/v1/proof/', include('apps.proof.urls')),
    path('api/v1/organisations/', include('apps.organisations.urls')),
    path('api/v1/volunteers/', include('apps.volunteers.urls')),
    path('api/v1/ai/', include('apps.ai_engine.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.api.views import login_api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('assets/', include('assets.urls')),
    path('inventory/', include('inventory.urls')),
    path('locations/', include('locations.urls')),
    path('', include('assets.urls')),  # Корневой URL направляет на assets
    
    # API URLs
    path('api/', include('locations.api.urls')),
    path('api/', include('inventory.api.urls')),
    # path('api/', include('accounts.api.urls')),
    
    # Напрямую добавляем accounts API endpoint
    path('accounts/api/login/', login_api, name='api-login'),
]

# Добавляем URL-шаблоны для медиа-файлов в режиме отладки
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
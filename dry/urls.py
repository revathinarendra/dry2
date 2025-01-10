# from django.contrib import admin
# from django.urls import path, include
# from rest_framework_simplejwt.views import TokenObtainPairView, TokenVerifyView, TokenRefreshView
# from django.conf import settings
# from django.conf.urls.static import static

# from dry import views

# urlpatterns = [
#     path('', views.home, name='home'),
#     path('admin/', admin.site.urls),
#     path('api/', include('accounts.urls')),
#     path('api/', include('recruit.urls')),
#     path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
#     path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
# ]

# # Serve static and media files in development
# if settings.DEBUG:
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# # Custom error handlers
# handler404 = 'utils.error_views.handler404'
# handler500 = 'utils.error_views.handler500'
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenVerifyView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static

from dry import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),

    # API URLs
    path('api/accounts/', include('accounts.urls')),  # Include accounts API under /api/accounts/
    path('api/recruit/', include('recruit.urls')),    # Include recruit API under /api/recruit/
    
    # JWT Token routes
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'utils.error_views.handler404'
handler500 = 'utils.error_views.handler500'

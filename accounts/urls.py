from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('account/profile/', views.user_profile, name='user_profile'),
    path('account/updateprofile/',views.update_user_profile, name='update_profile'),
    path('login/', views.login_view, name='login'),
    # Add other URL patterns here
]

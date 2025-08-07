from django.urls import path
from . import views


urlpatterns = [
    # Auth Routes
    path('register/', views.register_user, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Member Routes
    path('profile/', views.UserProfileView.as_view(), name='profile'),

    # Admin Routes
    path('admin/view-user/<int:user_id>/', views.view_user_profile, name='admin-view-user'),
    path('admin/list-members/', views.list_members, name='list-members'),
    path('forget_password/', views.forget_password, name='forget_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset-password'),
    
]

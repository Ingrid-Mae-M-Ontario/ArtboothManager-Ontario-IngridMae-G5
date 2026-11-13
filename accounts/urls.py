from django.urls import path

from accounts import views

urlpatterns = [
    path('', views.dashboard_redirect, name='dashboard'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('dashboard/owner/', views.owner_dashboard, name='owner_dashboard'),
    path('dashboard/assistant/', views.assistant_dashboard, name='assistant_dashboard'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
]
from django.contrib.auth.views import LogoutView, LoginView
from django.urls import path, re_path, include
from . import views

#Add Django site authentication urls (for login, logout, password management)
urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/logout', LogoutView.as_view(), name='logout'),
    path('accounts/login', LoginView.as_view(), name='login'),
    path('accounts/register', views.register_request, name="register"),

    re_path(r'^accounts/edit/$', views.profile_edit, name='profile_edit')
]
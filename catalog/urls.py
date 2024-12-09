from django.urls import path
from . import views

urlpatterns = [
    path('', views.catalog_main_page, name='catalog_main_page'),
]

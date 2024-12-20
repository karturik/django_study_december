from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.catalog_main_page, name='catalog_main_page'),
    re_path(r'^books/$', views.BookListView.as_view(), name='book-list'),
    re_path(r'^book/(?P<pk>\d+)$', views.BookDetailView.as_view(), name='book-detail'),
    re_path(r'^authors/$', views.AuthorListView.as_view(), name='author-list'),
    re_path(r'^author/(?P<pk>\d+)$', views.AuthorDetailView.as_view(), name='author-detail'),

    re_path(r'^mybooks/$', views.LoanedBooksByUserListView.as_view(), name='my-borrowed'),

]

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render
from django.views import generic
from .models import Book, Author, BookInstance, Genre
from django.contrib.sessions.backends.db import SessionStore
    

def catalog_main_page(request):
    """
    Функция отображения для домашней страницы сайта.
    """
    # Генерация "количеств" некоторых главных объектов
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    # Доступные книги (статус = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count()  # Метод 'all()' применён по умолчанию.

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1
    
    # Отрисовка HTML-шаблона index.html с данными внутри
    # переменной контекста context
    return render(
        request,
        'catalog/catalog_main_page.html',
        context={
            'num_books': num_books,
            'num_instances': num_instances,
            'num_instances_available': num_instances_available,
            'num_authors': num_authors,
            'num_visits':num_visits
            }
    )
    

class BookListView(generic.ListView):
    model = Book
    paginate_by = 10

class BookDetailView(generic.DetailView):
    model = Book

    def get_context_data(self, **kwargs):
        # Взять базовый контекст из родительского класса 
        context = super(BookDetailView, self).get_context_data(**kwargs)
        book = self.object
        book_id = book.id
        
        # Получаем сессию из request
        session = self.request.session
        visit_key = f'num_visits_{book_id}'
        
        # Получаем количество посещений или 0 если первый визит
        visit_num = session.get(visit_key, 0)
        session[visit_key] = visit_num + 1
        session.save()

        # Добавить новый элемент к контексту
        context['visit_num'] = visit_num
        return context


class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10

class AuthorDetailView(generic.DetailView):
    model = Author
    model = Author

    
class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """
        Generic class-based view listing books on loan to current user.
    """
    login_url = reverse_lazy('login')
    
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')
        
import datetime
import pandas as pd

from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.urls import reverse_lazy, reverse
from django.shortcuts import render
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.sessions.backends.db import SessionStore

from .forms import RenewBookForm, UploadBooksFileForm
from .models import Book, Author, BookInstance, Genre, Language
from .utils import create_books_from_df

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

        # Add user_profile to context
        if self.request.user.is_authenticated:
            context['user_profile'] = self.request.user.profile
        else:
            context['user_profile'] = None

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

class AllBorrowedBooksListView(PermissionRequiredMixin, generic.ListView):
    """
        Generic class-based view listing books on loan for all users.
    """
    login_url = reverse_lazy('login')
    
    permission_required = 'catalog.can_mark_returned'
    permission_denied_message = "You don't have permission to view this page."
    
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_all.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')        

@permission_required('catalog.can_mark_returned', login_url='login')  
def renew_book_librarian(request, pk):
    book_inst = get_object_or_404(BookInstance, pk=pk)

    # Если данный запрос типа POST, тогда
    if request.method == 'POST':

        # Создаём экземпляр формы и заполняем данными из запроса (связывание, binding):
        form = RenewBookForm(request.POST)

        # Проверка валидности данных формы:
        if form.is_valid():
            # Обработка данных из form.cleaned_data
            #(здесь мы просто присваиваем их полю due_back)
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            # Переход по адресу 'all-borrowed':
            return HttpResponseRedirect(reverse('all-borrowed') )

    # Если это GET (или какой-либо ещё), создать форму по умолчанию.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst':book_inst})


class AuthorCreate(CreateView):
    model = Author
    fields = '__all__'
    initial={'date_of_death':'12/10/2016',}

class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name','last_name','date_of_birth','date_of_death']

class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('author-list')
    delete_message = "Автор удален."

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.error(self.request, self.delete_message)
        return response

class BookCreate(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, generic.CreateView):
    permission_required = 'catalog.can_mark_returned'
    model = Book
    fields = '__all__'
    success_url = reverse_lazy('book-list')
    success_message = "Книга успешно создана."

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response

class BookUpdate(UpdateView):
    model = Book
    fields = '__all__'

class BookDelete(DeleteView):
    model = Book
    success_url = reverse_lazy('book-list')


def book_file_upload_view(request):
    if request.method == 'POST':
        if 'file' not in request.FILES:
            return HttpResponse('No file uploaded')
        
        file = request.FILES['file']
        file_format = file.name.split('.')[-1].lower()
        
        if file_format == 'csv':
            try:
                df = pd.read_csv(file)
            except Exception as e:
                return HttpResponse(f'Error reading CSV file: {e}')
        elif file_format in ['xls', 'xlsx']:
            try:
                df = pd.read_excel(file)
            except Exception as e:
                return HttpResponse(f'Error reading Excel file: {e}')
        else:
            return HttpResponse('Unsupported file format')

        create_books_from_df(df)
        
        return HttpResponse(df.to_html())
    else:
        form = UploadBooksFileForm()
        return render(request, 'catalog/book_file_upload.html', context={'form': form})

def searching(request):
    print(request)
    if request.method == "POST":
        searched = request.POST.get('searched').title()
        print("User search query: ", searched)
        books_results = Book.objects.filter(title__icontains=searched)
        authors_results = Author.objects.filter(last_name__icontains=searched)
        print(books_results, authors_results)
        return render(request, "catalog/search_page.html", {'searched':searched, 
                                                            'books_results':books_results,
                                                            'authors_results':authors_results})
    else:
        return render(request, "catalog/search_page.html")
    
def like_book(request):
    if request.method == "POST":
        book_id = request.POST.get('book_id')
        book = Book.objects.get(pk=book_id)
        user_profile = request.user.profile  # предполагается, что у пользователя есть профиль

        if user_profile.liked_books.filter(id=book_id).exists():
            user_profile.liked_books.remove(book)
            status = 'unliked'
        else:
            user_profile.liked_books.add(book)
            status = 'liked'

        return JsonResponse({'status': status})

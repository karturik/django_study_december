import pandas as pd
from .models import Language, Genre, Book

def create_books_from_df(df: pd.DataFrame):

    language = Language.objects.get(name__icontains='EN')
    all_genres = Genre.objects.all()

    for _, row in df.iterrows():
        title = row['title']
        summary = row['summary']
        isbn = row['isbn']
        cover = row['cover_url']
        genre = row['genre']

        book = Book.objects.create(title=title, summary = summary, isbn=isbn, language=language, online_cover=cover)
        # Create genre as a post-step
        if not genre in [genre_model.name for genre_model in all_genres]:
            Genre.objects.create(name=genre)

        book_genres = Genre.objects.filter(name__exact = genre)
        book.genre.set(book_genres) # Присвоение типов many-to-many напрямую недопустимо

        book.save()

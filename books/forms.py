from django import forms
from .models import Book


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            "isbn", "title", "subtitle", "authors", "publisher",
            "publication_year", "description", "categories", "cover_image",
        ]


class BookImportForm(forms.Form):
    csv_file = forms.FileField(label="CSV File")
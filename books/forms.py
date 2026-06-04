from django import forms
from .models import Book, Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class BookForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.filter(is_archived=False),
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": "6"}),
        required=False,
    )

    class Meta:
        model = Book
        fields = [
            "isbn", "title", "subtitle", "authors", "publisher",
            "publication_year", "description", "categories", "cover_image",
        ]


class BookImportForm(forms.Form):
    csv_file = forms.FileField(label="CSV File")
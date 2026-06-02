from django import forms
from .models import BookCopy


class CopyForm(forms.ModelForm):
    acquisition_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = BookCopy
        fields = ["book", "acquisition_date", "shelf_location", "notes", "status"]


class CopyImportForm(forms.Form):
    csv_file = forms.FileField(label="CSV File")
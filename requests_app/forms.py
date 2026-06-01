from datetime import timedelta
from django import forms
from django.utils import timezone
from .models import CheckoutRequest
from inventory.models import BookCopy


class RequestCheckoutForm(forms.Form):
    pass


class ProcessRequestForm(forms.Form):
    action = forms.ChoiceField(choices=[("approve", "Approve"), ("reject", "Reject")], widget=forms.RadioSelect)
    copy = forms.ModelChoiceField(
        queryset=BookCopy.objects.none(),
        required=False,
        label="Select Copy",
        help_text="Choose an available copy (required if approving)",
    )
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Default: 7 days from today",
    )
    notes = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, available_copies=None, **kwargs):
        super().__init__(*args, **kwargs)
        if available_copies is not None:
            self.fields["copy"].queryset = available_copies
        if not self.is_bound:
            self.fields["due_date"].initial = timezone.localdate() + timedelta(days=7)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("action") == "approve" and not cleaned_data.get("copy"):
            raise forms.ValidationError("Please select a copy when approving.")
        return cleaned_data
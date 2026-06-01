from django import forms
from accounts.models import User
from inventory.models import BookCopy


class CheckoutUserForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(status=User.Status.ACTIVE),
        label="User",
        help_text="Search by LRN or name",
    )


class CheckoutCopyForm(forms.Form):
    copy = forms.ModelChoiceField(
        queryset=BookCopy.objects.filter(is_archived=False, status=BookCopy.Status.AVAILABLE),
        label="Copy",
        help_text="Select an available copy",
    )


class ReturnForm(forms.Form):
    copy = forms.ModelChoiceField(
        queryset=BookCopy.objects.filter(is_archived=False, status=BookCopy.Status.BORROWED),
        label="Copy",
        help_text="Select a borrowed copy to return",
    )
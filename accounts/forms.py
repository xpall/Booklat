from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from .models import User


class LoginForm(forms.Form):
    lrn = forms.CharField(label="LRN", max_length=64, widget=forms.TextInput(attrs={"autofocus": True}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput)


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput,
        required=False,
    )
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput,
        help_text="Minimum 16 characters. Must include uppercase, lowercase, number, and special character.",
    )
    confirm_password = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    def clean_new_password(self):
        password = self.cleaned_data.get("new_password")
        password_validation.validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Passwords do not match.")
        return cleaned_data


class PasswordResetForm(forms.Form):
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput,
        help_text="Minimum 16 characters. Must include uppercase, lowercase, number, and special character.",
    )
    confirm_password = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    def clean_new_password(self):
        password = self.cleaned_data.get("new_password")
        password_validation.validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Passwords do not match.")
        return cleaned_data


class UserForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text="Minimum 16 characters. Must include uppercase, lowercase, number, and special character.",
    )
    role = forms.ModelChoiceField(queryset=None, required=True, empty_label=None, label="Role")

    class Meta:
        model = User
        fields = ["lrn", "first_name", "last_name", "role"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = User._meta.get_field("role").remote_field.model.objects.all().order_by("name")
        if not self.initial.get("role"):
            self.initial["role"] = self.fields["role"].queryset.filter(name="Member").first()

    def clean_password(self):
        password = self.cleaned_data.get("password")
        password_validation.validate_password(password)
        return password


class UserUpdateForm(forms.ModelForm):
    role = forms.ModelChoiceField(queryset=None, required=True, empty_label=None, label="Role")

    class Meta:
        model = User
        fields = ["first_name", "last_name", "role"]

    def __init__(self, *args, request_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Role
        roles = Role.objects.all()
        if request_user and not request_user.is_admin:
            roles = roles.exclude(name__in=["Administrator", "Staff"])
        self.fields["role"].queryset = roles.order_by("name")


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(label="CSV File")
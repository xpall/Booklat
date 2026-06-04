from django import forms


class CreatePostForm(forms.Form):
    pen_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Your pen name (optional)"}),
    )
    is_anonymous = forms.BooleanField(
        required=False,
        label="Post anonymously",
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 5, "maxlength": 500}),
        label="Your message",
        help_text="Max 500 characters",
    )

    def clean(self):
        cleaned_data = super().clean()
        pen_name = cleaned_data.get("pen_name", "").strip()
        is_anonymous = cleaned_data.get("is_anonymous", False)
        if not pen_name and not is_anonymous:
            raise forms.ValidationError(
                "Please provide a pen name or choose to post anonymously."
            )
        return cleaned_data


class ProcessPostForm(forms.Form):
    action = forms.ChoiceField(
        choices=[("approve", "Approve"), ("reject", "Reject")],
        widget=forms.RadioSelect,
        label="Decision",
    )
    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "maxlength": 300}),
        required=False,
        label="Reason for rejection (optional)",
    )

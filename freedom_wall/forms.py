from django import forms


class CreatePostForm(forms.Form):
    pen_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Your pen name (optional)"}),
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 5, "maxlength": 500}),
        label="Your message",
        help_text="Max 500 characters",
    )


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

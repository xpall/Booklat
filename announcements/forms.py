from django import forms


class AnnouncementForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"placeholder": "Announcement title"}),
        label="Title",
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 5}),
        label="Content",
    )

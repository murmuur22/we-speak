from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


class JoinForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = ''
        self.fields['password2'].label = 'Confirm password'

    class Meta(UserCreationForm.Meta):
        fields = ('username',)

    def clean_username(self):
        value = self.cleaned_data['username'].lower()
        if get_user_model().objects.filter(username__iexact=value).exists():
            raise forms.ValidationError('That username is already taken.')
        if len(value) > 28 or not value.isascii() or not all(c.isalnum() or c in '_-' for c in value):
            raise forms.ValidationError('Use 1–28 letters, numbers, underscores or hyphens.')
        return value

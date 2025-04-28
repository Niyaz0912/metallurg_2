from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import User


class StyleFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class LoginForm(StyleFormMixin, forms.Form):
    username = forms.CharField(
        max_length=150,
        label=_('Username'),
        help_text=_('Только латинские буквы, цифры и @/./+/-/_')
    )
    password = forms.CharField(
        max_length=255,
        widget=forms.PasswordInput,
        label=_('Password')
    )


class RegistrationForm(StyleFormMixin, UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label=_('First Name')
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label=_('Last Name')
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label=_('Phone')
    )

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'first_name', 'last_name', 'phone')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'employee'
        if commit:
            user.save()
        return user


class UserUpdateForm(StyleFormMixin, UserChangeForm):
    phone = forms.CharField(
        max_length=20,
        required=False,
        label=_('Phone')
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone')
        labels = {
            'username': _('Username'),
            'first_name': _('First Name'),
            'last_name': _('Last Name'),
            'email': _('Email'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password' in self.fields:
            self.fields.pop('password')
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

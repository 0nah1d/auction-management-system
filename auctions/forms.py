from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Address


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['province', 'city', 'zone', 'address', 'zip_code', 'phone']

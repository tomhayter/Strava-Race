from django import forms
from  django.contrib.auth.forms import UserCreationForm

class LoginForm(forms.Form):
    username = forms.CharField(label="Username", widget=forms.TextInput(attrs={'class':'text-input'}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'class':'text-input'}))

class SignUpForm(forms.Form):
    username = forms.CharField(label="Username", widget=forms.TextInput(attrs={'class':'text-input'}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'class':'text-input'}))
    confirm_password = forms.CharField(label="Confirm Password", widget=forms.PasswordInput(attrs={'class':'text-input'}))

    def clean(self):
        cleaned_data = super(SignUpForm, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError(
                "Password and Confirm Password do not match"
            )
        return cleaned_data

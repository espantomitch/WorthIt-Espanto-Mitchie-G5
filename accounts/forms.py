from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User

class IdentityValidationMixin:
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        existing = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError("This email is already registered.")
        return email

class RegistrationForm(IdentityValidationMixin, UserCreationForm):
    first_name = forms.CharField(max_length=150, label="First name")
    last_name = forms.CharField(max_length=150, label="Last name")
    email = forms.EmailField()

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email", "password1", "password2")

    def clean_username(self):
        username = self.cleaned_data["username"].strip().lower()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

class LoginForm(AuthenticationForm):
    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()

class ProfileForm(IdentityValidationMixin, forms.ModelForm):
    first_name = forms.CharField(max_length=150, label="First name")
    last_name = forms.CharField(max_length=150, label="Last name")
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "contact_number")
        help_texts = {"contact_number": "Optional. Example: +639171234567."}

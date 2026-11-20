from io import BytesIO

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from PIL import Image, ImageOps

from .models import User, normalize_name

class IdentityValidationMixin:
    def clean_first_name(self):
        return normalize_name(self.cleaned_data["first_name"])

    def clean_last_name(self):
        return normalize_name(self.cleaned_data["last_name"])

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


    profile_picture = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
        help_text="Optional. Upload a JPEG, PNG, or WebP image up to 8 MB.",
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "contact_number")
        help_texts = {"contact_number": "Optional. Example: +639171234567."}

    def clean_profile_picture(self):
        upload = self.cleaned_data["profile_picture"]
        if not upload:
            return None
        if upload.size > 8 * 1024 * 1024:
            raise forms.ValidationError("Choose a profile picture no larger than 8 MB.")
        try:
            with Image.open(upload, formats=("JPEG", "PNG", "WEBP")) as image:
                if image.width * image.height > 25_000_000:
                    raise forms.ValidationError("Choose a profile picture of 25 megapixels or less.")
                picture = ImageOps.exif_transpose(image).convert("RGB")
                picture = ImageOps.fit(picture, (512, 512))
                with BytesIO() as output:
                    picture.save(output, format="JPEG", quality=85)
                    return output.getvalue()
        except (Image.DecompressionBombError, OSError, ValueError):
            raise forms.ValidationError("Upload a valid JPEG, PNG, or WebP image.") from None

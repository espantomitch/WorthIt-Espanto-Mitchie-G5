from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.templatetags.static import static
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from .models import ProfilePicture, User


class ProfilePictureTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            "avatar_buyer", "avatar_buyer@example.test", first_name="Demo", last_name="Buyer"
        )
        cls.other = User.objects.create_user("avatar_other", "avatar_other@example.test")

    def upload(self, color):
        stream = BytesIO()
        Image.new("RGB", (100, 80), color).save(stream, format="PNG")
        return SimpleUploadedFile("photo.png", stream.getvalue(), content_type="image/png")

    def save_profile(self, **changes):
        return self.client.post(reverse("accounts:profile_edit"), {
            "first_name": "Demo", "last_name": "Buyer", "email": self.user.email, **changes,
        })

    def test_picture_is_private_to_the_signed_in_account(self):
        picture_url = reverse("accounts:profile_picture")
        self.assertEqual(self.client.get(picture_url).status_code, 302)
        self.client.force_login(self.user)
        self.assertRedirects(
            self.client.get(picture_url), static("images/default-profile.jpg"),
            fetch_redirect_response=False,
        )
        self.assertRedirects(
            self.save_profile(profile_picture=self.upload("red")), reverse("accounts:profile")
        )
        response = self.client.get(picture_url)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        self.assertIn("no-store", response["Cache-Control"])
        with Image.open(BytesIO(response.content)) as image:
            self.assertEqual(image.size, (512, 512))
        self.client.force_login(self.other)
        self.assertRedirects(
            self.client.get(picture_url), static("images/default-profile.jpg"),
            fetch_redirect_response=False,
        )

    def test_replacement_validation_and_edits_without_upload(self):
        self.client.force_login(self.user)
        self.save_profile(profile_picture=self.upload("red"))
        first = bytes(ProfilePicture.objects.get(user=self.user).image)
        invalid = SimpleUploadedFile("fake.png", b"not a picture", content_type="image/png")
        response = self.save_profile(profile_picture=invalid, first_name="Invalid")
        self.assertContains(response, "Upload a valid JPEG, PNG, or WebP image.")
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Demo")
        self.assertEqual(bytes(ProfilePicture.objects.get(user=self.user).image), first)
        self.save_profile(first_name="New")
        self.assertEqual(bytes(ProfilePicture.objects.get(user=self.user).image), first)
        self.save_profile(profile_picture=self.upload("blue"))
        self.assertEqual(ProfilePicture.objects.filter(user=self.user).count(), 1)
        self.assertNotEqual(bytes(ProfilePicture.objects.get(user=self.user).image), first)

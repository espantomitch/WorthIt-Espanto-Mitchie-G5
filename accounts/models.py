from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower

class AccountManager(UserManager):
    def _create_user(self, username, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        return super()._create_user(username.strip().lower(), email.strip().lower(), password, **extra_fields)

class User(AbstractUser):
    email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=20, blank=True, validators=[
        RegexValidator(r"^\+?[0-9][0-9 ()-]{6,19}$", "Enter a valid contact number, such as +639171234567.")
    ])
    objects = AccountManager()

    class Meta:
        db_table = "users"
        constraints = [
            models.UniqueConstraint(Lower("username"), name="users_username_ci_unique"),
            models.UniqueConstraint(Lower("email"), name="users_email_ci_unique"),
            models.CheckConstraint(condition=~models.Q(email=""), name="users_email_nonempty"),
        ]

    @property
    def role(self):
        # One source of truth: Django staff status controls the Admin role.
        return "Admin" if self.is_staff else "User"

    def save(self, *args, **kwargs):
        self.username = self.username.strip().lower()
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

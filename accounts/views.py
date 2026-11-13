from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from .decorators import role_required
from .forms import LoginForm, ProfileForm, RegistrationForm
from .models import User

def home(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    return render(request, "home.html")

def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = RegistrationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                account = form.save(commit=False)
                account.is_staff = False
                account.is_superuser = False
                account.save()
        except IntegrityError:
            form.add_error(None, "That username or email is already in use. Please choose another.")
        else:
            messages.success(request, "Your account has been created. You can now log in.")
            return redirect("accounts:login")
    return render(request, "accounts/register.html", {"form": form})

class AccountLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        # Always dispatch by role; never redirect to untrusted next URLs.
        return reverse("accounts:dashboard")

    def form_valid(self, form):
        messages.success(self.request, "You are now logged in.")
        return super().form_valid(form)

@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("accounts:login")

@login_required
def dashboard(request):
    return redirect("accounts:admin_dashboard" if request.user.is_staff else "accounts:user_dashboard")

@role_required(admin=False)
def user_dashboard(request):
    return render(request, "accounts/user_dashboard.html")

@role_required(admin=True)
def admin_dashboard(request):
    return render(request, "accounts/admin_dashboard.html", {
        "user_count": User.objects.filter(is_staff=False).count(),
        "admin_count": User.objects.filter(is_staff=True).count(),
        "active_count": User.objects.filter(is_active=True).count(),
    })

@login_required
def profile(request):
    # No user ID is accepted: users can only access their own profile.
    return render(request, "accounts/profile.html")

@login_required
def profile_edit(request):
    form = ProfileForm(request.POST if request.method == "POST" else None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error("email", "This email is already registered.")
        else:
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")
    return render(request, "accounts/profile_edit.html", {"form": form})

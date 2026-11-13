from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class AccountAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (("Contact", {"fields": ("contact_number",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Required details", {"fields": ("email", "first_name", "last_name")}),)

admin.site.site_header = "WorthIt Administration"
admin.site.site_title = "WorthIt Admin"
admin.site.index_title = "Account management"
